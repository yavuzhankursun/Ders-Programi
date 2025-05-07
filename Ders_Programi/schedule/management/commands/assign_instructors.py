import logging
from django.core.management.base import BaseCommand
from django.db import transaction, models
from schedule.models import Ders, OgretimUyesi
from itertools import cycle

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Belirtilen kurallara göre ve kalan derslere öğretim üyelerini atar.'

    # Atanacak öğretim üyelerinin tam adları
    HOCA_VILDAN = "Dr. Öğr. Üyesi Vildan YAZICI"
    HOCA_CANDIDE = "Arş. Gör. Candide ÖZTÜRK"
    HOCA_ERAY = "Arş. Gör. Eray DURSUN"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Öğretim üyesi atama işlemi başlıyor...'))

        try:
            # 1. Özel Öğretim Üyelerini Bul
            # ===============================
            hoca_vildan = OgretimUyesi.objects.filter(ad_soyad=self.HOCA_VILDAN).first()
            hoca_candide = OgretimUyesi.objects.filter(ad_soyad=self.HOCA_CANDIDE).first()
            hoca_eray = OgretimUyesi.objects.filter(ad_soyad=self.HOCA_ERAY).first()

            ozel_hocalar_pks = []
            if hoca_vildan:
                self.stdout.write(self.style.SUCCESS(f'{self.HOCA_VILDAN} bulundu.'))
                ozel_hocalar_pks.append(hoca_vildan.pk)
            else:
                self.stderr.write(self.style.WARNING(f'{self.HOCA_VILDAN} bulunamadı.'))

            if hoca_candide:
                self.stdout.write(self.style.SUCCESS(f'{self.HOCA_CANDIDE} bulundu.'))
                ozel_hocalar_pks.append(hoca_candide.pk)
            else:
                self.stderr.write(self.style.WARNING(f'{self.HOCA_CANDIDE} bulunamadı.'))

            if hoca_eray:
                self.stdout.write(self.style.SUCCESS(f'{self.HOCA_ERAY} bulundu.'))
                ozel_hocalar_pks.append(hoca_eray.pk)
            else:
                 self.stderr.write(self.style.WARNING(f'{self.HOCA_ERAY} bulunamadı.'))


            # 2. Özel Atamaları Yap (MAT ve LAB dersleri)
            # ============================================
            mat_dersleri_atama_sayisi = 0
            lab_dersleri_atama_sayisi_candide = 0
            lab_dersleri_atama_sayisi_eray = 0

            # Ders koduna göre atama (MAT dersleri)
            if hoca_vildan:
                mat_dersleri = Ders.objects.filter(ders_kodu__startswith='MAT')
                self.stdout.write(f'Ders kodu "MAT" ile başlayan {mat_dersleri.count()} ders bulundu.')
                with transaction.atomic():
                    for ders in mat_dersleri:
                        if not ders.ogretim_uyeleri.filter(pk=hoca_vildan.pk).exists():
                            ders.ogretim_uyeleri.add(hoca_vildan)
                            mat_dersleri_atama_sayisi += 1
                            logger.info(f'{hoca_vildan.ad_soyad} -> {ders.ders_kodu} ({ders.ders_adi}) dersine atandı.')
                        # else: logger.info(f'{hoca_vildan.ad_soyad} zaten {ders.ders_kodu} ({ders.ders_adi}) dersine atanmış.')
                if mat_dersleri_atama_sayisi > 0:
                    self.stdout.write(self.style.SUCCESS(f'{mat_dersleri_atama_sayisi} MAT dersine {self.HOCA_VILDAN} atandı.'))

            # Ders adına göre atama (LAB dersleri)
            lab_dersleri = Ders.objects.filter(ders_adi__icontains='lab')
            self.stdout.write(f'Ders adında "lab" geçen {lab_dersleri.count()} ders bulundu.')

            if hoca_candide or hoca_eray:
                 with transaction.atomic():
                    for ders in lab_dersleri:
                        if hoca_candide:
                            if not ders.ogretim_uyeleri.filter(pk=hoca_candide.pk).exists():
                                ders.ogretim_uyeleri.add(hoca_candide)
                                lab_dersleri_atama_sayisi_candide += 1
                                logger.info(f'{hoca_candide.ad_soyad} -> {ders.ders_kodu} ({ders.ders_adi}) dersine atandı.')
                            # else: logger.info(f'{hoca_candide.ad_soyad} zaten {ders.ders_kodu} ({ders.ders_adi}) dersine atanmış.')
                        if hoca_eray:
                            if not ders.ogretim_uyeleri.filter(pk=hoca_eray.pk).exists():
                                ders.ogretim_uyeleri.add(hoca_eray)
                                lab_dersleri_atama_sayisi_eray += 1
                                logger.info(f'{hoca_eray.ad_soyad} -> {ders.ders_kodu} ({ders.ders_adi}) dersine atandı.')
                            # else: logger.info(f'{hoca_eray.ad_soyad} zaten {ders.ders_kodu} ({ders.ders_adi}) dersine atanmış.')

            if lab_dersleri_atama_sayisi_candide > 0:
                self.stdout.write(self.style.SUCCESS(f'{lab_dersleri_atama_sayisi_candide} LAB dersine {self.HOCA_CANDIDE} atandı.'))
            if lab_dersleri_atama_sayisi_eray > 0:
                self.stdout.write(self.style.SUCCESS(f'{lab_dersleri_atama_sayisi_eray} LAB dersine {self.HOCA_ERAY} atandı.'))


            # 3. Kalan Öğretim Üyelerini ve Atanmamış Dersleri Bul
            # =====================================================
            diger_ogretim_uyeleri = OgretimUyesi.objects.exclude(pk__in=ozel_hocalar_pks)
            atanmamis_dersler = Ders.objects.annotate(
                hoca_sayisi=models.Count('ogretim_uyeleri')
            ).filter(hoca_sayisi=0)

            self.stdout.write(f'Atama yapılacak {diger_ogretim_uyeleri.count()} diğer öğretim üyesi bulundu.')
            self.stdout.write(f'Henüz öğretim üyesi atanmamış {atanmamis_dersler.count()} ders bulundu.')

            # 4. Kalan Derslere Diğer Öğretim Üyelerini Sırayla Ata
            # =======================================================
            kalan_atama_sayisi = 0
            if diger_ogretim_uyeleri.exists() and atanmamis_dersler.exists():
                hoca_dongusu = cycle(diger_ogretim_uyeleri) # Hocaları sırayla döndür

                with transaction.atomic():
                    for ders in atanmamis_dersler:
                        atanacak_hoca = next(hoca_dongusu)
                        ders.ogretim_uyeleri.add(atanacak_hoca)
                        kalan_atama_sayisi += 1
                        logger.info(f'[Kalan] {atanacak_hoca.ad_soyad} -> {ders.ders_kodu} ({ders.ders_adi}) dersine atandı.')

                self.stdout.write(self.style.SUCCESS(f'{kalan_atama_sayisi} kalan derse diğer öğretim üyeleri sırayla atandı.'))
            elif not diger_ogretim_uyeleri.exists():
                 self.stdout.write(self.style.WARNING('Atanacak başka öğretim üyesi bulunamadı.'))
            elif not atanmamis_dersler.exists():
                 self.stdout.write(self.style.WARNING('Öğretim üyesi atanmamış başka ders bulunamadı.'))


            self.stdout.write(self.style.SUCCESS('Öğretim üyesi atama işlemi tamamlandı.'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Atama sırasında bir hata oluştu: {e}'))
            logger.error(f"Atama hatası: {e}", exc_info=True) 