from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, User, Faculty, Department, Course, Classroom, Schedule, SharedCourse, Student
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Veritabanı motoru
engine = create_engine('sqlite:///schedule.db', echo=False)

# Session oluşturucusu
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

def init_db():
    """Veritabanını başlat"""
    session = get_session()
    try:
        # Veritabanı tablolarını oluştur
        Base.metadata.create_all(engine)
        logger.info("Veritabanı tabloları başarıyla oluşturuldu")
        
        # Mevcut verileri temizle
        session.query(SharedCourse).delete()
        session.query(Schedule).delete()
        session.query(Course).delete()
        session.query(Faculty).delete()
        session.query(Classroom).delete()
        session.query(Department).delete()
        session.query(User).filter(User.user_type != 'yonetici').delete()
        session.commit()
        
        # Varsayılan kullanıcıyı oluştur
        create_default_user()
        
        # Örnek verileri ekle (bölümler ve derslikler)
        create_sample_data()
        
        # Fakülte üyelerini ekle
        add_faculty_members()
        
        # Dersleri ekle
        add_courses()
        
        # Kısıtlamaları yapılandır
        configure_constraints()
        
        # Ders programını ekle
        add_schedule()
        
        logger.info("Veritabanı başarıyla başlatıldı")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Veritabanı başlatma hatası: {str(e)}")
        return False
    finally:
        close_session()

def get_session():
    """Veritabanı oturumu döndür"""
    return Session()

def close_session():
    """Oturumu kapat"""
    Session.remove()

def create_default_user():
    """Varsayılan yönetici kullanıcısı oluştur"""
    session = get_session()
    try:
        # Eğer kullanıcı yoksa varsayılan yönetici oluştur
        if session.query(User).count() == 0:
            admin = User(name='Admin', surname='User', email='admin@example.com', 
                        password='admin123', user_type='yonetici')
            session.add(admin)
            session.commit()
            logger.info("Varsayılan yönetici kullanıcısı oluşturuldu")
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Varsayılan kullanıcı oluşturma hatası: {str(e)}")
        return False
    finally:
        close_session()

def create_sample_data():
    """Örnek verileri oluştur (bölümler ve derslikler)"""
    session = get_session()
    try:
        logger.info("Örnek veriler oluşturuluyor...")
        
        # Örnek bölümler
        blm = Department(name='Bilgisayar Mühendisliği', code='BLM')
        yzm = Department(name='Yazılım Mühendisliği', code='YZM')
        session.add(blm)
        session.add(yzm)
        
        # Örnek derslikler
        classrooms_data = [
            {'name': 'M101', 'capacity': 66, 'type': 'NORMAL'},
            {'name': 'M201', 'capacity': 141, 'type': 'NORMAL'},
            {'name': 'M301', 'capacity': 141, 'type': 'NORMAL'},
            {'name': 'S101', 'capacity': 138, 'type': 'NORMAL'},
            {'name': 'S201', 'capacity': 60, 'type': 'NORMAL'},
            {'name': 'S202', 'capacity': 60, 'type': 'NORMAL'},
            {'name': 'D101', 'capacity': 87, 'type': 'NORMAL'},
            {'name': 'D102', 'capacity': 87, 'type': 'NORMAL'},
            {'name': 'D103', 'capacity': 88, 'type': 'NORMAL'},
            {'name': 'D104', 'capacity': 56, 'type': 'NORMAL'},
            {'name': 'D201', 'capacity': 87, 'type': 'NORMAL'},
            {'name': 'D202', 'capacity': 56, 'type': 'NORMAL'},
            {'name': 'D301', 'capacity': 88, 'type': 'NORMAL'},
            {'name': 'D302', 'capacity': 56, 'type': 'NORMAL'},
            {'name': 'D401', 'capacity': 88, 'type': 'NORMAL'},
            {'name': 'D402', 'capacity': 56, 'type': 'NORMAL'},
            {'name': 'D403', 'capacity': 56, 'type': 'NORMAL'},
            {'name': 'AMFİ A', 'capacity': 143, 'type': 'NORMAL'},
            {'name': 'AMFİ B', 'capacity': 143, 'type': 'NORMAL'},
            {'name': 'BİL.LAB 1', 'capacity': 40, 'type': 'LAB'},
            {'name': 'BİL.LAB 2', 'capacity': 30, 'type': 'LAB'},
            {'name': 'KÜÇÜK LAB', 'capacity': 20, 'type': 'LAB'},
            {'name': 'E102', 'capacity': 60, 'type': 'NORMAL'}
        ]
        
        for data in classrooms_data:
            classroom = Classroom(**data)
            session.add(classroom)
        
        session.commit()
        logger.info("Örnek veriler başarıyla oluşturuldu!")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Örnek veri oluşturma hatası: {str(e)}")
        return False
    finally:
        close_session()

def configure_constraints():
    """BLM ve YZM bölümleri için özel kısıtlar ekle"""
    session = get_session()
    try:
        logger.info("BLM ve YZM bölümleri için özel kısıtlar yapılandırılıyor...")
        
        # Bölümleri bul
        blm = session.query(Department).filter_by(code='BLM').first()
        yzm = session.query(Department).filter_by(code='YZM').first()
        
        if not blm or not yzm:
            logger.warning("BLM veya YZM bölümü bulunamadı, kısıtlar eklenemiyor.")
            return False
        
        # İngilizce dersi
        english_course_blm = session.query(Course).filter(Course.name.like('%İngilizce%'), Course.department_id == blm.id).first()
        english_course_yzm = session.query(Course).filter(Course.name.like('%İngilizce%'), Course.department_id == yzm.id).first()
        
        if english_course_blm and english_course_yzm:
            # Bu derslerin aynı zamanda verilmesini sağla (Pazartesi 09:00-11:00)
            fixed_time = {
                "Pazartesi": ["09:00-10:00", "10:00-11:00"]
            }
            english_course_blm.set_fixed_time(fixed_time)
            english_course_yzm.set_fixed_time(fixed_time)
            
            # Ortak ders olarak işaretle
            if not session.query(SharedCourse).filter_by(course_id=english_course_blm.id, shared_with_department_id=yzm.id).first():
                shared = SharedCourse(course_id=english_course_blm.id, shared_with_department_id=yzm.id)
                session.add(shared)
        
        # Türk Dili dersi
        turkish_course_blm = session.query(Course).filter(Course.name.like('%Türk Dili%'), Course.department_id == blm.id).first()
        turkish_course_yzm = session.query(Course).filter(Course.name.like('%Türk Dili%'), Course.department_id == yzm.id).first()
        
        if turkish_course_blm and turkish_course_yzm:
            # Bu derslerin aynı zamanda verilmesini sağla (Çarşamba 13:00-15:00)
            fixed_time = {
                "Çarşamba": ["13:00-14:00", "14:00-15:00"]
            }
            turkish_course_blm.set_fixed_time(fixed_time)
            turkish_course_yzm.set_fixed_time(fixed_time)
            
            # Ortak ders olarak işaretle
            if not session.query(SharedCourse).filter_by(course_id=turkish_course_blm.id, shared_with_department_id=yzm.id).first():
                shared = SharedCourse(course_id=turkish_course_blm.id, shared_with_department_id=yzm.id)
                session.add(shared)
        
        # BLM ve YZM ortak verilen mesleki dersler için kısıtlar (örneğin Programlama)
        programming_course_blm = session.query(Course).filter(Course.name == 'Programlama I', Course.department_id == blm.id).first()
        programming_course_yzm = session.query(Course).filter(Course.name == 'Programlama I', Course.department_id == yzm.id).first()
        
        if programming_course_blm and programming_course_yzm:
            # Bu dersleri ortak dersler olarak işaretle
            if not session.query(SharedCourse).filter_by(course_id=programming_course_blm.id, shared_with_department_id=yzm.id).first():
                shared = SharedCourse(course_id=programming_course_blm.id, shared_with_department_id=yzm.id)
                session.add(shared)
        
        session.commit()
        logger.info("BLM ve YZM bölümleri için özel kısıtlar başarıyla yapılandırıldı.")
        return True
        
    except Exception as e:
        session.rollback()
        logger.error(f"Kısıt yapılandırma hatası: {str(e)}")
        return False
    finally:
        close_session()

def add_faculty_members():
    """Öğretim üyelerini ekle"""
    session = get_session()
    try:
        # Öğretim üyeleri listesi
        faculty_members = [
            {'name': 'Ulaş', 'surname': 'VURAL', 'email': 'ulas.vural@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Nur Banu', 'surname': 'ALBAYRAK', 'email': 'nur.banu@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Vildan', 'surname': 'YAZICI', 'email': 'vildan.yazici@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Ercan', 'surname': 'ÖLÇER', 'email': 'ercan.olcer@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Mehmet', 'surname': 'KARA', 'email': 'mehmet.kara@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Nevcihan', 'surname': 'DURU', 'email': 'nevcihan.duru@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Elif Pınar', 'surname': 'HACIBEYOĞLU', 'email': 'elif.hacibeyoglu@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'H. Tarık', 'surname': 'DURU', 'email': 'tarik.duru@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Saliha', 'surname': 'ELMAS', 'email': 'saliha.elmas@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'İsmet', 'surname': 'KARADUMAN', 'email': 'ismet.karaduman@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Ahmet', 'surname': 'ŞEN', 'email': 'ahmet.sen@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Fulya', 'surname': 'AKDENİZ', 'email': 'fulya.akdeniz@example.com', 'title': 'Dr. Öğr. Üyesi'},
            {'name': 'Duygu', 'surname': 'SUNMAZ ARSLAN', 'email': 'duygu.sunmaz@example.com', 'title': 'Dr. Öğr. Üyesi'}
        ]
        
        # Öğretim üyelerini ekle
        for member in faculty_members:
            # Kullanıcı oluştur
            user = User(
                name=member['name'],
                surname=member['surname'],
                email=member['email'],
                password='faculty123',
                user_type='ogretim_uyesi'
            )
            session.add(user)
            session.commit()
            
            # Öğretim üyesi profili oluştur
            faculty = Faculty(
                user_id=user.id,
                title=member['title']
            )
            session.add(faculty)
        
        session.commit()
        logger.info("Öğretim üyeleri başarıyla eklendi")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Öğretim üyesi ekleme hatası: {str(e)}")
        return False
    finally:
        close_session()

def add_courses():
    """Dersleri ekle"""
    session = get_session()
    try:
        print("add_courses fonksiyonu başlatıldı")
        # Bölümleri bul
        blm = session.query(Department).filter_by(code='BLM').first()
        yzm = session.query(Department).filter_by(code='YZM').first()
        
        print(f"Bölümler: BLM={blm}, YZM={yzm}")
        
        if not blm or not yzm:
            logger.error("BLM veya YZM bölümü bulunamadı")
            return False
        
        # Öğretim üyelerini bul
        faculty_members = {}
        for faculty in session.query(Faculty).all():
            faculty_members[f"{faculty.user.name} {faculty.user.surname}"] = faculty.id
        
        print(f"Öğretim üyeleri: {faculty_members}")
        
        # Dersler listesi
        courses = [
            # BLM Dersleri - 1. Sınıf (semester 1-2)
            {'name': 'BİLGİSAYAR LAB I', 'code': 'BLM101', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'VERİTABANI YÖNETİM SİSTEMLERİ', 'code': 'BLM102', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'MATEMATİK I', 'code': 'BLM103', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'MİKROİŞLEMCİLER', 'code': 'BLM104', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'SİBER GÜVENLİĞE GİRİŞ', 'code': 'BLM105', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'TEMEL BİLGİ TEKNOLOJİLERİ', 'code': 'BLM106', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'BİLGİSAYAR AĞLARI', 'code': 'BLM107', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'BİLGİSAYAR MÜHENDİSLİĞİNE GİRİŞ', 'code': 'BLM108', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Nevcihan DURU']},
            {'name': 'BİLGİSAYAR MİMARİSİ VE ORGANİZASYONU', 'code': 'BLM109', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'LİNEER CEBİR', 'code': 'BLM110', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['H. Tarık DURU']},
            {'name': 'YAZILIM LAB I', 'code': 'BLM111', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['H. Tarık DURU']},
            {'name': 'YAPAY ZEKA UYGULAMALARI', 'code': 'BLM112', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL'], 'is_online': True},
            {'name': 'FİZİK I', 'code': 'BLM113', 'weekly_hours': 4, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Saliha ELMAS']},
            {'name': 'TEMEL ELEKTRONİK VE UYGULAMALARI', 'code': 'BLM114', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'SAYISAL YÖNTEMLER', 'code': 'BLM115', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'İŞ SAĞLIĞI VE GÜVENLİĞİ I', 'code': 'BLM116', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'DİFERANSİYEL DENKLEMLER', 'code': 'BLM117', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'YAPAY ZEKA', 'code': 'BLM118', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'PROGRAMLAMA DİLLERİ', 'code': 'BLM119', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'GİRİŞİMCİLİK VE İNOVASYON', 'code': 'BLM120', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'KULLANICI DENEYİMİ TASARIMI', 'code': 'BLM121', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'BİÇİMSEL DİLLER VE OTOMATLAR', 'code': 'BLM122', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'AYRIK MATEMATİK', 'code': 'BLM123', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI'], 'is_online': True},
            {'name': 'PROJE VE PORTFÖY YÖNETİMİ VE ÇEVİK YAKLAŞIM', 'code': 'BLM124', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA'], 'is_online': True},
            {'name': 'İNGİLİZCE', 'code': 'BLM125', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Duygu SUNMAZ ARSLAN'], 'is_online': True},
            {'name': 'NESNEYE YÖNELİK PROGRAMLAMA', 'code': 'BLM126', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'KRİPTOLOJİYE GİRİŞ', 'code': 'BLM127', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'BİLGİSAYAR PROGRAMLAMA I', 'code': 'BLM128', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'YAZILIM MÜHENDİSLİĞİ', 'code': 'BLM129', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'PROGRAMLAMA LAB I', 'code': 'BLM130', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Nevcihan DURU']},
            {'name': 'WEB PROGRAMLAMA', 'code': 'BLM131', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'YAZILIM TEST VE KALİTE', 'code': 'BLM132', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'YAPAY ZEKA MODELLERİ', 'code': 'BLM133', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL'], 'is_online': True},
            {'name': 'YAZILIM GEREKSİNİMİ ANALİZİ', 'code': 'BLM134', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'AKILLI SİSTEMLER', 'code': 'BLM135', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            
            # BLM Dersleri - 2. Sınıf (semester 3-4)
            {'name': 'ALGORİTMALAR', 'code': 'BLM201', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 3, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'VERİ YAPILARI', 'code': 'BLM202', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 3, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'İŞLETİM SİSTEMLERİ', 'code': 'BLM203', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 3, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'MATEMATİK II', 'code': 'BLM204', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 3, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'YAPAY ZEKA VE UZMAN SİSTEMLER', 'code': 'BLM205', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 4, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            
            # BLM Dersleri - 3. Sınıf (semester 5-6)
            {'name': 'YAZILIM MİMARİSİ', 'code': 'BLM301', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 5, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'BİLGİSAYAR AĞLARI II', 'code': 'BLM302', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 5, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'MOBİL UYGULAMA GELİŞTİRME', 'code': 'BLM303', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 5, 'instructor_id': faculty_members['Nevcihan DURU']},
            {'name': 'BULUT BİLİŞİM', 'code': 'BLM304', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 6, 'instructor_id': faculty_members['H. Tarık DURU']},
            {'name': 'BİTİRME PROJESİ I', 'code': 'BLM305', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 5, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            
            # BLM Dersleri - 4. Sınıf (semester 7-8)
            {'name': 'BİTİRME PROJESİ II', 'code': 'BLM401', 'weekly_hours': 4, 'department_id': blm.id, 'semester': 7, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'MAKİNE ÖĞRENMESİ', 'code': 'BLM402', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 7, 'instructor_id': faculty_members['Duygu SUNMAZ ARSLAN']},
            {'name': 'BÜYÜK VERİ ANALİTİĞİ', 'code': 'BLM403', 'weekly_hours': 3, 'department_id': blm.id, 'semester': 7, 'instructor_id': faculty_members['Saliha ELMAS']},
            {'name': 'BLOCKCHAIN TEKNOLOJİLERİ', 'code': 'BLM404', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 8, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'GİRİŞİMCİLİK VE PROJE YÖNETİMİ', 'code': 'BLM405', 'weekly_hours': 2, 'department_id': blm.id, 'semester': 8, 'instructor_id': faculty_members['Ahmet ŞEN']},
            
            # YZM Dersleri - 1. Sınıf (semester 1-2)
            {'name': 'BİLGİSAYAR LAB I', 'code': 'YZM101', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'VERİTABANI YÖNETİM SİSTEMLERİ', 'code': 'YZM102', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'MATEMATİK I', 'code': 'YZM103', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'MİKROİŞLEMCİLER', 'code': 'YZM104', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'SİBER GÜVENLİĞE GİRİŞ', 'code': 'YZM105', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'TEMEL BİLGİ TEKNOLOJİLERİ', 'code': 'YZM106', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'BİLGİSAYAR AĞLARI', 'code': 'YZM107', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA']},
            {'name': 'BİLGİSAYAR MÜHENDİSLİĞİNE GİRİŞ', 'code': 'YZM108', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Nevcihan DURU']},
            {'name': 'BİLGİSAYAR MİMARİSİ VE ORGANİZASYONU', 'code': 'YZM109', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'LİNEER CEBİR', 'code': 'YZM110', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['H. Tarık DURU']},
            {'name': 'YAZILIM LAB I', 'code': 'YZM111', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'YAPAY ZEKA UYGULAMALARI', 'code': 'YZM112', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL'], 'is_online': True},
            {'name': 'FİZİK I', 'code': 'YZM113', 'weekly_hours': 4, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Saliha ELMAS']},
            {'name': 'TEMEL ELEKTRONİK VE UYGULAMALARI', 'code': 'YZM114', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'SAYISAL YÖNTEMLER', 'code': 'YZM115', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'İŞ SAĞLIĞI VE GÜVENLİĞİ I', 'code': 'YZM116', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'DİFERANSİYEL DENKLEMLER', 'code': 'YZM117', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'YAPAY ZEKA', 'code': 'YZM118', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'PROGRAMLAMA DİLLERİ', 'code': 'YZM119', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'GİRİŞİMCİLİK VE İNOVASYON', 'code': 'YZM120', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'KULLANICI DENEYİMİ TASARIMI', 'code': 'YZM121', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'BİÇİMSEL DİLLER VE OTOMATLAR', 'code': 'YZM122', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'AYRIK MATEMATİK', 'code': 'YZM123', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Vildan YAZICI'], 'is_online': True},
            {'name': 'PROJE VE PORTFÖY YÖNETİMİ VE ÇEVİK YAKLAŞIM', 'code': 'YZM124', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Mehmet KARA'], 'is_online': True},
            {'name': 'İNGİLİZCE', 'code': 'YZM125', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Duygu SUNMAZ ARSLAN'], 'is_online': True},
            {'name': 'NESNEYE YÖNELİK PROGRAMLAMA', 'code': 'YZM126', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'KRİPTOLOJİYE GİRİŞ', 'code': 'YZM127', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'BİLGİSAYAR PROGRAMLAMA I', 'code': 'YZM128', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'YAZILIM MÜHENDİSLİĞİ', 'code': 'YZM129', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'PROGRAMLAMA LAB I', 'code': 'YZM130', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'WEB PROGRAMLAMA', 'code': 'YZM131', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'YAZILIM TEST VE KALİTE', 'code': 'YZM132', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'YAPAY ZEKA MODELLERİ', 'code': 'YZM133', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ulaş VURAL'], 'is_online': True},
            {'name': 'YAZILIM GEREKSİNİMİ ANALİZİ', 'code': 'YZM134', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'AKILLI SİSTEMLER', 'code': 'YZM135', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 1, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            
            # YZM Dersleri - 2. Sınıf (semester 3-4)
            {'name': 'ALGORİTMALAR', 'code': 'YZM201', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 3, 'instructor_id': faculty_members['Ulaş VURAL']},
            {'name': 'VERİ YAPILARI', 'code': 'YZM202', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 3, 'instructor_id': faculty_members['Nur Banu ALBAYRAK']},
            {'name': 'İŞLETİM SİSTEMLERİ', 'code': 'YZM203', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 3, 'instructor_id': faculty_members['Ercan ÖLÇER']},
            {'name': 'MATEMATİK II', 'code': 'YZM204', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 3, 'instructor_id': faculty_members['Vildan YAZICI']},
            {'name': 'YAZILIM TASARIMI', 'code': 'YZM205', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 4, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            
            # YZM Dersleri - 3. Sınıf (semester 5-6)
            {'name': 'YAZILIM MİMARİSİ', 'code': 'YZM301', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 5, 'instructor_id': faculty_members['Elif Pınar HACIBEYOĞLU']},
            {'name': 'MOBİL PROGRAMLAMA', 'code': 'YZM302', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 5, 'instructor_id': faculty_members['Nevcihan DURU']},
            {'name': 'WEB SERVİSLERİ', 'code': 'YZM303', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 5, 'instructor_id': faculty_members['Fulya AKDENİZ']},
            {'name': 'YAZILIM KALİTE GÜVENCESİ', 'code': 'YZM304', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 6, 'instructor_id': faculty_members['H. Tarık DURU']},
            {'name': 'BİTİRME PROJESİ I', 'code': 'YZM305', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 5, 'instructor_id': faculty_members['Mehmet KARA']},
            
            # YZM Dersleri - 4. Sınıf (semester 7-8)
            {'name': 'BİTİRME PROJESİ II', 'code': 'YZM401', 'weekly_hours': 4, 'department_id': yzm.id, 'semester': 7, 'instructor_id': faculty_members['Saliha ELMAS']},
            {'name': 'YAPAY ZEKA YÖNTEMLERİ', 'code': 'YZM402', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 7, 'instructor_id': faculty_members['Duygu SUNMAZ ARSLAN']},
            {'name': 'VERİ BİLİMİ', 'code': 'YZM403', 'weekly_hours': 3, 'department_id': yzm.id, 'semester': 7, 'instructor_id': faculty_members['İsmet KARADUMAN']},
            {'name': 'DAĞITIK SİSTEMLER', 'code': 'YZM404', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 8, 'instructor_id': faculty_members['Ahmet ŞEN']},
            {'name': 'YAZILIM PROJE YÖNETİMİ', 'code': 'YZM405', 'weekly_hours': 2, 'department_id': yzm.id, 'semester': 8, 'instructor_id': faculty_members['Vildan YAZICI']}
        ]
        
        # Dersleri ekle
        for course_data in courses:
            course = Course(**course_data)
            session.add(course)
            print(f"Ders eklendi: {course.name}")
        
        session.commit()
        print("Commit başarılı")
        logger.info("Dersler başarıyla eklendi")
        return True
    except Exception as e:
        session.rollback()
        print(f"Hata: {str(e)}")
        logger.error(f"Ders ekleme hatası: {str(e)}")
        return False
    finally:
        close_session()

def add_schedule():
    """Ders programını ekle"""
    session = get_session()
    try:
        # Derslikleri bul
        classrooms = {}
        for classroom in session.query(Classroom).all():
            classrooms[classroom.name] = classroom.id
        
        # Dersleri bul
        courses = {}
        for course in session.query(Course).all():
            courses[course.code] = course.id
        
        # Ders programı listesi
        schedule_data = [
            # Pazartesi
            {'course_id': courses['BLM101'], 'day': 'Pazartesi', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['BİL.LAB 1']},
            {'course_id': courses['BLM102'], 'day': 'Pazartesi', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM101'], 'day': 'Pazartesi', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['BİL.LAB 1']},
            {'course_id': courses['BLM102'], 'day': 'Pazartesi', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM102'], 'day': 'Pazartesi', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM103'], 'day': 'Pazartesi', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM104'], 'day': 'Pazartesi', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['E102']},
            {'course_id': courses['BLM105'], 'day': 'Pazartesi', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM103'], 'day': 'Pazartesi', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM104'], 'day': 'Pazartesi', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['E102']},
            {'course_id': courses['BLM105'], 'day': 'Pazartesi', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM103'], 'day': 'Pazartesi', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM105'], 'day': 'Pazartesi', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM106'], 'day': 'Pazartesi', 'start_time': '16:00', 'end_time': '17:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM106'], 'day': 'Pazartesi', 'start_time': '17:00', 'end_time': '18:00', 'classroom_id': classrooms['M301']},
            
            # Salı
            {'course_id': courses['BLM107'], 'day': 'Salı', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['M101']},
            {'course_id': courses['BLM107'], 'day': 'Salı', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['M101']},
            {'course_id': courses['BLM108'], 'day': 'Salı', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM108'], 'day': 'Salı', 'start_time': '12:00', 'end_time': '13:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM109'], 'day': 'Salı', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM110'], 'day': 'Salı', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM109'], 'day': 'Salı', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM110'], 'day': 'Salı', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM109'], 'day': 'Salı', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM110'], 'day': 'Salı', 'start_time': '16:00', 'end_time': '17:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM111'], 'day': 'Salı', 'start_time': '17:00', 'end_time': '19:00', 'classroom_id': classrooms['BİL.LAB 1']},
            {'course_id': courses['BLM112'], 'day': 'Salı', 'start_time': '19:00', 'end_time': '21:00', 'is_online': True},
            
            # Çarşamba
            {'course_id': courses['BLM113'], 'day': 'Çarşamba', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['M201']},
            {'course_id': courses['BLM114'], 'day': 'Çarşamba', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['D102']},
            {'course_id': courses['BLM115'], 'day': 'Çarşamba', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['M101']},
            {'course_id': courses['BLM113'], 'day': 'Çarşamba', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['M201']},
            {'course_id': courses['BLM114'], 'day': 'Çarşamba', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['D102']},
            {'course_id': courses['BLM115'], 'day': 'Çarşamba', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['M101']},
            {'course_id': courses['BLM116'], 'day': 'Çarşamba', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['D403']},
            {'course_id': courses['BLM113'], 'day': 'Çarşamba', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['M201']},
            {'course_id': courses['BLM113'], 'day': 'Çarşamba', 'start_time': '12:00', 'end_time': '13:00', 'classroom_id': classrooms['M201']},
            {'course_id': courses['BLM113'], 'day': 'Çarşamba', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['M201']},
            {'course_id': courses['BLM117'], 'day': 'Çarşamba', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM118'], 'day': 'Çarşamba', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['D403']},
            {'course_id': courses['BLM119'], 'day': 'Çarşamba', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['D202']},
            {'course_id': courses['BLM117'], 'day': 'Çarşamba', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM118'], 'day': 'Çarşamba', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['D403']},
            {'course_id': courses['BLM119'], 'day': 'Çarşamba', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['D202']},
            {'course_id': courses['BLM117'], 'day': 'Çarşamba', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM118'], 'day': 'Çarşamba', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['D403']},
            {'course_id': courses['BLM119'], 'day': 'Çarşamba', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['D202']},
            {'course_id': courses['BLM120'], 'day': 'Çarşamba', 'start_time': '16:00', 'end_time': '17:00', 'classroom_id': classrooms['BİL.LAB 1']},
            {'course_id': courses['BLM120'], 'day': 'Çarşamba', 'start_time': '17:00', 'end_time': '18:00', 'classroom_id': classrooms['BİL.LAB 1']},
            
            {'course_id': courses['BLM118'], 'day': 'Perşembe', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['D402']},
            {'course_id': courses['BLM121'], 'day': 'Perşembe', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM118'], 'day': 'Perşembe', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['D402']},
            {'course_id': courses['BLM121'], 'day': 'Perşembe', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM118'], 'day': 'Perşembe', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['D402']},
            {'course_id': courses['BLM122'], 'day': 'Perşembe', 'start_time': '13:00', 'end_time': '14:00', 'classroom_id': classrooms['BİL.LAB 2']},
            {'course_id': courses['BLM123'], 'day': 'Perşembe', 'start_time': '14:00', 'end_time': '15:00', 'is_online': True},
            {'course_id': courses['BLM122'], 'day': 'Perşembe', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['BİL.LAB 2']},
            {'course_id': courses['BLM123'], 'day': 'Perşembe', 'start_time': '15:00', 'end_time': '16:00', 'is_online': True},
            {'course_id': courses['BLM122'], 'day': 'Perşembe', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['BİL.LAB 2']},
            {'course_id': courses['BLM123'], 'day': 'Perşembe', 'start_time': '16:00', 'end_time': '17:00', 'is_online': True},
            {'course_id': courses['BLM124'], 'day': 'Perşembe', 'start_time': '16:00', 'end_time': '17:00', 'is_online': True},
            {'course_id': courses['BLM124'], 'day': 'Perşembe', 'start_time': '17:00', 'end_time': '18:00', 'is_online': True},
            {'course_id': courses['BLM125'], 'day': 'Perşembe', 'start_time': '19:00', 'end_time': '21:00', 'is_online': True},
            
            {'course_id': courses['BLM126'], 'day': 'Cuma', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM127'], 'day': 'Cuma', 'start_time': '09:00', 'end_time': '10:00', 'classroom_id': classrooms['E102']},
            {'course_id': courses['BLM103'], 'day': 'Cuma', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['S101']},
            {'course_id': courses['BLM126'], 'day': 'Cuma', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM127'], 'day': 'Cuma', 'start_time': '10:00', 'end_time': '11:00', 'classroom_id': classrooms['E102']},
            {'course_id': courses['BLM126'], 'day': 'Cuma', 'start_time': '11:00', 'end_time': '12:00', 'classroom_id': classrooms['AMFİ B']},
            {'course_id': courses['BLM128'], 'day': 'Cuma', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM129'], 'day': 'Cuma', 'start_time': '14:00', 'end_time': '15:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM128'], 'day': 'Cuma', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM129'], 'day': 'Cuma', 'start_time': '15:00', 'end_time': '16:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM128'], 'day': 'Cuma', 'start_time': '16:00', 'end_time': '17:00', 'classroom_id': classrooms['M301']},
            {'course_id': courses['BLM129'], 'day': 'Cuma', 'start_time': '16:00', 'end_time': '17:00', 'classroom_id': classrooms['S201']},
            {'course_id': courses['BLM130'], 'day': 'Cuma', 'start_time': '17:00', 'end_time': '19:00', 'classroom_id': classrooms['BİL.LAB 1']}
        ]
        
        # Ders programını ekle
        for schedule_item in schedule_data:
            schedule = Schedule(
                **schedule_item,
                academic_year='2024-2025',
                semester='Güz'
            )
            session.add(schedule)
        
        session.commit()
        logger.info("Ders programı başarıyla eklendi")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Ders programı ekleme hatası: {str(e)}")
        return False
    finally:
        close_session() 