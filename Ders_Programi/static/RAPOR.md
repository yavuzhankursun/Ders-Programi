# HAFTALIK DERS PROGRAMI OLUŞTURMA SİSTEMİ

## PROJE RAPORU

### 1. GİRİŞ

Bu rapor, Bilgisayar Mühendisliği ve Yazılım Mühendisliği bölümleri için otomatik haftalık ders programı oluşturan web tabanlı bir uygulamanın geliştirilme sürecini ve özelliklerini detaylı bir şekilde açıklamaktadır. Proje, mühendislik fakültesine ait bölümlerin ders programlarını belirli kısıtlar dahilinde otomatik olarak oluşturup Excel formatında dışa aktarabilmektedir.

### 2. PROJENİN AMACI

Projenin temel amacı, üniversitelerdeki ders programı oluşturma sürecini otomatikleştirmek ve optimize etmektir. Manuel olarak ders programı oluşturmak, çeşitli kısıtlar ve ihtiyaçlar nedeniyle karmaşık ve zaman alıcı bir süreçtir. Bu projede geliştirilen uygulama ile:

- Öğretim üyelerinin müsaitlik durumları
- Derslik kapasiteleri ve türleri
- Bölüm ders çakışmalarını önleme
- Ortak derslerin programlanması
- Online ve laboratuvar derslerinin özel gereksinimlerinin karşılanması

gibi kısıtlar dikkate alınarak en uygun ders programı otomatik olarak oluşturulabilmektedir.

### 3. KULLANILAN TEKNOLOJİLER

#### 3.1. Backend Teknolojileri
- **Python**: Temel programlama dili
- **Flask**: Web framework
- **SQLAlchemy**: ORM (Object-Relational Mapping) kütüphanesi
- **Flask-Migrate**: Veritabanı şema değişikliklerini yönetmek için
- **Pandas & XlsxWriter**: Excel veri işleme ve dosya oluşturma

#### 3.2. Frontend Teknolojileri
- **HTML5 / CSS3**: Kullanıcı arayüzü için temel teknolojiler
- **JavaScript**: İstemci tarafı işlemler için
- **Bootstrap**: Responsive tasarım framework'ü

#### 3.3. Veritabanı
- **SQLite**: Geliştirme ortamında
- **PostgreSQL**: Üretim ortamında (opsiyonel)

#### 3.4. Diğer Araçlar
- **Docker & Docker Compose**: Konteynerleştirme ve dağıtım
- **Git**: Versiyon kontrol sistemi

### 4. VERİTABANI TASARIMI

Uygulama, aşağıdaki ana veri modellerine sahiptir:

#### 4.1. Kullanıcılar (User)
- Genel kullanıcı bilgileri (id, ad, soyad, email, şifre)
- Kullanıcı türü (öğrenci, öğretim üyesi, yönetici)

#### 4.2. Öğretim Üyeleri (Faculty)
- Öğretim üyesi ile ilgili bilgiler (ünvan, müsaitlik durumu)
- User modeli ile ilişkilendirilmiş

#### 4.3. Öğrenciler (Student)
- Öğrenci bilgileri (öğrenci numarası, bölüm, sınıf)
- User modeli ile ilişkilendirilmiş

#### 4.4. Bölümler (Department)
- Bölüm bilgileri (id, ad, kod)

#### 4.5. Dersler (Course)
- Ders bilgileri (id, ad, kod, haftalık ders saati, zorunlu/seçmeli, yüz yüze/online, sabit zaman)
- Bölüm ve öğretim üyesi ile ilişkilendirilmiş

#### 4.6. Derslikler (Classroom)
- Derslik bilgileri (id, ad, kapasite, tür)

#### 4.7. Ders Programı (Schedule)
- Program bilgileri (ders, gün, başlangıç saati, bitiş saati, derslik)
- Akademik yıl ve dönem bilgisi

#### 4.8. Ortak Dersler (SharedCourse)
- İki veya daha fazla bölüm tarafından ortak verilen dersleri tanımlar
- Ders ve ortak bölüm ilişkileri

### 5. ALGORİTMANIN ÇALIŞMA PRENSİBİ

Ders programı oluşturma algoritması, aşağıdaki adımları takip eder:

#### 5.1. Veri Hazırlama
- Tüm bölümlerin derslerini, derslikleri ve öğretim üyelerini yükler
- BLM ve YZM bölümleri arasında ortak ders ilişkilerini tespit eder
- Sınıf programlarını ve öğretim üyesi müsaitliklerini başlatır

#### 5.2. Ders Sınıflandırma
1. **Sabit Zamanlı Dersler**: Belirli bir gün ve saatte işlenmesi gereken dersler (örn. İngilizce)
2. **Ortak Dersler**: Birden fazla bölüm tarafından alınan dersler
3. **Normal Dersler**: Diğer tüm dersler

#### 5.3. Ders Yerleştirme Sırası
1. Önce sabit zamanlı dersler yerleştirilir
2. Sonra ortak dersler yerleştirilir
3. Son olarak normal dersler yerleştirilir

#### 5.4. Uygun Zaman ve Derslik Bulma
Her ders için:
1. Dersin sabit zamanı var mı kontrol edilir
2. Öğretim üyesinin müsaitlik durumu kontrol edilir
3. Sınıf programında çakışma olup olmadığı kontrol edilir
4. Ortak dersler için diğer bölüm sınıfları ile çakışma kontrol edilir
5. Ders için uygun derslik bulunur (laboratuvar/normal ve kapasite kontrolü)
6. Online dersler için akşam saatleri tercih edilir

#### 5.5. Program Oluşturma
Uygun zaman ve derslik bulunduktan sonra:
1. Ders, programlara eklenir (derslik, öğretim üyesi ve sınıf programları)
2. Ortak dersler için diğer bölümlerin programları da güncellenir
3. Veritabanına kaydedilir

### 6. UYGULAMA ARAYÜZÜ VE İŞLEVLERİ

#### 6.1. Yönetim Paneli
- Genel istatistikler (bölüm, ders, öğretim üyesi ve derslik sayıları)
- Hızlı erişim linkleri

#### 6.2. Bölüm Yönetimi
- Bölüm ekleme, düzenleme ve silme
- Bölüm kodları (BLM, YZM) ve isimleri

#### 6.3. Derslik Yönetimi
- Derslik ekleme, düzenleme ve silme
- Derslik kapasitesi ve türü (NORMAL, LAB)

#### 6.4. Öğretim Üyesi Yönetimi
- Öğretim üyesi ekleme, düzenleme ve silme
- Müsaitlik durumu belirleme (gün ve saat bazında)

#### 6.5. Ders Yönetimi
- Ders ekleme, düzenleme ve silme
- Ders özelliklerini belirleme (zorunlu/seçmeli, online/yüz yüze)
- Sabit zamanlı dersler için zaman belirleme
- Ortak ders tanımlama

#### 6.6. Ders Programı Oluşturma
- Bölüm, akademik yıl ve dönem seçme
- Otomatik program oluşturma
- Hata raporlama

#### 6.7. Ders Programı Görüntüleme
- Bölüm ve sınıflara göre filtreleme
- Günlük, haftalık görünüm

#### 6.8. Excel'e Aktarma
- İstenilen şablonda Excel dosyası oluşturma
- Bölüm bazında sayfalar

### 7. KISITLAR VE ÖZELLİKLER

Uygulamada dikkate alınan temel kısıtlar şunlardır:

#### 7.1. Sınıf Çakışmalarını Önleme
- Aynı sınıfın aynı anda farklı dersleri olamaz

#### 7.2. Öğretim Üyesi Çakışmalarını Önleme
- Bir öğretim üyesi aynı anda birden fazla ders veremez
- Öğretim üyesinin müsait olmadığı zamanlarda ders ataması yapılmaz

#### 7.3. BLM ve YZM Bölümleri Arasındaki Kısıtlar
- Ortak öğrencisi olan derslerde çakışma olmamalı
- Ortak dersler (İngilizce, Türk Dili, Atatürk İlkeleri) aynı zamanda verilmeli

#### 7.4. Derslik Kısıtları
- Derslik kapasitesi öğrenci sayısına uygun olmalı
- Laboratuvar dersleri LAB tipi dersliklerde verilmeli

#### 7.5. Zaman Kısıtları
- Online dersler için 17:00-21:00 saatleri arası tercih edilmeli
- Zorunlu zaman kısıtlaması olan dersler için belirlenen zamana uyulmalı

### 8. EXCEL ÇIKTISI VE ŞABLON

Uygulama, ders programını aşağıdaki şablona uygun olarak Excel formatında dışa aktarabilmektedir:

- Her bölüm için ayrı çalışma sayfası
- Bölüm adı ve dönem bilgisini içeren başlık
- Sınıflara göre sütunlar (1., 2., 3. ve 4. sınıf)
- Gün ve saatlere göre satırlar
- Her ders için:
  - Ders kodu
  - Ders adı
  - Öğretim üyesi
  - Derslik bilgisi

### 9. KURULUM VE ÇALIŞTIRMA

#### 9.1. Manuel Kurulum
```bash
# Repoyu klonla
git clone https://github.com/kullaniciadiz/haftalik-ders-programi.git
cd haftalik-ders-programi

# Sanal ortam oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Gereksinimleri yükle
pip install -r requirements.txt

# Veritabanını başlat
flask init-db

# Uygulamayı çalıştır
flask run
```

#### 9.2. Docker ile Kurulum
```bash
# Repoyu klonla
git clone https://github.com/kullaniciadiz/haftalik-ders-programi.git
cd haftalik-ders-programi

# Docker Compose ile çalıştır
docker-compose up --build
```

### 10. KISITLAR VE GELECEK GELİŞTİRMELER

#### 10.1. Mevcut Kısıtlar
- Sistem şu anda sadece BLM ve YZM bölümleri için optimize edilmiştir
- Ders saatleri 1 saat olarak sabitlenmiştir (2 veya 3 saatlik bloklar halinde yapılamaz)
- Öğretim üyelerinin tercihleri (sabah/öğle/akşam) dikkate alınmamaktadır

#### 10.2. Gelecek Geliştirmeler
- Birden fazla fakültenin ders programını oluşturabilme
- Ders programında manuel değişiklik yapabilme
- Blok ders saatleri (ardışık 2-3 saat) planlayabilme
- Öğretim üyesi tercihlerini daha detaylı dikkate alma
- Çakışma önleme algoritmasını geliştirme

### 11. GITHUB BAĞLANTILARI

Proje ekip üyelerinin GitHub bağlantıları:

- [Üye 1 - Github](https://github.com/uye1)
- [Üye 2 - Github](https://github.com/uye2)
- [Üye 3 - Github](https://github.com/uye3)

### 12. SONUÇ

Bu proje, üniversite ders programı oluşturma sürecini otomatikleştirerek zaman ve emek tasarrufu sağlamaktadır. Belirlenen kısıtlar dahilinde BLM ve YZM bölümleri için uygun ders programlarını oluşturabilmekte ve istenen şablonda Excel formatında dışa aktarabilmektedir.

Sistem, kullanıcı dostu arayüzü, veritabanı entegrasyonu ve otomatik program oluşturma özellikleri ile etkili bir çözüm sunmaktadır. Gelecekteki geliştirmeler ile daha kapsamlı ve esnek bir yapıya kavuşturulabilir. 