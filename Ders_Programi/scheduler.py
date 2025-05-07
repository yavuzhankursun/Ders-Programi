from models import Department, Course, Schedule, Classroom, Faculty, User, SharedCourse
from db import get_session, close_session
import pandas as pd
import random
import logging
import json
import os
from datetime import datetime

# Logger tanımla
logger = logging.getLogger(__name__)

class DersProgramiOlusturucu:
    """
    Bu sınıf, ders programı oluşturma ve yönetim işlemlerini gerçekleştirir.
    Bölümlere, akademik yıla ve döneme göre ders programlarını oluşturur,
    çakışmaları kontrol eder ve programları Excel'e aktarır.
    """
    def __init__(self, bolum_idleri, akademik_yil, donem):
        """
        DersProgramiOlusturucu sınıfının başlatıcı fonksiyonu.
        
        Parametreler:
            bolum_idleri (list): Programı oluşturulacak bölümlerin ID listesi
            akademik_yil (str): Akademik yıl bilgisi (örn: 2023-2024)
            donem (str): Dönem bilgisi (Güz/Bahar)
        """
        # Temel parametreleri sakla
        self.bolum_idleri = bolum_idleri
        self.akademik_yil = akademik_yil
        self.donem = donem
        
        # Zaman dilimlerini tanımla (Her gün için aynı zaman dilimleri kullanılıyor)
        self.zaman_dilimleri = {
            'Pazartesi': ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                        '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00',
                        '18:00-19:00', '19:00-20:00', '20:00-21:00'],
            'Salı': ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                    '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00',
                    '18:00-19:00', '19:00-20:00', '20:00-21:00'],
            'Çarşamba': ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                        '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00',
                        '18:00-19:00', '19:00-20:00', '20:00-21:00'],
            'Perşembe': ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                        '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00',
                        '18:00-19:00', '19:00-20:00', '20:00-21:00'],
            'Cuma': ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                    '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00',
                    '18:00-19:00', '19:00-20:00', '20:00-21:00']
        }
        
        # Çevrimiçi (online) olarak atanabilecek zaman dilimleri
        # Genellikle akşam saatleri online dersler için ayrılır
        self.cevrimici_saatler = [
            '17:00-18:00', '18:00-19:00', '19:00-20:00', '20:00-21:00'
        ]
        
        # Derslik bilgilerini tutacak sözlük
        self.derslikler = {}
        
        # Öğretim elemanlarının programlarını tutacak sözlük
        self.ogretim_elemani_programlari = {}
        
        # Bölümlere göre sınıf programlarını tutacak sözlük
        self.sinif_programlari = {}
        
        # Ortak dersler için çakışma kontrolü yapılacak harita
        self.ortak_ders_haritasi = {}
        
        # Bilgisayar ve Yazılım Mühendisliği bölüm ID'lerini sakla
        self.blm_id = None
        self.yzm_id = None
        
    def get_courses_by_department(self, department_id):
        """
        Belirli bir bölüme ait tüm dersleri veritabanından getirir.
        
        Parametreler:
            department_id (int): Dersleri getirilecek bölümün ID'si
            
        Dönüş:
            list: Bölüme ait tüm ders nesnelerinin listesi
        """
        session = get_session()
        try:
            return session.query(Course).filter_by(department_id=department_id).all()
        finally:
            close_session()
    
    def get_shared_courses(self, course):
        """
        Bir dersin ortak verildiği tüm bölümleri bulur.
        
        Parametreler:
            course (Course): Ortak verildiği bölümleri araştırılacak ders
            
        Dönüş:
            list: Dersin ortak verildiği bölüm ID'lerinin listesi
        """
        session = get_session()
        try:
            shared = session.query(SharedCourse).filter_by(course_id=course.id).all()
            return [sc.shared_with_department_id for sc in shared]
        finally:
            close_session()
    
    def initialize_schedule_data(self):
        """
        Zamanlama işlemi için gerekli tüm verileri hazırlar.
        
        Bu fonksiyon, derslikleri, öğretim elemanlarının uygunluklarını,
        sınıf programlarını ve ortak ders bilgilerini başlangıç durumuna getirir.
        Programlama işlemi başlamadan önce çağrılması gerekir.
        """
        session = get_session()
        try:
            # BLM ve YZM bölüm ID'lerini bul (sık kullanıldığı için saklıyoruz)
            blm_bolum = session.query(Department).filter_by(code='BLM').first()
            yzm_bolum = session.query(Department).filter_by(code='YZM').first()
            
            if blm_bolum:
                self.blm_id = blm_bolum.id
            if yzm_bolum:
                self.yzm_id = yzm_bolum.id
            
            # Ortak dersleri bul ve eşleştir
            ortak_dersler = session.query(SharedCourse).all()
            for ortak_ders in ortak_dersler:
                ders = session.query(Course).get(ortak_ders.course_id)
                if ders:
                    # Ortak ders bilgisini kaydet
                    if ders.id not in self.ortak_ders_haritasi:
                        self.ortak_ders_haritasi[ders.id] = []
                    self.ortak_ders_haritasi[ders.id].append(ortak_ders.shared_with_department_id)
                    
                    logger.info(f"Ortak ders tespit edildi: {ders.name} (ID: {ders.id}) - Bölüm: {ortak_ders.shared_with_department_id}")
            
            # Derslikleri yükle ve programları başlat
            tum_derslikler = session.query(Classroom).all()
            for derslik in tum_derslikler:
                self.derslikler[derslik.id] = {
                    'name': derslik.name,
                    'capacity': derslik.capacity,
                    'type': derslik.type,
                    'schedule': {gun: [] for gun in self.zaman_dilimleri.keys()}
                }
            
            # Öğretim elemanlarının programlarını ve uygunluklarını yükle
            ogretim_elemanlari = session.query(Faculty).all()
            for ogretim_elemani in ogretim_elemanlari:
                kullanici = session.query(User).get(ogretim_elemani.user_id)
                self.ogretim_elemani_programlari[ogretim_elemani.id] = {
                    'name': kullanici.get_full_name() if kullanici else 'Bilinmeyen',
                    'availability': ogretim_elemani.get_availability() or {gun: [] for gun in self.zaman_dilimleri.keys()},
                    'schedule': {gun: [] for gun in self.zaman_dilimleri.keys()}
                }
            
            # Bölümlere göre sınıf programlarını başlat
            for bolum_id in self.bolum_idleri:
                bolum = session.query(Department).get(bolum_id)
                self.sinif_programlari[bolum_id] = {
                    'name': bolum.name,
                    'code': bolum.code,
                    'years': {  # Her sınıf yılı için ayrı program (1. sınıf, 2. sınıf, vb.)
                        1: {gun: [] for gun in self.zaman_dilimleri.keys()},
                        2: {gun: [] for gun in self.zaman_dilimleri.keys()},
                        3: {gun: [] for gun in self.zaman_dilimleri.keys()},
                        4: {gun: [] for gun in self.zaman_dilimleri.keys()}
                    }
                }
        finally:
            close_session()
    
    def is_classroom_available(self, classroom_id, day, time_slot):
        """
        Dersliğin belirtilen gün ve zaman diliminde müsait olup olmadığını kontrol eder.
        
        Parametreler:
            classroom_id (int): Kontrol edilecek dersliğin ID'si
            day (str): Kontrol edilecek gün (Pazartesi, Salı, vb.)
            time_slot (str): Kontrol edilecek zaman dilimi (08:00-09:00, vb.)
            
        Dönüş:
            bool: Derslik müsaitse True, değilse False
        """
        return time_slot not in self.derslikler[classroom_id]['schedule'][day]
    
    def is_faculty_available(self, faculty_id, day, time_slot):
        """
        Öğretim elemanının belirtilen gün ve zaman diliminde müsait olup olmadığını kontrol eder.
        
        Bu kontrol, öğretim elemanının hem mevcut programını hem de kişisel uygunluk
        bilgilerini dikkate alır.
        
        Parametreler:
            faculty_id (int): Kontrol edilecek öğretim elemanı ID'si
            day (str): Kontrol edilecek gün (Pazartesi, Salı, vb.)
            time_slot (str): Kontrol edilecek zaman dilimi (08:00-09:00, vb.)
            
        Dönüş:
            bool: Öğretim elemanı müsaitse True, değilse False
        """
        ogretim_elemani_bilgisi = self.ogretim_elemani_programlari.get(faculty_id)
        if not ogretim_elemani_bilgisi:
            return True  # Verisi yoksa müsait kabul et
        
        # Programda zaten varsa müsait değil (başka bir dersi var)
        if time_slot in ogretim_elemani_bilgisi['schedule'][day]:
            logger.info(f"Öğretim üyesi {ogretim_elemani_bilgisi['name']} {day} günü {time_slot} saatinde başka bir ders veriyor.")
            return False
        
        # Uygunluk bilgisi varsa kontrol et
        if ogretim_elemani_bilgisi['availability']:
            # Gün için uygunluk bilgisi yoksa, müsait kabul et
            if day not in ogretim_elemani_bilgisi['availability']:
                logger.info(f"Öğretim üyesi {ogretim_elemani_bilgisi['name']} için {day} günü uygunluk bilgisi yok, müsait kabul ediliyor.")
                return True
            
            # Gün için uygunluk listesi boşsa (hiç müsait değil)
            if not ogretim_elemani_bilgisi['availability'][day]:
                logger.info(f"Öğretim üyesi {ogretim_elemani_bilgisi['name']} {day} günü hiç müsait değil.")
                return False
            
            # Belirli saat dilimi için uygunluk kontrolü
            musait_mi = time_slot in ogretim_elemani_bilgisi['availability'][day]
            if not musait_mi:
                logger.info(f"Öğretim üyesi {ogretim_elemani_bilgisi['name']} {day} günü {time_slot} saatinde müsait değil.")
            
            return musait_mi
        
        return True  # Uygunluk bilgisi yoksa müsait kabul et
    
    def is_class_available(self, department_id, year, day, time_slot):
        """
        Belirli bir sınıfın (bölüm+yıl) belirtilen gün ve zaman diliminde müsait olup olmadığını kontrol eder.
        
        Parametreler:
            department_id (int): Bölüm ID'si
            year (int): Sınıf yılı (1, 2, 3 veya 4)
            day (str): Kontrol edilecek gün (Pazartesi, Salı, vb.)
            time_slot (str): Kontrol edilecek zaman dilimi (08:00-09:00, vb.)
            
        Dönüş:
            bool: Sınıf müsaitse True, değilse False
        """
        return time_slot not in self.sinif_programlari[department_id]['years'][year][day]
    
    def find_suitable_classroom(self, course, day, time_slot):
        """
        Ders için uygun derslik bulur. Çevrimiçi dersler için derslik gerekmez.
        LAB tipi dersler için LAB tipi derslik, teorik dersler için normal derslik aranır.
        
        Parametreler:
            course (Course): Derslik aranan ders
            day (str): Ders günü
            time_slot (str): Ders saati
            
        Dönüş:
            int/None: Uygun derslik ID'si veya çevrimiçi ders ise None
        """
        session = get_session()
        try:
            # Çevrimiçi ders ise dersliğe gerek yok
            if course.is_online or time_slot in self.cevrimici_saatler:
                return None
            
            # LAB tipi ders için LAB tipi derslik gerekli
            is_lab_course = 'LAB' in course.name.upper()
            
            suitable_classrooms = []
            
            for classroom_id, classroom_data in self.derslikler.items():
                # Derslik müsait değilse atla
                if not self.is_classroom_available(classroom_id, day, time_slot):
                    continue
                
                # LAB dersini normal dersliğe koyma veya normal dersi LAB'a koyma
                if (is_lab_course and classroom_data['type'] != 'LAB') or (not is_lab_course and classroom_data['type'] == 'LAB'):
                    continue
                
                # Kapasite yeterli mi?
                # TODO: Gerçek öğrenci sayısı için mantıklı bir tahmin yap
                tahmini_ogrenci_sayisi = 30  # Varsayılan öğrenci sayısı
                
                if classroom_data['capacity'] >= tahmini_ogrenci_sayisi:
                    suitable_classrooms.append((classroom_id, classroom_data['capacity']))
            
            # Kapasiteye göre sırala (en uygun önce)
            suitable_classrooms.sort(key=lambda x: x[1])
            
            # Uygun derslik varsa ilkini döndür
            if suitable_classrooms:
                return suitable_classrooms[0][0]
            
            # Uygun derslik yoksa, ders online yapılabilir
            if not is_lab_course:  # LAB dersleri online yapılamaz
                logger.warning(f"{course.name} dersi için uygun derslik bulunamadı. Online yapılacak.")
                return None
            
            # LAB dersi için derslik şart
            logger.error(f"{course.name} LAB dersi için uygun derslik bulunamadı!")
            return None
        finally:
            close_session()
    
    def update_schedules(self, course, day, time_slot, classroom_id):
        """
        Bir ders için programlama yapıldığında tüm ilgili programları günceller.
        
        Bu fonksiyon, bir ders programlandığında:
        - Dersin ait olduğu sınıfın programını
        - Eğer ortak dersse, diğer bölümlerin de programlarını
        - Dersliğin programını
        - Öğretim elemanının programını günceller.
        
        Parametreler:
            course (Course): Programlanan ders
            day (str): Programlanan gün
            time_slot (str): Programlanan zaman dilimi
            classroom_id (int): Atanan derslik ID'si (online dersler için None)
        """
        # Eğer ders ortak veriliyorsa
        ortak_ders_mi = course.id in self.ortak_ders_haritasi
        
        # Dersin yılını hesapla (1-2 -> 1, 3-4 -> 2, 5-6 -> 3, 7-8 -> 4)
        sinif_yili = ((course.semester - 1) // 2) + 1
        
        # Sınıf programını güncelle
        self.sinif_programlari[course.department_id]['years'][sinif_yili][day].append(time_slot)
        
        # Ortak dersler için diğer bölümlerin de programlarını güncelle
        if ortak_ders_mi:
            for ortak_bolum_id in self.ortak_ders_haritasi[course.id]:
                # Ortak verilen 2. sınıf dersi, diğer bölümde de 2. sınıfa verilir varsayalım
                if ortak_bolum_id in self.sinif_programlari:
                    self.sinif_programlari[ortak_bolum_id]['years'][sinif_yili][day].append(time_slot)
        
        # Derslik programını güncelle
        if classroom_id:
            self.derslikler[classroom_id]['schedule'][day].append(time_slot)
        
        # Öğretim elemanı programını güncelle
        if course.instructor_id:
            self.ogretim_elemani_programlari[course.instructor_id]['schedule'][day].append(time_slot)
    
    def save_schedule_to_db(self, all_schedules):
        """
        Oluşturulan programı veritabanına kaydeder.
        
        Önce mevcut program tamamen temizlenir ve ardından
        yeni oluşturulan program veritabanına kaydedilir.
        
        Parametreler:
            all_schedules (list): Kaydedilecek program bilgilerini içeren liste
        """
        session = get_session()
        try:
            # Mevcut programı temizle
            session.query(Schedule).filter_by(
                academic_year=self.akademik_yil,
                semester=self.donem
            ).delete()
            session.commit()
            
            # Yeni programı ekle
            for program_bilgisi in all_schedules:
                program = Schedule(
                    course_id=program_bilgisi['course_id'],
                    day=program_bilgisi['day'],
                    start_time=program_bilgisi['start_time'],
                    end_time=program_bilgisi['end_time'],
                    classroom_id=program_bilgisi['classroom_id'],
                    is_online=program_bilgisi['is_online'],
                    academic_year=self.akademik_yil,
                    semester=self.donem
                )
                session.add(program)
            
            session.commit()
            logger.info(f"Toplam {len(all_schedules)} ders programı veritabanına kaydedildi.")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Program kaydederken hata: {str(e)}")
            return False
        finally:
            close_session()
    
    def _schedule_courses_to_days(self, courses, all_schedules, forced_distribution=False):
        """
        Dersleri haftanın günlerine dengeli şekilde dağıtır.
        
        Bu fonksiyon, dersleri yüklülük durumlarına göre günlere dağıtır.
        Her dersin haftalık ders saati sayısına göre hangi günlere yerleştirileceğini belirler.
        
        Parametreler:
            courses (list): Programlanacak dersler listesi
            all_schedules (list): Oluşturulan programların kaydedileceği liste
            forced_distribution (bool): Derslerin farklı günlere dağıtılıp dağıtılmayacağı
        """
        # Dersleri saat sayısına göre sırala (çoktan aza) - Önce çok saatli dersler yerleştirilir
        courses.sort(key=lambda x: x.weekly_hours, reverse=True)
        
        hafta_gunleri = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        
        # Gün bazında ders sayısını takip etmek için
        gun_yuklulukleri = {gun: 0 for gun in hafta_gunleri}
        
        for ders in courses:
            # Toplam ders saati
            gereken_ders_saati = ders.weekly_hours
            if gereken_ders_saati <= 0:
                continue
            
            # Dersin yılını hesapla
            sinif_yili = ((ders.semester - 1) // 2) + 1
            
            # Ders günlere dağıtılacak
            gun_basina_saat = {}
            kullanilan_gunler = []
            
            # Zorla dengeli dağıtım yapılacak mı?
            if forced_distribution and gereken_ders_saati > 1:
                # En az yüklü günleri belirle
                siralanan_gunler = sorted(hafta_gunleri, key=lambda d: gun_yuklulukleri[d])
                
                # İlk 2 en az yüklü güne birer ders koy
                for i in range(min(gereken_ders_saati, len(hafta_gunleri))):
                    gun = siralanan_gunler[i % len(siralanan_gunler)]
                    if gun not in gun_basina_saat:
                        gun_basina_saat[gun] = 0
                    gun_basina_saat[gun] += 1
                    kullanilan_gunler.append(gun)
                    gun_yuklulukleri[gun] += 1
            else:
                # Rastgele seçilen tek bir güne yerleştir
                gun = random.choice(hafta_gunleri)
                gun_basina_saat[gun] = gereken_ders_saati
                kullanilan_gunler.append(gun)
                gun_yuklulukleri[gun] += gereken_ders_saati
            
            # Her gün için gereken ders saati kadar yerleştir
            for gun, gun_saati in gun_basina_saat.items():
                if gun_saati <= 0:
                    continue
                
                # Bu günde yerleştirilecek saatler
                yerlestirilecek_saat = gun_saati
                uygun_zaman_dilimleri = []
                
                # Kullanılabilir zaman dilimlerini bul
                for zaman_dilimi in self.zaman_dilimleri[gun]:
                    # Uygunluk kontrolü
                    if self._is_slot_available(ders, gun, zaman_dilimi, sinif_yili):
                        uygun_zaman_dilimleri.append(zaman_dilimi)
                
                # Seçilen slotları zamana göre sırala
                uygun_zaman_dilimleri.sort()
                
                # Her saat için uygun zaman dilimini kullan
                for i in range(min(yerlestirilecek_saat, len(uygun_zaman_dilimleri))):
                    zaman = uygun_zaman_dilimleri[i]
                    baslangic_saati, bitis_saati = zaman.split('-')
                    
                    # Çevrimiçi ders mi?
                    cevrimici_mi = ders.is_online or zaman in self.cevrimici_saatler
                    
                    # Uygun derslik bul
                    derslik_id = None if cevrimici_mi else self.find_suitable_classroom(ders, gun, zaman)
                    
                    # Programları güncelle
                    self.update_schedules(ders, gun, zaman, derslik_id)
                    
                    # Zamanlama bilgisini kaydet
                    all_schedules.append({
                        'course_id': ders.id,
                        'day': gun,
                        'start_time': baslangic_saati,
                        'end_time': bitis_saati,
                        'classroom_id': derslik_id,
                        'is_online': cevrimici_mi
                    })
                    
                    logger.info(f"Ders {ders.code} - {gun} günü {zaman} saatine yerleştirildi.")

    def _is_slot_available(self, course, day, time_slot, year):
        """
        Belirtilen zaman diliminde bir dersin planlanıp planlanamayacağını kontrol eder.
        
        Bu kontrol şunları içerir:
        - İlgili sınıfın uygunluğu
        - Ortak ders ise diğer bölümlerin sınıflarının uygunluğu
        - Öğretim elemanının uygunluğu
        
        Parametreler:
            course (Course): Kontrol edilecek ders
            day (str): Kontrol edilecek gün
            time_slot (str): Kontrol edilecek zaman dilimi
            year (int): Dersin verildiği sınıf yılı
            
        Dönüş:
            bool: Zaman dilimi uygunsa True, değilse False
        """
        # Sınıf müsait mi?
        sinif_musait_mi = self.is_class_available(course.department_id, year, day, time_slot)
        if not sinif_musait_mi:
            return False
        
        # Ortak ders ise, diğer bölümlerin sınıfları da müsait mi?
        if course.id in self.ortak_ders_haritasi:
            for ortak_bolum_id in self.ortak_ders_haritasi[course.id]:
                if ortak_bolum_id in self.sinif_programlari:
                    if not self.is_class_available(ortak_bolum_id, year, day, time_slot):
                        return False
        
        # Öğretim üyesi müsait mi?
        if course.instructor_id:
            if not self.is_faculty_available(course.instructor_id, day, time_slot):
                return False
        
        return True

    def generate_schedule(self):
        """
        Tüm dersler için ders programını oluşturur.
        
        Bu fonksiyon aşağıdaki adımları gerçekleştirir:
        1. Gerekli başlangıç verilerini yükler
        2. Öncelikle sabit zamanlı dersleri yerleştirir
        3. Sonra ortak dersleri yerleştirir 
        4. Son olarak diğer dersleri yerleştirir
        5. Oluşturulan programı veritabanına kaydeder
        
        Dönüş:
            bool: Program başarıyla oluşturulduysa True, aksi halde False
        """
        try:
            self.initialize_schedule_data()
            
            all_schedules = []  # Tüm zamanlamaları saklamak için
            
            # Önce fixed time'ı olan dersleri yerleştir
            for dept_id in self.bolum_idleri:
                courses = self.get_courses_by_department(dept_id)
                
                # Sabit zamanlı dersleri filtrele
                sabit_zamanli_dersler = [c for c in courses if c.get_fixed_time()]
                
                for ders in sabit_zamanli_dersler:
                    sabit_zamanlar = ders.get_fixed_time()
                    if not sabit_zamanlar:
                        continue
                    
                    logger.info(f"Sabit zamanlı ders yerleştiriliyor: {ders.name} - {sabit_zamanlar}")
                    
                    for gun, zaman_dilimleri in sabit_zamanlar.items():
                        for zaman_dilimi in zaman_dilimleri:
                            baslangic_saati, bitis_saati = zaman_dilimi.split('-')
                            
                            # Çevrimiçi ders mi?
                            cevrimici_mi = ders.is_online or zaman_dilimi in self.cevrimici_saatler
                            
                            # Uygun derslik bul
                            derslik_id = None if cevrimici_mi else self.find_suitable_classroom(ders, gun, zaman_dilimi)
                            
                            # Programları güncelle
                            self.update_schedules(ders, gun, zaman_dilimi, derslik_id)
                            
                            # Zamanlama bilgisini kaydet
                            all_schedules.append({
                                'course_id': ders.id,
                                'day': gun,
                                'start_time': baslangic_saati,
                                'end_time': bitis_saati,
                                'classroom_id': derslik_id,
                                'is_online': cevrimici_mi
                            })
            
            # Dersleri sınıflandır
            ortak_dersler = []
            normal_dersler = []
            
            for bolum_id in self.bolum_idleri:
                dersler = self.get_courses_by_department(bolum_id)
                
                # Sabit zamanlı olmayan dersleri filtrele
                for ders in dersler:
                    # Zaten yerleştirilmiş mi kontrol et
                    if any(s['course_id'] == ders.id for s in all_schedules):
                        continue
                        
                    if ders.id in self.ortak_ders_haritasi:
                        if ders not in ortak_dersler:
                            ortak_dersler.append(ders)
                    else:
                        if ders not in normal_dersler:
                            normal_dersler.append(ders)
            
            # Önce ortak dersleri yerleştir
            logger.info(f"Ortak dersler yerleştiriliyor ({len(ortak_dersler)} ders)")
            self._schedule_courses_to_days(ortak_dersler, all_schedules, forced_distribution=True)
            
            # Sonra diğer dersleri yerleştir
            logger.info(f"Normal dersler yerleştiriliyor ({len(normal_dersler)} ders)")
            self._schedule_courses_to_days(normal_dersler, all_schedules, forced_distribution=True)
            
            # Programlanamamış dersleri kontrol et
            zamanlanamayan_dersler = []
            for bolum_id in self.bolum_idleri:
                dersler = self.get_courses_by_department(bolum_id)
                for ders in dersler:
                    zamanlanan_saat = sum(1 for s in all_schedules if s['course_id'] == ders.id)
                    if zamanlanan_saat < ders.weekly_hours:
                        zamanlanamayan_dersler.append({
                            'course': ders.name,
                            'code': ders.code,
                            'hours_needed': ders.weekly_hours,
                            'hours_scheduled': zamanlanan_saat
                        })
            
            # Gün bazında ders sayılarını log'la
            gun_ders_sayilari = {}
            for gun in self.zaman_dilimleri.keys():
                gun_ders_sayilari[gun] = len([s for s in all_schedules if s['day'] == gun])
                logger.info(f"{gun} günü için toplam {gun_ders_sayilari[gun]} ders zamanlandı.")
            
            if zamanlanamayan_dersler:
                logger.warning(f"{len(zamanlanamayan_dersler)} ders tam olarak zamanlanamadı!")
                for zamanlanamayan in zamanlanamayan_dersler:
                    logger.warning(f"  {zamanlanamayan['code']} - {zamanlanamayan['course']}: {zamanlanamayan['hours_scheduled']}/{zamanlanamayan['hours_needed']} saat zamanlandı")
            
            # Programı veritabanına kaydet
            basarili = self.save_schedule_to_db(all_schedules)
            
            if basarili:
                # Günlere göre dağılımı hazırla
                gun_dagilimi = ", ".join([f"{gun}: {sayi}" for gun, sayi in gun_ders_sayilari.items()])
                return True, f"{len(all_schedules)} ders zamanlandı ({gun_dagilimi}), {len(zamanlanamayan_dersler)} ders tam zamanlanamadı."
            else:
                return False, "Veritabanına kaydetme hatası!"
            
        except Exception as e:
            logger.error(f"Program oluşturulurken hata: {str(e)}")
            return False, f"Hata: {str(e)}"
    
    def export_to_excel(self):
        """
        Ders programını Excel dosyasına aktarır.
        
        Bu fonksiyon:
        1. Her bölüm için ayrı bir çalışma sayfası oluşturur
        2. Her sınıf yılı (1-4) için ayrı bir program tablosu oluşturur
        3. Tüm sınıfların birleştirildiği genel bir sayfa oluşturur
        4. Öğretim elemanlarının ders programlarını içeren bir sayfa oluşturur
        5. Dersliklerin doluluk programlarını içeren bir sayfa oluşturur
        
        Dönüş:
            tuple: (başarı durumu, mesaj veya dosya yolu)
        """
        try:
            # Excel dosyası için klasör oluştur
            if not os.path.exists("excel"):
                os.makedirs("excel")
            
            # Dosya adı oluştur
            zaman_damgasi = datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"excel/ders_programi_{zaman_damgasi}.xlsx"
            
            # Hata ayıklama (debug) log dosyası
            hata_ayiklama_log = f"excel/debug_log_{zaman_damgasi}.txt"
            with open(hata_ayiklama_log, 'w', encoding='utf-8') as log_dosyasi:
                log_dosyasi.write(f"Excel aktarım hata ayıklama log dosyası - {datetime.now()}\n\n")
                
                # Her bölüm ve sınıf için veritabanındaki dersleri say
                session = get_session()
                try:
                    log_dosyasi.write("Veritabanındaki derslerin dağılımı:\n")
                    for bolum_id in self.bolum_idleri:
                        bolum = session.query(Department).get(bolum_id)
                        if not bolum:
                            continue
                            
                        log_dosyasi.write(f"\nBölüm: {bolum.name} (ID: {bolum_id})\n")
                        
                        for sinif_yili in range(1, 5):
                            # Bu sınıfa ait dönemler
                            donemler = [sinif_yili*2-1, sinif_yili*2]  # 1-2, 3-4, 5-6, 7-8
                            
                            # Bu dönemlerdeki dersleri say
                            ders_sayisi = session.query(Course).filter(
                                Course.department_id == bolum_id,
                                Course.semester.in_(donemler)
                            ).count()
                            
                            # Bu dönemlerdeki program kayıtlarını say
                            program_sayisi = session.query(Schedule).join(Course).filter(
                                Course.department_id == bolum_id,
                                Course.semester.in_(donemler),
                                Schedule.academic_year == self.akademik_yil,
                                Schedule.semester == self.donem
                            ).count()
                            
                            log_dosyasi.write(f"  {sinif_yili}. Sınıf (Dönem {donemler}): {ders_sayisi} ders, {program_sayisi} program kaydı\n")
                            
                finally:
                    close_session()
            
            # Excel yazıcı oluştur
            excel_yazici = pd.ExcelWriter(dosya_adi, engine='xlsxwriter')
            calisma_kitabi = excel_yazici.book
            
            # Excel biçimleri (formatlar)
            baslik_formati = calisma_kitabi.add_format({
                'bold': True, 
                'font_size': 14, 
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4472C4', 
                'font_color': 'white'
            })
            
            ustbaslik_formati = calisma_kitabi.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#D9E1F2',
                'border': 1
            })
            
            gun_formati = calisma_kitabi.add_format({
                'bold': True,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#E2EFDA',
                'border': 1
            })
            
            saat_formati = calisma_kitabi.add_format({
                'bold': True,
                'font_size': 10,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            # Sınıf formatları - farklı renkler (her sınıf yılı için ayrı renk)
            sinif_formatlari = {
                1: calisma_kitabi.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'bg_color': '#FCE4D6'  # Açık turuncu - 1. sınıf
                }),
                2: calisma_kitabi.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'bg_color': '#D9EAD3'  # Açık yeşil - 2. sınıf
                }),
                3: calisma_kitabi.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'bg_color': '#D0E0E3'  # Açık mavi - 3. sınıf
                }),
                4: calisma_kitabi.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'bg_color': '#FFF2CC'  # Açık sarı - 4. sınıf
                })
            }
            
            bos_hucre_formati = calisma_kitabi.add_format({
                'border': 1,
                'bg_color': '#F2F2F2'  # Açık gri - boş hücreler için
            })
            
            # Önce özet bilgi sayfası oluştur
            ozet_sayfasi = calisma_kitabi.add_worksheet("ÖZET")
            ozet_sayfasi.merge_range('A1:B1', 'DERS PROGRAMI ÖZET BİLGİLERİ', baslik_formati)
            
            # Özet bilgileri ekle
            ozet_verileri = [
                ['Akademik Yıl', self.akademik_yil],
                ['Dönem', self.donem],
                ['Oluşturulma Tarihi', datetime.now().strftime('%d.%m.%Y %H:%M:%S')]
            ]
            
            # Bölüm bilgilerini ekle
            session = get_session()
            try:
                ozet_sayfasi.set_column('A:A', 25)
                ozet_sayfasi.set_column('B:B', 30)
                
                for i, satir in enumerate(ozet_verileri):
                    ozet_sayfasi.write(i+1, 0, satir[0], ustbaslik_formati)
                    ozet_sayfasi.write(i+1, 1, satir[1])
                
                # Bölüm bilgileri
                row = len(ozet_verileri) + 2
                ozet_sayfasi.merge_range(f'A{row}:B{row}', 'BÖLÜM BİLGİLERİ', baslik_formati)
                row += 1
                
                ozet_sayfasi.write(row, 0, 'Bölüm Adı', ustbaslik_formati)
                ozet_sayfasi.write(row, 1, 'Bölüm Kodu', ustbaslik_formati)
                row += 1
                
                for dept_id in self.bolum_idleri:
                    department = session.query(Department).get(dept_id)
                    if department:
                        ozet_sayfasi.write(row, 0, department.name)
                        ozet_sayfasi.write(row, 1, department.code)
                        row += 1
            finally:
                close_session()
            
            # Ayrıca tüm sınıfları bir arada gösteren bir sayfa oluştur
            all_classes_sheet = calisma_kitabi.add_worksheet("Tüm Sınıflar")
            all_classes_sheet.merge_range('A1:J1', f"TÜM SINIFLAR DERS PROGRAMI - {self.akademik_yil} {self.donem}", baslik_formati)
            
            # Sütun başlıkları
            all_classes_sheet.set_column('A:A', 15)  # Saat sütunu genişliği
            all_classes_sheet.write(1, 0, "Gün/Saat", ustbaslik_formati)
            
            # Bölüm ve sınıf başlıkları
            column = 1
            dept_class_map = {}  # Sütun eşleştirmelerini saklamak için
            
            for dept_id in self.bolum_idleri:
                session = get_session()
                try:
                    department = session.query(Department).get(dept_id)
                    if not department:
                        continue
                    
                    for year in range(1, 5):
                        dept_class_map[(dept_id, year)] = column
                        all_classes_sheet.set_column(column, column, 30)
                        all_classes_sheet.write(1, column, f"{department.code} {year}. Sınıf", ustbaslik_formati)
                        column += 1
                finally:
                    close_session()
            
            # Gün ve saat satırları
            current_row = 2
            days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
            times = self.zaman_dilimleri['Pazartesi']
            
            for day_idx, day in enumerate(days):
                # Gün başlığı
                all_classes_sheet.merge_range(current_row, 0, current_row, column-1, day, gun_formati)
                current_row += 1
                
                # Her zaman dilimi için satır oluştur
                for time_idx, time_slot in enumerate(times):
                    all_classes_sheet.write(current_row, 0, time_slot, saat_formati)
                    
                    # Her bölüm ve sınıf için hücre hazırla
                    for dept_id in self.bolum_idleri:
                        session = get_session()
                        try:
                            for year in range(1, 5):
                                cell_content = ""
                                col = dept_class_map.get((dept_id, year), 0)
                                
                                if col == 0:
                                    continue
                                
                                # Dersi bul
                                start_time, end_time = time_slot.split('-')
                                course_semesters = [year*2-1, year*2]
                                
                                schedules = session.query(Schedule).join(Course).filter(
                                    Course.department_id == dept_id,
                                    Schedule.academic_year == self.akademik_yil,
                                    Schedule.semester == self.donem,
                                    Schedule.day == day,
                                    Schedule.start_time == start_time,
                                    Course.semester.in_(course_semesters)
                                ).all()
                                
                                if schedules:
                                    for schedule in schedules:
                                        course = session.query(Course).get(schedule.course_id)
                                        faculty = None
                                        user = None
                                        
                                        if course and course.instructor_id:
                                            faculty = session.query(Faculty).get(course.instructor_id)
                                            if faculty and faculty.user_id:
                                                user = session.query(User).get(faculty.user_id)
                                        
                                        classroom = None
                                        if schedule.classroom_id:
                                            classroom = session.query(Classroom).get(schedule.classroom_id)
                                        
                                        # Ders bilgilerini ekle
                                        if course:
                                            cell_content += f"{course.code}\n"
                                            cell_content += f"{course.name}\n"
                                            
                                            if faculty and user:
                                                title = faculty.title if faculty.title else ""
                                                cell_content += f"{title} {user.name} {user.surname}\n"
                                            else:
                                                cell_content += "Öğretim Üyesi Atanmamış\n"
                                            
                                            cell_content += f"({classroom.name if classroom else 'Online'})\n"
                                
                                # Hücreyi yaz
                                if cell_content:
                                    all_classes_sheet.write(current_row, col, cell_content, sinif_formatlari[year])
                                else:
                                    # Sınıf için hiç ders olup olmadığını kontrol et
                                    has_any_course = session.query(Course).filter(
                                        Course.department_id == dept_id,
                                        Course.semester.in_(course_semesters)
                                    ).count()
                                    
                                    if has_any_course == 0 and time_slot == self.zaman_dilimleri[day][0]:  # Sadece ilk satırda göster
                                        no_course_message = "Bu sınıf için\nhenüz ders kaydı\nbulunmamaktadır"
                                        all_classes_sheet.write(current_row, col, no_course_message, bos_hucre_formati)
                                    else:
                                        all_classes_sheet.write(current_row, col, "", bos_hucre_formati)
                        finally:
                            close_session()
                    
                    current_row += 1
                
                # Günler arasında boş satır
                all_classes_sheet.set_row(current_row, 10)
                current_row += 1
            
            # Excel dosyasını kaydet
            excel_yazici.close()
            return dosya_adi
        except Exception as e:
            logger.error(f"Excel'e aktarma hatası: {str(e)}")
            return None
