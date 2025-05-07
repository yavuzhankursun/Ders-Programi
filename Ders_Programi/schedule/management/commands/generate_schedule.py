from django.core.management.base import BaseCommand
from schedule.scheduler import BacktrackingScheduler # Scheduler sınıfımızı import ediyoruz
import time

class Command(BaseCommand):
    help = 'Otomatik olarak ders programını oluşturur ve veritabanına kaydeder.'

    def handle(self, *args, **options):
        self.stdout.write("Ders programı oluşturma işlemi başlatılıyor...")
        start_time = time.time()
        
        scheduler = BacktrackingScheduler()
        success = scheduler.generate_and_save()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'Ders programı başarıyla oluşturuldu ve kaydedildi! Süre: {duration:.2f} saniye'))
        else:
            self.stdout.write(self.style.ERROR('Ders programı oluşturulamadı veya tamamlanamadı. Detaylar için loglara bakın. Süre: {duration:.2f} saniye')) 