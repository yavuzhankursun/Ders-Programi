import argparse
import logging
import sys
import os
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style
import sqlite3

from models import User, Faculty, Student, Department, Course, Classroom, Schedule, SharedCourse
from db import init_db, get_session, close_session, create_default_user, create_sample_data, configure_constraints
from scheduler import DersProgramiOlusturucu

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("schedule_app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Terminal renkleri için başlatma
init(autoreset=True)

def print_title(title):
    """Başlık yazdır"""
    print("\n" + Fore.GREEN + Style.BRIGHT + "=" * 60)
    print(Fore.GREEN + Style.BRIGHT + title.center(60))
    print(Fore.GREEN + Style.BRIGHT + "=" * 60 + "\n")

def print_success(message):
    """Başarı mesajı yazdır"""
    print(Fore.GREEN + Style.BRIGHT + "✓ " + message)

def print_error(message):
    """Hata mesajı yazdır"""
    print(Fore.RED + Style.BRIGHT + "✗ " + message)

def print_info(message):
    """Bilgi mesajı yazdır"""
    print(Fore.CYAN + Style.BRIGHT + "ℹ " + message)

def print_table(headers, data):
    """Tablo yazdır"""
    print(tabulate(data, headers=headers, tablefmt="fancy_grid"))

def list_departments():
    """Bölümleri listele"""
    session = get_session()
    try:
        departments = session.query(Department).all()
        
        if not departments:
            print_info("Henüz bölüm bulunmamaktadır.")
            return
        
        data = []
        for dept in departments:
            courses_count = session.query(Course).filter_by(department_id=dept.id).count()
            data.append([dept.id, dept.name, dept.code, courses_count])
        
        print_table(["ID", "Bölüm Adı", "Bölüm Kodu", "Ders Sayısı"], data)
    finally:
        close_session()

def add_department():
    """Yeni bölüm ekle"""
    print_title("Yeni Bölüm Ekle")
    
    name = input("Bölüm Adı: ")
    code = input("Bölüm Kodu: ")
    
    if not name or not code:
        print_error("Bölüm adı ve kodu zorunludur!")
        return
    
    session = get_session()
    try:
        # Kod benzersiz mi kontrol et
        existing = session.query(Department).filter_by(code=code).first()
        if existing:
            print_error(f"'{code}' kodlu bir bölüm zaten mevcut!")
            return
        
        department = Department(name=name, code=code)
        session.add(department)
        session.commit()
        
        print_success(f"'{name}' bölümü başarıyla eklendi!")
    except Exception as e:
        session.rollback()
        print_error(f"Bölüm eklenirken hata oluştu: {str(e)}")
    finally:
        close_session()

def list_classrooms():
    """Derslikleri listele"""
    session = get_session()
    try:
        classrooms = session.query(Classroom).all()
        
        if not classrooms:
            print_info("Henüz derslik bulunmamaktadır.")
            return
        
        data = []
        for cr in classrooms:
            data.append([cr.id, cr.name, cr.capacity, cr.type])
        
        print_table(["ID", "Derslik Adı", "Kapasite", "Tür"], data)
    finally:
        close_session()

def add_classroom():
    """Yeni derslik ekle"""
    print_title("Yeni Derslik Ekle")
    
    name = input("Derslik Adı: ")
    capacity_str = input("Kapasite: ")
    type_choice = input("Tür (1: NORMAL, 2: LAB): ")
    location = input("Konum (opsiyonel): ")
    
    if not name or not capacity_str:
        print_error("Derslik adı ve kapasitesi zorunludur!")
        return
    
    try:
        capacity = int(capacity_str.strip())
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    if type_choice.strip() == "1":
        type = "NORMAL"
    elif type_choice.strip() == "2":
        type = "LAB"
    else:
        print_error("Geçersiz tür seçimi!")
        return
    
    session = get_session()
    try:
        # İsim benzersiz mi kontrol et
        existing = session.query(Classroom).filter_by(name=name).first()
        if existing:
            print_error(f"'{name}' adlı bir derslik zaten mevcut!")
            return
        
        classroom = Classroom(name=name, capacity=capacity, type=type, location=location)
        session.add(classroom)
        session.commit()
        
        print_success(f"'{name}' dersliği başarıyla eklendi!")
    except Exception as e:
        session.rollback()
        print_error(f"Derslik eklenirken hata oluştu: {str(e)}")
    finally:
        close_session()

def list_faculty():
    """Öğretim üyelerini listele"""
    session = get_session()
    try:
        try:
            faculty_members = session.query(Faculty).join(User).all()
            
            if not faculty_members:
                print_info("Henüz öğretim üyesi bulunmamaktadır.")
                return
            
            data = []
            for faculty in faculty_members:
                user = session.query(User).get(faculty.user_id)
                title = faculty.title if faculty.title else ""
                data.append([faculty.id, f"{title} {user.name} {user.surname}", user.email])
            
            print_table(["ID", "Öğretim Üyesi", "E-posta"], data)
        except Exception as e:
            print_error(f"Öğretim üyeleri listelenirken hata: {str(e)}")
    finally:
        close_session()

def add_faculty():
    """Yeni öğretim üyesi ekle"""
    print_title("Yeni Öğretim Üyesi Ekle")
    
    name = input("Ad: ")
    surname = input("Soyad: ")
    email = input("E-posta: ")
    title = input("Unvan (opsiyonel): ")
    
    if not name or not surname or not email:
        print_error("Ad, soyad ve e-posta zorunludur!")
        return
    
    session = get_session()
    try:
        # E-posta benzersiz mi kontrol et
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            print_error(f"'{email}' e-posta adresi zaten kullanımda!")
            return
        
        # Kullanıcı oluştur
        try:
            user = User(name=name, surname=surname, email=email, 
                       password="faculty123", user_type="ogretim_uyesi")
            session.add(user)
            session.commit()
        except Exception as e:
            session.rollback()
            print_error(f"Kullanıcı oluşturulurken hata: {str(e)}")
            return
        
        # Öğretim üyesi profili oluştur
        try:
            faculty = Faculty(user_id=user.id, title=title)
            session.add(faculty)
            session.commit()
            
            print_success(f"'{name} {surname}' öğretim üyesi başarıyla eklendi!")
        except Exception as e:
            session.rollback()
            # Oluşturulan kullanıcıyı sil
            session.delete(user)
            session.commit()
            if "NOT NULL constraint failed" in str(e):
                print_error("Unvan veya diğer zorunlu alanlar boş olamaz!")
            else:
                print_error(f"Öğretim üyesi profili oluşturulurken hata: {str(e)}")
            return
            
    except Exception as e:
        session.rollback()
        if "UNIQUE constraint failed" in str(e):
            print_error("Bu e-posta zaten kullanılıyor!")
        else:
            print_error(f"Öğretim üyesi eklenirken hata oluştu: {str(e)}")
    finally:
        close_session()

def list_courses():
    """Dersleri listele"""
    session = get_session()
    try:
        try:
            # Join işlemi yerine tüm dersleri al, sonra ilişkileri ayrı ayrı kontrol et
            courses = session.query(Course).all()
            
            if not courses:
                print_info("Henüz ders bulunmamaktadır.")
                return
            
            data = []
            for course in courses:
                instructor = "Atanmamış"
                department_code = "Bilinmiyor"
                
                # Department bilgisi kontrol et
                try:
                    if course.department_id:
                        department = session.query(Department).get(course.department_id)
                        if department:
                            department_code = department.code
                except Exception as e:
                    logger.error(f"Bölüm bilgisi alınırken hata: {str(e)}")
                    
                # Instructor bilgisi kontrol et
                try:
                    if course.instructor_id:
                        faculty = session.query(Faculty).get(course.instructor_id)
                        if faculty and faculty.user_id:
                            user = session.query(User).get(faculty.user_id)
                            if user:
                                instructor = f"{faculty.title if faculty.title else ''} {user.name} {user.surname}"
                except Exception as e:
                    logger.error(f"Öğretim üyesi bilgisi alınırken hata: {str(e)}")
                
                data.append([
                    course.id, 
                    course.code, 
                    course.name, 
                    department_code, 
                    course.semester, 
                    course.weekly_hours,
                    instructor
                ])
            
            print_table(["ID", "Kod", "Ders Adı", "Bölüm", "Dönem", "Haftalık Saat", "Öğretim Üyesi"], data)
        except Exception as e:
            print_error(f"Dersler listelenirken hata: {str(e)}")
            logger.exception("Ders listesi oluşturulurken hata")
    finally:
        close_session()

def add_course():
    """Yeni ders ekle"""
    print_title("Yeni Ders Ekle")
    
    # Bölümleri göster
    print_info("Mevcut Bölümler:")
    list_departments()
    
    department_id_str = input("Bölüm ID: ")
    name = input("Ders Adı: ")
    code = input("Ders Kodu: ")
    semester_str = input("Dönem (1-8): ")
    weekly_hours_str = input("Haftalık Saat: ")
    is_mandatory = input("Zorunlu mu? (E/H): ").lower() == 'e'
    is_online = input("Online mı? (E/H): ").lower() == 'e'
    
    # Öğretim üyelerini göster
    print_info("Mevcut Öğretim Üyeleri:")
    list_faculty()
    
    instructor_id_str = input("Öğretim Üyesi ID (opsiyonel): ")
    
    if not name or not code or not department_id_str or not semester_str or not weekly_hours_str:
        print_error("Ders adı, kodu, bölüm ID, dönem ve haftalık saat zorunludur!")
        return
    
    try:
        department_id = int(department_id_str.strip())
        semester = int(semester_str.strip())
        weekly_hours = int(weekly_hours_str.strip())
        instructor_id = int(instructor_id_str.strip()) if instructor_id_str.strip() else None
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    session = get_session()
    try:
        # Bölüm var mı kontrol et
        department = session.query(Department).get(department_id)
        if not department:
            print_error(f"ID: {department_id} olan bir bölüm bulunamadı!")
            return
        
        # Kod benzersiz mi kontrol et
        existing = session.query(Course).filter_by(code=code).first()
        if existing:
            print_error(f"'{code}' kodlu bir ders zaten mevcut!")
            return
        
        # Öğretim üyesi var mı kontrol et
        if instructor_id:
            faculty = session.query(Faculty).get(instructor_id)
            if not faculty:
                print_error(f"ID: {instructor_id} olan bir öğretim üyesi bulunamadı!")
                return
        
        try:
            course = Course(
                name=name,
                code=code,
                department_id=department_id,
                semester=semester,
                weekly_hours=weekly_hours,
                is_mandatory=is_mandatory,
                is_online=is_online,
                instructor_id=instructor_id
            )
            session.add(course)
            session.flush()  # Veritabanı işlemini tamamla ama henüz commit etme
            
            # Oluşturulan dersin ID'sini al
            new_course_id = course.id
            logger.info(f"Yeni ders oluşturuldu: ID={new_course_id}, Kod={code}")
            
            session.commit()
            
            # Ders eklendikten sonra doğrulama kontrolü yap
            verification = session.query(Course).get(new_course_id)
            if verification:
                print_success(f"'{name}' dersi başarıyla eklendi! (ID: {new_course_id})")
            else:
                print_error("Ders eklendi ancak doğrulama yapılamadı. Lütfen dersleri listeleyin.")
                
        except Exception as e:
            session.rollback()
            if "FOREIGN KEY constraint failed" in str(e):
                print_error("Belirtilen öğretim üyesi veya bölüm bulunamadı!")
            elif "NOT NULL constraint failed" in str(e):
                print_error("Zorunlu alanlar boş bırakılamaz!")
            elif "UNIQUE constraint failed" in str(e):
                print_error(f"'{code}' kodlu bir ders zaten var!")
            else:
                print_error(f"Ders eklenirken detaylı hata: {str(e)}")
            return
    except Exception as e:
        session.rollback()
        print_error(f"Ders eklenirken hata oluştu: {str(e)}")
    finally:
        close_session()

def add_shared_course():
    """Ortak ders ekle"""
    print_title("Ortak Ders Tanımla")
    
    # Dersleri göster
    print_info("Mevcut Dersler:")
    list_courses()
    
    course_id_str = input("Paylaşılacak Ders ID: ")
    
    # Bölümleri göster
    print_info("Mevcut Bölümler:")
    list_departments()
    
    shared_dept_id_str = input("Paylaşılacak Bölüm ID: ")
    
    if not course_id_str or not shared_dept_id_str:
        print_error("Ders ID ve Bölüm ID zorunludur!")
        return
    
    try:
        course_id = int(course_id_str.strip())
        shared_dept_id = int(shared_dept_id_str.strip())
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    session = get_session()
    try:
        # Ders var mı kontrol et
        course = session.query(Course).get(course_id)
        if not course:
            print_error(f"ID: {course_id} olan bir ders bulunamadı!")
            return
        
        # Bölüm var mı kontrol et
        department = session.query(Department).get(shared_dept_id)
        if not department:
            print_error(f"ID: {shared_dept_id} olan bir bölüm bulunamadı!")
            return
        
        # Kendi bölümüyle paylaşım yapılamaz
        if course.department_id == shared_dept_id:
            print_error("Bir ders kendi bölümüyle paylaşılamaz!")
            return
        
        # Zaten paylaşılmış mı kontrol et
        existing = session.query(SharedCourse).filter_by(
            course_id=course_id, 
            shared_with_department_id=shared_dept_id
        ).first()
        
        if existing:
            print_error(f"Bu ders zaten bu bölümle paylaşılmış!")
            return
        
        shared_course = SharedCourse(
            course_id=course_id,
            shared_with_department_id=shared_dept_id
        )
        session.add(shared_course)
        session.commit()
        
        print_success(f"'{course.name}' dersi '{department.name}' bölümüyle başarıyla paylaşıldı!")
    except Exception as e:
        session.rollback()
        print_error(f"Ortak ders tanımlanırken hata oluştu: {str(e)}")
    finally:
        close_session()

def set_fixed_time():
    """Derse sabit zaman tanımla"""
    print_title("Derse Sabit Zaman Tanımla")
    
    # Dersleri göster
    print_info("Mevcut Dersler:")
    list_courses()
    
    course_id_str = input("Ders ID: ")
    
    if not course_id_str:
        print_error("Ders ID zorunludur!")
        return
    
    try:
        course_id = int(course_id_str.strip())
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    session = get_session()
    try:
        # Ders var mı kontrol et
        course = session.query(Course).get(course_id)
        if not course:
            print_error(f"ID: {course_id} olan bir ders bulunamadı!")
            return
        
        fixed_time = {}
        days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        
        print_info("Her gün için sabit zamanları belirleyin (birden fazla saat için virgülle ayırın):")
        print_info("Saat formatı: 08:00-09:00, 09:00-10:00, vb.")
        print_info("Hiçbir zaman ayrılmayacaksa boş bırakın.")
        
        for day in days:
            time_slots_input = input(f"{day} için sabit zamanlar: ")
            if time_slots_input.strip():
                time_slots = [ts.strip() for ts in time_slots_input.split(',')]
                fixed_time[day] = time_slots
        
        if not fixed_time:
            print_error("Hiçbir gün için sabit zaman belirtilmedi!")
            return
        
        # Sabit zamanları ayarla
        course.set_fixed_time(fixed_time)
        session.commit()
        
        print_success(f"'{course.name}' dersi için sabit zamanlar başarıyla ayarlandı!")
    except Exception as e:
        session.rollback()
        print_error(f"Sabit zaman ayarlanırken hata oluştu: {str(e)}")
    finally:
        close_session()

def list_schedules():
    """Ders programlarını listele"""
    session = get_session()
    try:
        academic_years = session.query(Schedule.academic_year).distinct().all()
        
        if not academic_years:
            print_info("Henüz oluşturulmuş bir ders programı bulunmamaktadır.")
            return
        
        print_title("Mevcut Ders Programları")
        for year in academic_years:
            semesters = session.query(Schedule.semester).filter_by(academic_year=year[0]).distinct().all()
            for semester in semesters:
                count = session.query(Schedule).filter_by(
                    academic_year=year[0], 
                    semester=semester[0]
                ).count()
                
                print(f"  * {year[0]} {semester[0]} - {count} ders")
    finally:
        close_session()

def generate_schedule():
    """Ders programı oluştur"""
    print_title("Ders Programı Oluştur")
    
    # Bölümleri göster
    print_info("Mevcut Bölümler:")
    list_departments()
    
    departments_input = input("Bölüm ID'leri (virgülle ayırın): ")
    academic_year = input("Akademik Yıl (örn: 2024-2025): ")
    semester = input("Dönem (Güz/Bahar): ")
    
    if not departments_input or not academic_year or not semester:
        print_error("Bölüm ID'leri, akademik yıl ve dönem zorunludur!")
        return
    
    try:
        department_ids = [int(dept_id.strip()) for dept_id in departments_input.split(',')]
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    if semester not in ['Güz', 'Bahar']:
        print_error("Dönem 'Güz' veya 'Bahar' olmalıdır!")
        return
    
    session = get_session()
    try:
        # Bölümlerin var olduğunu kontrol et
        for dept_id in department_ids:
            department = session.query(Department).get(dept_id)
            if not department:
                print_error(f"ID: {dept_id} olan bir bölüm bulunamadı!")
                return
    finally:
        close_session()
    
    print_info("Ders programı oluşturuluyor, lütfen bekleyin...")
    scheduler = DersProgramiOlusturucu(department_ids, academic_year, semester)
    success, message = scheduler.generate_schedule()
    
    if success:
        print_success(message)
    else:
        print_error(message)

def export_schedule():
    """Ders programını Excel'e aktar"""
    print_title("Ders Programını Excel'e Aktar")
    
    # Mevcut programları göster
    list_schedules()
    
    # Bölümleri göster
    print_info("Mevcut Bölümler:")
    list_departments()
    
    departments_input = input("Bölüm ID'leri (virgülle ayırın): ")
    academic_year = input("Akademik Yıl (örn: 2024-2025): ")
    semester = input("Dönem (Güz/Bahar): ")
    
    if not departments_input or not academic_year or not semester:
        print_error("Bölüm ID'leri, akademik yıl ve dönem zorunludur!")
        return
    
    try:
        department_ids = [int(dept_id.strip()) for dept_id in departments_input.split(',')]
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    if semester not in ['Güz', 'Bahar']:
        print_error("Dönem 'Güz' veya 'Bahar' olmalıdır!")
        return
    
    session = get_session()
    try:
        # Bölümlerin var olduğunu kontrol et
        for dept_id in department_ids:
            department = session.query(Department).get(dept_id)
            if not department:
                print_error(f"ID: {dept_id} olan bir bölüm bulunamadı!")
                return
    finally:
        close_session()
    
    print_info("Excel dosyası oluşturuluyor, lütfen bekleyin...")
    scheduler = DersProgramiOlusturucu(department_ids, academic_year, semester)
    excel_path = scheduler.export_to_excel()
    
    if excel_path:
        print_success(f"Excel dosyası oluşturuldu: {excel_path}")
    else:
        print_error("Excel dosyası oluşturulurken bir hata oluştu!")

def init_database():
    """Veritabanını başlat ve örnek verileri oluştur"""
    print_title("Veritabanı Başlatılıyor")
    
    try:
        # Veritabanı tabloları oluştur
        init_db()
        print_success("Veritabanı tabloları başarıyla oluşturuldu.")
        
        # Varsayılan kullanıcı oluştur
        create_default_user()
        print_success("Varsayılan yönetici kullanıcısı oluşturuldu.")
        
        # Örnek verileri oluştur
        create_sample_data()
        print_success("Örnek veriler başarıyla oluşturuldu.")
        
        # BLM ve YZM için kısıtları yapılandır
        configure_constraints()
        print_success("BLM ve YZM bölümleri için kısıtlar başarıyla yapılandırıldı.")
        
        print_info("\nSistem kullanıma hazır!")
    except Exception as e:
        print_error(f"Veritabanı başlatılırken hata oluştu: {str(e)}")

def clean_database():
    """Veritabanını sil"""
    try:
        # schedule.db dosyasını sil
        if os.path.exists("schedule.db"):
            os.remove("schedule.db")
            print_success("Veritabanı başarıyla silindi.")
        else:
            print_info("Veritabanı dosyası zaten bulunmuyor.")
    except Exception as e:
        print_error(f"Veritabanı silinirken hata oluştu: {str(e)}")

def show_menu():
    """Ana menüyü göster ve seçimi döndür"""
    print_title("HAFTALIK DERS PROGRAMI OLUŞTURMA SİSTEMİ")
    
    options = [
        "Bölümleri Listele",
        "Yeni Bölüm Ekle",
        "Derslikleri Listele",
        "Yeni Derslik Ekle",
        "Öğretim Üyelerini Listele",
        "Yeni Öğretim Üyesi Ekle",
        "Dersleri Listele",
        "Yeni Ders Ekle",
        "Ortak Ders Tanımla",
        "Derse Sabit Zaman Tanımla",
        "Ders Programlarını Listele",
        "Ders Programı Oluştur",
        "Ders Programını Excel'e Aktar",
        "Öğretim Üyesi Müsaitlik Durumu Düzenle",
        "Ders Programı Sil",
        "Veritabanını Başlat (Tüm veriler silinir ve yenilenir)",
        "Veritabanını Temizle (Sadece tüm veriler silinir)"
    ]
    
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    print("0. Çıkış\n")
    
    while True:
        try:
            choice_input = input("Seçiminiz (0-{}): ".format(len(options)))
            choice = int(choice_input.strip())
            if 0 <= choice <= len(options):
                return choice
            print_error(f"Lütfen 0-{len(options)} arasında bir değer girin!")
        except ValueError:
            print_error("Sayısal değerler geçerli bir sayı olmalıdır!")

def main():
    """Ana program döngüsü"""
    while True:
        choice = show_menu()
        
        if choice == 0:
            print_success("Program sonlandırılıyor...")
            break
        elif choice == 1:
            list_departments()
        elif choice == 2:
            add_department()
        elif choice == 3:
            list_classrooms()
        elif choice == 4:
            add_classroom()
        elif choice == 5:
            list_faculty()
        elif choice == 6:
            add_faculty()
        elif choice == 7:
            list_courses()
        elif choice == 8:
            add_course()
        elif choice == 9:
            add_shared_course()
        elif choice == 10:
            set_fixed_time()
        elif choice == 11:
            list_schedules()
        elif choice == 12:
            generate_schedule()
        elif choice == 13:
            export_schedule()
        elif choice == 14:
            edit_faculty_availability()
        elif choice == 15:
            delete_schedule()
        elif choice == 16:
            init_database()
        elif choice == 17:
            clean_database()
        else:
            print_error("Geçersiz seçim! Lütfen 0-17 arasında bir değer girin.")
        
        input("\nDevam etmek için ENTER tuşuna basın...")
        
        if choice == 0:
            break

def edit_faculty_availability():
    """Öğretim üyesinin müsaitlik durumunu düzenle"""
    print_title("Öğretim Üyesi Müsaitlik Durumu Düzenle")
    
    # Öğretim üyelerini listele
    print_info("Mevcut Öğretim Üyeleri:")
    list_faculty()
    
    # Seçim yap
    faculty_id_str = input("Öğretim Üyesi ID (opsiyonel): ")
    if not faculty_id_str:
        print_error("İşlem iptal edildi!")
        return
    
    try:
        faculty_id = int(faculty_id_str.strip())
    except ValueError:
        print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
        return
    
    # Öğretim üyesini bul
    session = get_session()
    try:
        faculty = session.query(Faculty).get(faculty_id)
        if not faculty:
            print_error(f"ID: {faculty_id} olan bir öğretim üyesi bulunamadı!")
            return
        
        # Mevcut müsaitlik durumunu al
        availability = faculty.get_availability() or {}
        
        print_info("Müsaitlik Durumu Düzenleme")
        print_info("Günleri ve saatleri belirleyin. Öğretim üyesi sadece belirttiğiniz saatlerde müsait olacaktır.")
        print_info("Her gün için müsait olduğu saat dilimlerini virgülle ayırarak giriniz.")
        print_info("Müsait saat dilimleri: 09:00-10:00, 10:00-11:00, 11:00-12:00, 13:00-14:00, 14:00-15:00, 15:00-16:00, 16:00-17:00")
        print_info("Örnek: 09:00-10:00,10:00-11:00,13:00-14:00")
        print_info("Hiç müsait değilse boş bırakın.")
        
        # Gün isimleri
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        
        # Tüm saatler
        all_slots = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00"]
        
        # Her gün için müsaitlik bilgisi al
        new_availability = {}
        for day in days:
            current = availability.get(day, [])
            print_info(f"\n{day} günü için müsait saatler: {', '.join(current) if current else 'Yok'}")
            slots_input = input(f"{day} için müsait saatler: ")
            
            if not slots_input:
                new_availability[day] = []
            else:
                slots = [s.strip() for s in slots_input.split(",")]
                # Geçerli saat dilimlerini kontrol et
                valid_slots = [s for s in slots if s in all_slots]
                if len(valid_slots) != len(slots):
                    print_warning("Bazı saat dilimleri geçersizdi ve yok sayıldı.")
                new_availability[day] = valid_slots
        
        # Müsaitlik durumunu kaydet
        faculty.set_availability(new_availability)
        session.commit()
        
        print_success("Müsaitlik durumu başarıyla güncellendi!")
        
    except Exception as e:
        session.rollback()
        print_error(f"Müsaitlik durumu güncellenirken hata: {str(e)}")
        logger.exception("Müsaitlik durumu güncellenirken hata")
    finally:
        close_session()

def print_warning(message):
    """Uyarı mesajı yazdır"""
    print(f"\033[93m⚠ {message}\033[0m")

def delete_schedule():
    """Ders programını sil"""
    print_title("Ders Programı Sil")
    
    # Mevcut programları göster
    session = get_session()
    try:
        schedules = session.query(Schedule).order_by(Schedule.created_at.desc()).all()
        
        if not schedules:
            print_info("Silinecek ders programı bulunmamaktadır.")
            return
        
        print_info("Mevcut Ders Programları:")
        data = []
        for schedule in schedules:
            course = session.query(Course).get(schedule.course_id)
            department = session.query(Department).get(course.department_id) if course else None
            data.append([
                schedule.id,
                schedule.academic_year,
                schedule.semester,
                department.name if department else "Bilinmiyor",
                schedule.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        print_table(["ID", "Akademik Yıl", "Dönem", "Bölüm", "Oluşturulma Tarihi"], data)
        
        print_info("\nBir ID girin veya tüm programları silmek için 0 (sıfır) girin.")
        schedule_id_str = input("\nSilinecek Program ID: ")
        if not schedule_id_str:
            print_error("İşlem iptal edildi!")
            return
        
        try:
            schedule_id = int(schedule_id_str.strip())
        except ValueError:
            print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
            return
        
        # Tüm programları silme seçeneği
        if schedule_id == 0:
            # Akademik yıl ve dönem bazında grupla
            grouped_schedules = {}
            for schedule in schedules:
                key = f"{schedule.academic_year} {schedule.semester}"
                if key not in grouped_schedules:
                    grouped_schedules[key] = []
                grouped_schedules[key].append(schedule)
            
            print_info("Silmek istediğiniz program grubunu seçin:")
            options = list(grouped_schedules.keys())
            options.append("Tüm Programlar")
            
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            group_choice = input("\nSeçiminiz (1-{}): ".format(len(options)))
            if not group_choice:
                print_error("İşlem iptal edildi!")
                return
            
            try:
                group_index = int(group_choice.strip()) - 1
                if group_index < 0 or group_index >= len(options):
                    print_error("Geçersiz seçim!")
                    return
            except ValueError:
                print_error("Sayısal değerler geçerli bir sayı olmalıdır!")
                return
            
            # Tüm programlar seçeneği
            if group_index == len(options) - 1:
                confirm = input(f"TÜM DERS PROGRAMLARINI silmek istediğinizden emin misiniz? Bu işlem geri alınamaz! (E/H): ")
                if confirm.lower() != 'e':
                    print_info("İşlem iptal edildi.")
                    return
                
                try:
                    # Tüm programları sil
                    count = session.query(Schedule).delete()
                    session.commit()
                    print_success(f"Tüm ders programları başarıyla silindi! ({count} program)")
                except Exception as e:
                    session.rollback()
                    print_error(f"Programlar silinirken hata oluştu: {str(e)}")
                    logger.exception("Programlar silinirken hata")
                
                return
            
            # Belirli bir akademik yıl/dönem için tüm programları sil
            selected_key = options[group_index]
            selected_schedules = grouped_schedules[selected_key]
            
            confirm = input(f"{selected_key} dönemi için TÜM DERS PROGRAMLARINI ({len(selected_schedules)} program) silmek istediğinizden emin misiniz? (E/H): ")
            if confirm.lower() != 'e':
                print_info("İşlem iptal edildi.")
                return
            
            try:
                # Seçilen dönem için programları sil
                academic_year, semester = selected_key.split(" ", 1)
                count = session.query(Schedule).filter_by(
                    academic_year=academic_year,
                    semester=semester
                ).delete()
                session.commit()
                print_success(f"{selected_key} dönemi için tüm ders programları başarıyla silindi! ({count} program)")
            except Exception as e:
                session.rollback()
                print_error(f"Programlar silinirken hata oluştu: {str(e)}")
                logger.exception("Programlar silinirken hata")
            
            return
        
        # Tek program silme işlemi
        schedule = session.query(Schedule).get(schedule_id)
        if not schedule:
            print_error(f"ID: {schedule_id} olan bir program bulunamadı!")
            return
        
        # Bölüm bilgisini al
        course = session.query(Course).get(schedule.course_id)
        department = session.query(Department).get(course.department_id) if course else None
        
        # Onay al
        confirm = input(f"{schedule.academic_year} {schedule.semester} dönemi {department.name if department else 'Bilinmeyen Bölüm'} programını silmek istediğinizden emin misiniz? (E/H): ")
        if confirm.lower() != 'e':
            print_info("İşlem iptal edildi.")
            return
        
        # Programı sil
        session.delete(schedule)
        session.commit()
        
        print_success("Ders programı başarıyla silindi!")
        
    except Exception as e:
        session.rollback()
        print_error(f"Program silinirken hata oluştu: {str(e)}")
        logger.exception("Program silinirken hata")
    finally:
        close_session()

if __name__ == "__main__":
    main() 