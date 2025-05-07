# schedule/scheduler.py

from .models import Ders, OgretimUyesi, Derslik, OgretimUyesiKisiti, DersProgramiSlotu, Bolum, GlobalKisiti
from django.db import transaction
from collections import defaultdict
import datetime
import copy # Durumu kopyalamak için
import random

# Zaman aralıkları ve günler (views.py'deki ile aynı veya ortak bir yerden alınabilir)
# Sabit olarak burada tanımlayalım
TIME_SLOTS = (
    [(datetime.time(h, 0), datetime.time(h + 1, 0)) for h in range(8, 17)] + 
    [(datetime.time(17,0), datetime.time(19,0)), (datetime.time(19,0), datetime.time(21,0))]
)
DAYS = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']

class BacktrackingScheduler:
    def __init__(self):
        # Veri yükleme için
        self.dersler_listesi = []
        self.derslikler = []
        self.hoca_kisitlari = defaultdict(set)
        self.global_kisitlari = set() # Yeni: Global kısıtlar için set [(gun, saat_tuple)]
        
        # Backtracking durumu için
        self.program_state = {} # Anahtar: (ders_id), Değer: (gun, saat_tuple, derslik_id, hoca_id)
        self.hoca_programi = defaultdict(set) # hoca_programi[hoca_id] = set([(gun, saat_tuple)])
        self.derslik_programi = defaultdict(set) # derslik_programi[derslik_id] = set([(gun, saat_tuple)])
        self.sinif_programi = defaultdict(set) # sinif_programi[(bolum_id, sinif)] = set([(gun, saat_tuple)])
        
        self.yerlesmeyen_dersler_rapor = [] # Sadece raporlama için

    def _time_to_tuple(self, time_obj):
        """datetime.time nesnesini (saat, dakika) tuple'ına çevirir."""
        return (time_obj.hour, time_obj.minute)

    def load_data(self):
        """Veritabanından gerekli verileri yükler ve önceliklendirir."""
        print("Veriler yükleniyor...")
        
        rektorluk_kodlari = ('ATA', 'TUR', 'DIL', 'ISG', 'BLM417', 'BLM426') # Örnek Rektörlük/Zorunlu kodları
        
        # Dersleri çek ve Rektörlük derslerini ayır
        tum_dersler = list(Ders.objects.prefetch_related('ogretim_uyeleri', 'bolum'))
        rektorluk_dersleri = [d for d in tum_dersler if d.ders_kodu.startswith(rektorluk_kodlari)]
        diger_dersler = [d for d in tum_dersler if not d.ders_kodu.startswith(rektorluk_kodlari)]
        
        # Diğer dersleri kendi içinde sırala (önce lab, sonra sınıf, sonra kontenjan)
        diger_dersler.sort(key=lambda d: (d.tip != 'LAB', d.sinif, -d.kontenjan))
        
        # Öncelikli Rektörlük derslerini başa alarak son listeyi oluştur
        self.dersler_listesi = rektorluk_dersleri + diger_dersler
        
        # Farklı çözümler bulma olasılığını artırmak için ders sırasını karıştır
        random.shuffle(self.dersler_listesi)
        
        self.derslikler = list(Derslik.objects.all())
        
        # Öğretim Üyesi Özel Kısıtları Yükle
        ogretim_uyesi_kisitlari = OgretimUyesiKisiti.objects.all()
        self.hoca_kisitlari.clear()
        for kisit in ogretim_uyesi_kisitlari:
            try: # Saat dönüşümünde hata olursa atla
                kisit_start_tuple = self._time_to_tuple(kisit.baslangic_saati)
                kisit_end_tuple = self._time_to_tuple(kisit.bitis_saati)
                
                # Tanımlı TIME_SLOTS üzerinde dönerek kısıt aralığı ile çakışanları bul
                for slot_start, slot_end in TIME_SLOTS:
                    slot_start_tuple = self._time_to_tuple(slot_start)
                    slot_end_tuple = self._time_to_tuple(slot_end)
                    
                    # Çakışma kontrolü: (KısıtBaşlangıç < SlotBitiş) VE (KısıtBitiş > SlotBaşlangıç)
                    # Kısıt aralığı [başlangıç, bitiş), slot aralığı [başlangıç, bitiş) olarak düşünülür.
                    if kisit_start_tuple < slot_end_tuple and kisit_end_tuple > slot_start_tuple:
                        # Bu saat dilimi kısıtlama ile çakışıyor, hocayı o slot için uygun değil olarak işaretle
                        self.hoca_kisitlari[kisit.ogretim_uyesi.id].add((kisit.gun, (slot_start, slot_end)))
            except AttributeError:
                # Eğer başlangıç veya bitiş saati None ise (veritabanında null ise) bu hatayı alabiliriz.
                print(f"Uyarı: Kısıt ID {kisit.id} için geçersiz saat değeri, atlanıyor.")
                         
        # Genel Kısıtları Yükle
        genel_kisitlar = GlobalKisiti.objects.all()
        self.global_kisitlari.clear()
        for kisit in genel_kisitlar:
            try:
                kisit_start_tuple = self._time_to_tuple(kisit.baslangic_saati)
                kisit_end_tuple = self._time_to_tuple(kisit.bitis_saati)
                for slot_start, slot_end in TIME_SLOTS:
                    slot_start_tuple = self._time_to_tuple(slot_start)
                    slot_end_tuple = self._time_to_tuple(slot_end)
                    if kisit_start_tuple < slot_end_tuple and kisit_end_tuple > slot_start_tuple:
                        self.global_kisitlari.add((kisit.gun, (slot_start, slot_end)))
            except AttributeError:
                print(f"Uyarı: Global Kısıt ID {kisit.id} için geçersiz saat değeri, atlanıyor.")

        print(f"{len(self.dersler_listesi)} ders, {len(self.derslikler)} derslik yüklendi.")
        
        # --- Kısıtlama Dağılımını Yazdır (Teşhis için) ---
        print("\n--- Kısıtlama Analizi ---")
        # Global Kısıtlar
        global_kisit_gun_sayac = defaultdict(int)
        for gun, _ in self.global_kisitlari:
            global_kisit_gun_sayac[gun] += 1
        print("Global Kısıtlı Slot Sayıları (Gün Bazında):")
        for gun in DAYS:
            print(f"  {gun}: {global_kisit_gun_sayac[gun]}")
            
        # Hoca Kısıtları
        hoca_kisit_gun_sayac = defaultdict(int)
        for hoca_id, kisit_set in self.hoca_kisitlari.items():
            for gun, _ in kisit_set:
                hoca_kisit_gun_sayac[gun] += 1
        print("Hoca Özel Kısıtlı Slot Sayıları (Gün Bazında, Tüm Hocalar Toplamı):")
        for gun in DAYS:
             print(f"  {gun}: {hoca_kisit_gun_sayac[gun]}")
        print("------------------------\n")
        # print(f"Toplam {sum(len(v) for v in self.hoca_kisitlari.values())} özel, {len(self.global_kisitlari)} genel kısıtlı slot bulundu.")

    def check_constraints(self, ders, gun, saat_tuple, derslik, hoca):
        """Mevcut duruma göre kısıtları kontrol eder. İhlal durumunda False döner."""
        start_time, end_time = saat_tuple
        saat_str = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        log_prefix = f"[Kısıt İhlali | {ders.ders_kodu} @ {gun} {saat_str}]"

        # 1. Genel Kısıt Kontrolü
        if (gun, saat_tuple) in self.global_kisitlari:
            # print(f"{log_prefix} Genel Kısıtlama.")
            return False
            
        # 2. Hoca Özel Kısıt/Ders Kontrolü (Parametre olarak gelen hoca için)
        if (gun, saat_tuple) in self.hoca_kisitlari.get(hoca.id, set()):
            # print(f"{log_prefix} Hoca ({hoca.ad_soyad}) özel kısıtlaması var.") # Logu azaltmak için kapatılabilir
            return False
        if (gun, saat_tuple) in self.hoca_programi.get(hoca.id, set()): 
            # print(f"{log_prefix} Hoca ({hoca.ad_soyad}) zaten başka derste")
            return False

        # 3. Derslik uygun mu (Başka ders, Tip, Kapasite)?
        if (gun, saat_tuple) in self.derslik_programi.get(derslik.id, set()):
            # print(f"{log_prefix} Derslik ({derslik.derslik_adi}) dolu: {self.derslik_programi[derslik.id][(gun, saat_tuple)]}")
            return False
        if ders.tip == 'LAB' and derslik.statu != 'LAB':
            print(f"{log_prefix} Ders tipi LAB ama Derslik ({derslik.derslik_adi}) LAB değil.")
            return False
        if ders.kontenjan > derslik.kapasite:
            print(f"{log_prefix} Kontenjan ({ders.kontenjan}) > Derslik kapasitesi ({derslik.derslik_adi}: {derslik.kapasite}).")
            return False

        # 4. Sınıf uygun mu (Başka ders)?
        sinif_key = (ders.bolum.id, ders.sinif)
        if (gun, saat_tuple) in self.sinif_programi.get(sinif_key, set()):
            # print(f"{log_prefix} Sınıf ({ders.bolum.bolum_kodu}-{ders.sinif}) zaten başka derste: {self.sinif_programi[sinif_key][(gun, saat_tuple)]}")
            return False
            
        # Zorunlu saat/Ortak ders/Online kontrolleri için potansiyel yer
        # Mevcut implementasyonda bu kontroller aktif değil.

        return True # Tüm kısıtlar sağlandı

    def _solve(self, ders_index):
        """Rekürsif backtracking fonksiyonu."""
        # Temel durum: Tüm dersler yerleştirildi
        if ders_index == len(self.dersler_listesi):
            return True

        ders = self.dersler_listesi[ders_index]
        # Potansiyel hocaları al
        potential_hocalar = list(ders.ogretim_uyeleri.all())
        
        if not potential_hocalar:
            print(f"Uyarı: {ders} için atanabilecek hoca bulunamadı, atlanıyor.")
            self.yerlesmeyen_dersler_rapor.append(ders)
            return self._solve(ders_index + 1)

        # Bu ders için tüm olası yerleştirmeleri (gün, saat, derslik, hoca) dene
        # Günlerin deneme sırasını rastgele yapalım
        available_days = list(DAYS)
        random.shuffle(available_days)
        
        for gun in available_days: # Rastgele sıralanmış günleri dene
            for saat_tuple in TIME_SLOTS:
                for derslik in self.derslikler:
                    # Bu derslik/saat için uygun bir hoca var mı?
                    for hoca in potential_hocalar:
                        # Kısıtları kontrol et (ders, gün, saat, derslik, hoca)
                        if self.check_constraints(ders, gun, saat_tuple, derslik, hoca):
                            # Geçerli yer ve HOCA bulundu, durumu güncelle ve yerleştir
                            start_time, end_time = saat_tuple
                            sinif_key = (ders.bolum.id, ders.sinif)
                            
                            self.program_state[ders.id] = (gun, saat_tuple, derslik.id, hoca.id)
                            self.hoca_programi[hoca.id].add((gun, saat_tuple))
                            self.derslik_programi[derslik.id].add((gun, saat_tuple))
                            self.sinif_programi[sinif_key].add((gun, saat_tuple))
                            
                            # print(f"Deneniyor: {ders.ders_kodu} ({hoca.ad_soyad}) -> {gun} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')} @ {derslik.derslik_adi}")

                            # Bir sonraki ders için rekürsif çağrı
                            if self._solve(ders_index + 1):
                                return True # Çözüm bulundu!

                            # Geri al (Backtrack): Bu yerleştirme çözüme götürmedi
                            # print(f"Geri Alınıyor: {ders.ders_kodu} ({hoca.ad_soyad})")
                            del self.program_state[ders.id]
                            self.hoca_programi[hoca.id].remove((gun, saat_tuple))
                            self.derslik_programi[derslik.id].remove((gun, saat_tuple))
                            self.sinif_programi[sinif_key].remove((gun, saat_tuple))
                            
                            # Not: Aynı ders/saat/derslik için başka hoca denemeye GEREK YOK,
                            # çünkü bir yerleştirme yaptık ve başarısız olduysa, geri alıp
                            # farklı bir derslik/saat/gün deneyeceğiz. Eğer ilk hoca uygunsa
                            # o atanır ve devam edilir. (Bu, algoritmayı basitleştirir)
                            # Eğer farklı hoca atamalarının farklı sonuçlar doğurmasını
                            # istiyorsak (örn. hoca yükü dengeleme), buradaki mantık değişir.
                            
                            # Ancak, eğer mevcut hoca ile kısıt sağlanmazsa, döngü diğer hocayı dener.
                            
        # Bu ders için hiçbir geçerli yer (gün/saat/derslik/hoca kombinasyonu) bulunamadı
        # print(f"Çıkmaz sokak: {ders.ders_kodu} yerleştirilemedi.")
        # Eğer bu ders atlanmışsa (hocası yoksa) listeden çıkaralım
        if ders in self.yerlesmeyen_dersler_rapor:
             self.yerlesmeyen_dersler_rapor.remove(ders)
             
        return False # Bu seviyede çözüm yok

    @transaction.atomic
    def generate_and_save(self):
        """Backtracking ile programı oluşturur ve veritabanına kaydeder."""
        self.load_data()
        print("Backtracking ile ders programı oluşturuluyor...")
        
        # Program durumunu temizle
        self.program_state.clear()
        self.hoca_programi.clear()
        self.derslik_programi.clear()
        self.sinif_programi.clear()
        self.yerlesmeyen_dersler_rapor.clear()

        # Algoritmayı başlat
        success = self._solve(0)

        if success:
            print("Çözüm bulundu! Veritabanına kaydediliyor...")
            # Önce eski programı temizle
            DersProgramiSlotu.objects.all().delete()
            
            # Bulunan çözümü DersProgramiSlotu modeline kaydet
            for ders_id, placement in self.program_state.items():
                gun, saat_tuple, derslik_id, hoca_id = placement
                start_time, end_time = saat_tuple
                ders = Ders.objects.get(id=ders_id)
                hoca = OgretimUyesi.objects.get(id=hoca_id)
                derslik = Derslik.objects.get(id=derslik_id)
                
                # Dönem bilgisinden semester string'ini belirle
                semester_str = "Bilinmiyor"
                if ders.donem:
                    semester_str = "Güz" if ders.donem % 2 != 0 else "Bahar"
                
                DersProgramiSlotu.objects.create(
                    ders=ders,
                    ogretim_uyesi=hoca,
                    derslik=derslik,
                    gun=gun,
                    baslangic_saati=start_time,
                    bitis_saati=end_time,
                    bolum=ders.bolum,
                    sinif=ders.sinif,
                    academic_year="DEFAULT_YEAR", # TODO: Bu değer dinamik olmalı
                    semester=semester_str, # Semester değeri eklendi
                    is_manually_adjusted=False # Manuel ayarlanmadığı için False
                )
            print("Ders programı başarıyla veritabanına kaydedildi.")
            return True
        else:
            print("Uyarı: Tüm dersler için geçerli bir program bulunamadı!")
            if self.yerlesmeyen_dersler_rapor:
                 print("Yerleşemeyen (veya hocası olmayan) Dersler:")
                 for d in self.yerlesmeyen_dersler_rapor:
                      print(f"- {d.ders_kodu} ({d.ders_adi})")
            return False

# Kullanım örneği (management command içinde çağrılacak)
# scheduler = BacktrackingScheduler()
# success = scheduler.generate_and_save() 