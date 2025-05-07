# 📘 Ders Programı Yönetim Sistemi

Bu proje, eğitim kurumlarında haftalık ders programlarının **otomatik ve çakışmasız** şekilde oluşturulmasını sağlayan bir web tabanlı sistemdir. Amaç, manuel yapılan programlama sürecini otomatikleştirerek zaman kazancı ve hata azaltımı sağlamaktır.

---

## 🚀 Genel Özellikler

- Bölüm, derslik, öğretim üyesi ve ders tanımlamaları yapılabilir.
- Excel/CSV ile toplu veri içe aktarma ve dışa aktarma desteği.
- Backtracking algoritması ile çakışmasız ders programı üretimi.
- Program çıktılarının web arayüzü ve Excel formatında sunumu.
- Otomatik öğretim üyesi atama özelliği.

---

## ⚙️ Teknik Özellikler

- **Backend:** Python, Django
- **Veritabanı:** PostgreSQL / SQLite
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **Veri İşleme:** pandas, openpyxl
- **Yönetim Paneli:** Django Admin
- **Komutlar:** `import_courses`, `assign_all_instructors`, `generate_schedule`

---

## 🧠 Kullanılan Algoritma

### Ders Programı Oluşturma (Backtracking)

- Olası zaman–derslik kombinasyonları denenir.
- Öğretim üyesi ve derslik uygunluğu kontrol edilir.
- Çakışma durumlarında geri izleme (backtrack) yapılır.
- Tüm dersler uygun şekilde yerleşene kadar döngü devam eder.

> Bu yaklaşım, NP-hard kısıt tatmin problemleri için uygun bir yöntemdir.

---

## 🧪 Testler

- **Birim Testleri:** CRUD işlemleri ve komut çıktıları
- **Sistem Testleri:** Tam program oluşturma ve Excel dışa aktarma
- **Kullanıcı Testleri:** Admin paneli ile etkileşimli kullanım
- **Performans Testleri:** 200+ ders ile ≤5 saniye içinde program üretimi

---

## 📈 Gelecek Geliştirmeler

- Genetik algoritma veya kısıt programlama desteği
- AJAX destekli takvim görünümü
- Rol bazlı erişim ve kullanıcı ön yüzü
- API ile dış sistemlerle entegrasyon
- Mobil uyumlu arayüz veya bağımsız mobil uygulama

---

## 🛠️ Kurulum

```bash
# Ortamı kur
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate
pip install -r requirements.txt

# Veritabanını hazırla
python manage.py migrate

# Admin kullanıcı oluştur
python manage.py createsuperuser

# Sunucuyu başlat
python manage.py runserver
```

---

## 📎 Not

Bu proje, ders programı hazırlama sürecinin dijitalleştirilmesine yönelik örnek bir yazılım çözümüdür. Genişletilebilir mimarisi sayesinde farklı kurumsal ihtiyaçlara kolayca uyarlanabilir.
