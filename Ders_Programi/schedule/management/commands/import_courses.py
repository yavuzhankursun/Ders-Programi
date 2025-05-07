import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from schedule.models import Ders, Bolum

class Command(BaseCommand):
    help = 'Belirtilen CSV dosyasından dersleri veritabanına aktarır.'

    def add_arguments(self, parser):
        # CSV dosya yolunu komut satırından almak için argüman ekleyelim
        parser.add_argument('--file', type=str, help='İçe aktarılacak CSV dosyasının yolu', default='BLM_PLAN.csv')
        parser.add_argument('--bolum_kodu', type=str, help='Derslerin ait olacağı bölüm kodu', default='BLM')
        parser.add_argument('--default_kontenjan', type=int, help='Varsayılan ders kontenjanı', default=50)

    def handle(self, *args, **options):
        file_path = options['file']
        bolum_kodu = options['bolum_kodu']
        default_kontenjan = options['default_kontenjan']

        self.stdout.write(f'{file_path} dosyasından {bolum_kodu} bölümü için dersler içe aktarılıyor...')

        try:
            bolum = Bolum.objects.get(bolum_kodu=bolum_kodu)
        except Bolum.DoesNotExist:
            raise CommandError(f'Hata: "{bolum_kodu}" kodlu bölüm bulunamadı. Lütfen önce bölümü oluşturun.')

        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as csvfile: # UTF-8 with BOM için -sig
                reader = csv.DictReader(csvfile)
                
                created_count = 0
                updated_count = 0
                skipped_count = 0
                
                for row in reader:
                    try:
                        # Gerekli alanların varlığını ve geçerliliğini kontrol et
                        dönem_str = row.get('Dönem')
                        ders_kodu = row.get('Ders Kodu')
                        ders_adi = row.get('Ders Adi')
                        teorik_str = row.get('Teorik', '0')
                        uygulama_str = row.get('Uygulama', '0')
                        lab_str = row.get('Laboratuar', '0')

                        # Satırın geçerli bir ders satırı olup olmadığını kontrol et (ilk sütun sayısal mı?)
                        if not dönem_str or not dönem_str.isdigit() or not ders_kodu or not ders_adi:
                             # self.stdout.write(f'Atlanıyor (geçersiz satır): {row}')
                            skipped_count += 1
                            continue 
                        
                        sinif = int(dönem_str)
                        teorik = int(teorik_str) if teorik_str.isdigit() else 0
                        uygulama = int(uygulama_str) if uygulama_str.isdigit() else 0
                        lab = int(lab_str) if lab_str.isdigit() else 0
                        
                        haftalik_saat = teorik + uygulama + lab
                        if haftalik_saat == 0: # Haftalık saati olmayan dersleri atla (örn. Staj)
                            self.stdout.write(f'Atlanıyor (haftalık saat 0): {ders_kodu} - {ders_adi}')
                            skipped_count += 1
                            continue
                            
                        # Ders tipini belirle (Lab saati varsa LAB, yoksa TEORIK)
                        ders_tipi = 'LAB' if lab > 0 else 'TEORIK'
                        
                        # Veritabanına ekle veya güncelle
                        obj, created = Ders.objects.update_or_create(
                            ders_kodu=ders_kodu,
                            defaults={
                                'ders_adi': ders_adi,
                                'bolum': bolum,
                                'sinif': sinif,
                                'haftalik_saat': haftalik_saat,
                                'tip': ders_tipi,
                                'kontenjan': default_kontenjan, # CSV'de yok, varsayılan kullanılıyor
                                # Öğretim üyesi bilgisi CSV'de yok, manuel atanmalı
                                # Zorunlu saat bilgisi CSV'de yok
                            }
                        )
                        
                        if created:
                            created_count += 1
                            # self.stdout.write(f'Oluşturuldu: {obj}')
                        else:
                            updated_count += 1
                            # self.stdout.write(f'Güncellendi: {obj}')

                    except ValueError as e:
                        self.stdout.write(self.style.WARNING(f'Satır işlenirken hata (ValueError): {row} - Hata: {e}'))
                        skipped_count += 1
                    except IntegrityError as e:
                        self.stdout.write(self.style.WARNING(f'Satır işlenirken hata (IntegrityError): {row} - Hata: {e}'))
                        skipped_count += 1
                    except Exception as e:
                         self.stdout.write(self.style.ERROR(f'Satır işlenirken beklenmedik hata: {row} - Hata: {e}'))
                         skipped_count += 1

        except FileNotFoundError:
            raise CommandError(f'Hata: Belirtilen dosya bulunamadı: {file_path}')
        except Exception as e:
             raise CommandError(f'CSV dosyası işlenirken genel bir hata oluştu: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'İçe aktarma tamamlandı. Oluşturulan: {created_count}, Güncellenen: {updated_count}, Atlanan: {skipped_count}'
        )) 