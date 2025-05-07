from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Bolum(models.Model):
    bolum_kodu = models.CharField(max_length=10, unique=True, verbose_name="Bölüm Kodu")
    bolum_adi = models.CharField(max_length=100, verbose_name="Bölüm Adı")

    def __str__(self):
        return f"{self.bolum_kodu} - {self.bolum_adi}"

class OgretimUyesi(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Kullanıcı Hesabı")
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    # İleride unvan vb. eklenebilir

    def __str__(self):
        return self.ad_soyad

class Ogrenci(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Kullanıcı Hesabı") # Öğrenci girişi için
    ogrenci_no = models.CharField(max_length=20, unique=True, verbose_name="Öğrenci Numarası")
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    bolum = models.ForeignKey(Bolum, on_delete=models.CASCADE, verbose_name="Bölümü")
    sinif = models.IntegerField(verbose_name="Sınıf")

    def __str__(self):
        return f"{self.ogrenci_no} - {self.ad_soyad}"

class Derslik(models.Model):
    STATU_CHOICES = [
        ('NORMAL', 'Normal'),
        ('LAB', 'Laboratuvar'),
    ]
    derslik_adi = models.CharField(max_length=50, unique=True, verbose_name="Derslik Adı")
    kapasite = models.PositiveIntegerField(verbose_name="Kapasite")
    statu = models.CharField(max_length=10, choices=STATU_CHOICES, default='NORMAL', verbose_name="Statü")

    def __str__(self):
        return f"{self.derslik_adi} (Kapasite: {self.kapasite}, Statü: {self.statu})"

class Ders(models.Model):
    TIP_CHOICES = [
        ('TEORIK', 'Teorik'),
        ('LAB', 'Laboratuvar'),
        ('UYGULAMA', 'Uygulama'),
    ]
    ders_kodu = models.CharField(max_length=10, verbose_name="Ders Kodu")
    ders_adi = models.CharField(max_length=100, verbose_name="Ders Adı")
    bolum = models.ForeignKey(Bolum, on_delete=models.CASCADE, related_name='dersler', verbose_name="Bölümü")
    sinif = models.IntegerField(verbose_name="Sınıf") # Dersin hangi sınıf seviyesinde olduğu
    ogretim_uyeleri = models.ManyToManyField(OgretimUyesi, related_name='verdigi_dersler', blank=True, verbose_name="Öğretim Üyeleri")
    haftalik_saat = models.PositiveIntegerField(verbose_name="Haftalık Ders Saati")
    tip = models.CharField(max_length=10, choices=TIP_CHOICES, default='TEORIK', verbose_name="Ders Tipi (Yapısal)")
    kontenjan = models.PositiveIntegerField(verbose_name="Kontenjan", default=50)
    zorunlu_saat_gun = models.CharField(max_length=10, blank=True, null=True, verbose_name="Zorunlu Gün") # Örn: 'Pazartesi'
    zorunlu_baslangic_saati = models.TimeField(blank=True, null=True, verbose_name="Zorunlu Başlangıç Saati") # Örn: 09:00
    
    # Yeni eklenen alanlar
    is_zorunlu = models.BooleanField(default=True, verbose_name="Zorunlu Ders mi?")
    kredi = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, verbose_name="Kredi")
    akts = models.IntegerField(null=True, blank=True, verbose_name="AKTS")
    donem = models.IntegerField(null=True, blank=True, verbose_name="Dönem (1-8)") # Yeni dönem alanı
    is_shared = models.BooleanField(default=False, verbose_name="Ortak Ders mi?") # YENİ EKLENEN ALAN
    is_online = models.BooleanField(default=False, verbose_name="Online Ders mi?") # YENİ EKLENEN ALAN

    # Ortak dersleri belirtmek için ek alanlar düşünülebilir veya kodlama ile yönetilebilir.

    def __str__(self):
        return f"{self.ders_kodu} - {self.ders_adi} ({self.bolum.bolum_kodu} - Sınıf {self.sinif})"

class OgretimUyesiKisiti(models.Model):
    GUN_CHOICES = [
        ('Pazartesi', 'Pazartesi'),
        ('Salı', 'Salı'),
        ('Çarşamba', 'Çarşamba'),
        ('Perşembe', 'Perşembe'),
        ('Cuma', 'Cuma'),
    ]
    ogretim_uyesi = models.ForeignKey(OgretimUyesi, on_delete=models.CASCADE, related_name='kisitlari', verbose_name="Öğretim Üyesi")
    gun = models.CharField(max_length=10, choices=GUN_CHOICES, verbose_name="Gün")
    baslangic_saati = models.TimeField(verbose_name="Uygun Olmayan Başlangıç Saati")
    bitis_saati = models.TimeField(verbose_name="Uygun Olmayan Bitiş Saati")

    class Meta:
        verbose_name_plural = "Öğretim Üyesi Kısıtları"
        unique_together = ('ogretim_uyesi', 'gun', 'baslangic_saati') # Aynı hoca için aynı gün aynı saatte kısıt olmasın

    def __str__(self):
        return f"{self.ogretim_uyesi} - {self.gun} {self.baslangic_saati}-{self.bitis_saati} arası uygun değil"

# Yeni Global Kısıtlama Modeli
class GlobalKisiti(models.Model):
    GUN_CHOICES = [
        ('Pazartesi', 'Pazartesi'),
        ('Salı', 'Salı'),
        ('Çarşamba', 'Çarşamba'),
        ('Perşembe', 'Perşembe'),
        ('Cuma', 'Cuma'),
    ]
    aciklama = models.CharField(max_length=200, blank=True, help_text="Örn: Öğle Arası, Fakülte Toplantısı")
    gun = models.CharField(max_length=10, choices=GUN_CHOICES, verbose_name="Gün")
    baslangic_saati = models.TimeField(verbose_name="Uygun Olmayan Başlangıç Saati")
    bitis_saati = models.TimeField(verbose_name="Uygun Olmayan Bitiş Saati")

    class Meta:
        verbose_name = "Genel Kısıtlama"
        verbose_name_plural = "Genel Kısıtlamalar"
        unique_together = ('gun', 'baslangic_saati') # Aynı gün aynı saatte tek genel kısıt olsun

    def __str__(self):
        return f"{self.gun} {self.baslangic_saati}-{self.bitis_saati} ({self.aciklama}) - TÜMÜ"

class DersProgramiSlotu(models.Model):
    GUN_CHOICES = [
        ('Pazartesi', 'Pazartesi'),
        ('Salı', 'Salı'),
        ('Çarşamba', 'Çarşamba'),
        ('Perşembe', 'Perşembe'),
        ('Cuma', 'Cuma'),
    ]
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    ogretim_uyesi = models.ForeignKey(OgretimUyesi, on_delete=models.CASCADE, verbose_name="Öğretim Üyesi")
    derslik = models.ForeignKey(Derslik, on_delete=models.CASCADE, verbose_name="Derslik")
    gun = models.CharField(max_length=10, choices=GUN_CHOICES, verbose_name="Gün")
    baslangic_saati = models.TimeField(verbose_name="Başlangıç Saati")
    bitis_saati = models.TimeField(verbose_name="Bitiş Saati")
    # Programın hangi bölüme ve sınıfa ait olduğunu belirtmek için:
    bolum = models.ForeignKey(Bolum, on_delete=models.CASCADE, verbose_name="Bölüm")
    sinif = models.IntegerField(verbose_name="Sınıf")
    academic_year = models.CharField(max_length=20, verbose_name="Akademik Yıl") # max_length artırıldı
    semester = models.CharField(max_length=20, verbose_name="Dönem (Güz/Bahar)") # max_length artırıldı
    is_manually_adjusted = models.BooleanField(default=False, verbose_name="Manuel Ayarlandı mı?") # YENİ EKLENEN ALAN

    class Meta:
        verbose_name_plural = "Ders Programı Slotları"
        # Çakışmaları önlemek için unique constraintler eklenebilir
        # Örneğin: Aynı anda aynı hocanın başka dersi olamaz, aynı anda aynı sınıfın başka dersi olamaz, aynı anda aynı derslik dolu olamaz
        unique_together = [
            ('ogretim_uyesi', 'gun', 'baslangic_saati'),
            ('derslik', 'gun', 'baslangic_saati'),
            ('bolum', 'sinif', 'gun', 'baslangic_saati'),
        ]

    def __str__(self):
        return f"{self.gun} {self.baslangic_saati}-{self.bitis_saati} | {self.ders.ders_kodu} ({self.ogretim_uyesi}) @ {self.derslik}"
