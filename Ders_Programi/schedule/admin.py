from django.contrib import admin
from django.urls import path, reverse # reverse import edelim
from django.shortcuts import redirect # redirect import edelim
from django.utils.html import format_html # Buton için HTML formatlama
from .models import (
    Bolum, OgretimUyesi, Ogrenci, Derslik, Ders, 
    OgretimUyesiKisiti, DersProgramiSlotu, GlobalKisiti
)
from .views import import_courses_view # View'ı import edelim (gerçi doğrudan URL kullanacağız)
from .forms import GlobalKisitiAdminForm # Global formunu import et

# Register your models here.

@admin.register(Bolum)
class BolumAdmin(admin.ModelAdmin):
    list_display = ('bolum_kodu', 'bolum_adi')
    search_fields = ('bolum_kodu', 'bolum_adi')

# --- Inline Admin Tanımı ---
class OgretimUyesiKisitiInline(admin.TabularInline): # TabularInline daha kompakt görünür
    model = OgretimUyesiKisiti
    extra = 1 # Varsayılan olarak 1 boş satır gösterir
    # fields = ['gun', 'baslangic_saati', 'bitis_saati'] # Gösterilecek alanlar
    # verbose_name = "Kısıtlama"
    # verbose_name_plural = "Öğretim Üyesi Kısıtları"

# --- OgretimUyesi Admin Güncellemesi ---
@admin.register(OgretimUyesi)
class OgretimUyesiAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'user') 
    search_fields = ('ad_soyad', 'user__username')
    inlines = [OgretimUyesiKisitiInline] # Kısıtlamaları inline olarak ekle

@admin.register(Ogrenci)
class OgrenciAdmin(admin.ModelAdmin):
    list_display = ('ogrenci_no', 'ad_soyad', 'bolum', 'sinif', 'user')
    search_fields = ('ogrenci_no', 'ad_soyad', 'bolum__bolum_kodu')
    list_filter = ('bolum', 'sinif')

@admin.register(Derslik)
class DerslikAdmin(admin.ModelAdmin):
    list_display = ('derslik_adi', 'kapasite', 'statu')
    list_filter = ('statu',)
    search_fields = ('derslik_adi',)

@admin.register(Ders)
class DersAdmin(admin.ModelAdmin):
    list_display = ('ders_kodu', 'ders_adi', 'bolum', 'sinif', 'donem', 'haftalik_saat', 'tip', 'is_zorunlu', 'kredi', 'akts', 'kontenjan')
    search_fields = ('ders_kodu', 'ders_adi', 'bolum__bolum_kodu', 'sinif', 'donem')
    list_filter = ('bolum', 'sinif', 'donem', 'tip', 'is_zorunlu')
    actions = ['delete_selected']
    ordering = ('bolum', 'sinif', 'donem', 'ders_kodu')
    
    # Admin sayfasına URL eklemek için get_urls metodunu override et
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-courses/', 
                self.admin_site.admin_view(import_courses_view), # View fonksiyonunu buraya bağla
                name='schedule_ders_import' # Benzersiz bir isim verelim
            )
        ]
        return custom_urls + urls

    # Listeleme sayfasına buton eklemek için changelist_view'i override et
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        # Butonun URL'sini oluştur
        import_url = reverse('admin:schedule_ders_import')
        extra_context['show_import_button'] = True
        extra_context['import_url'] = import_url
        return super().changelist_view(request, extra_context=extra_context)

    # changelist template'ini override ederek butonu göstermemiz gerekiyor
    # Bunun yerine, admin template'ini ('admin/change_list.html') override edip
    # {% if show_import_button %} bloğunu eklemek daha temiz olabilir.
    # Şimdilik Python tarafında context'i hazırladık.
    # Template ('admin/schedule/ders/change_list.html') override edilip şu eklenebilir:
    # {% extends "admin/change_list.html" %}
    # {% load i18n %}
    # {% block object-tools-items %}
    #     <li>
    #         {% if show_import_button %}
    #             <a href="{{ import_url }}" class="addlink">
    #                 {% trans 'Dersleri İçe Aktar' %}
    #             </a>
    #         {% endif %}
    #     </li>
    #     {{ block.super }}
    # {% endblock %}

@admin.register(DersProgramiSlotu)
class DersProgramiSlotuAdmin(admin.ModelAdmin):
    list_display = ('gun', 'baslangic_saati', 'bitis_saati', 'ders', 'ogretim_uyesi', 'derslik', 'bolum', 'sinif', 'semester')
    list_filter = ('gun', 'bolum', 'sinif', 'ogretim_uyesi', 'derslik', 'semester')
    search_fields = ('ders__ders_kodu', 'ders__ders_adi', 'ogretim_uyesi__ad_soyad', 'derslik__derslik_adi')
    
    # Haftalık tablo görünümüne link eklemek için
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        view_schedule_url = reverse('schedule:view_schedule')
        extra_context['show_view_schedule_button'] = True
        extra_context['view_schedule_url'] = view_schedule_url
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(GlobalKisiti)
class GlobalKisitiAdmin(admin.ModelAdmin):
    form = GlobalKisitiAdminForm # Özel formu kullan
    list_display = ('aciklama', 'gun', 'baslangic_saati', 'bitis_saati')
    list_filter = ('gun',)
    search_fields = ('aciklama', 'gun')

    # Çoklu gün seçimi için save_model override
    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            # Düzenleme modu (şimdilik gün değiştirilemez, sadece diğer alanlar)
            obj.aciklama = form.cleaned_data['aciklama']
            obj.baslangic_saati = form.cleaned_data['baslangic_saati']
            obj.bitis_saati = form.cleaned_data['bitis_saati']
            super().save_model(request, obj, form, change)
            return

        # Yeni kayıt ekleniyor
        aciklama = form.cleaned_data['aciklama']
        baslangic_saati = form.cleaned_data['baslangic_saati']
        bitis_saati = form.cleaned_data['bitis_saati']
        secilen_gunler = form.cleaned_data['gunler']

        kisi_sayisi = 0
        for gun in secilen_gunler:
            # Aynı gün ve başlangıç saatinde zaten genel kısıt var mı?
            # unique_together bunu zaten engeller ama yine de kontrol edebiliriz.
            try:
                kisit = GlobalKisiti(
                    aciklama=aciklama,
                    gun=gun,
                    baslangic_saati=baslangic_saati,
                    bitis_saati=bitis_saati
                )
                kisit.save()
                kisi_sayisi += 1
            except Exception as e: # unique_together hatasını yakala
                from django.contrib import messages
                messages.warning(request, f'{gun} {baslangic_saati} için zaten bir genel kısıtlama mevcut. Atlandı.')
                
        if kisi_sayisi > 0:
            from django.contrib import messages
            messages.success(request, f'{kisi_sayisi} gün için genel kısıtlama başarıyla eklendi.')

# Eski kayıtları kaldır (artık decorator kullanıyoruz)
# admin.site.register(Bolum)
# admin.site.register(OgretimUyesi)
# admin.site.register(Ogrenci)
# admin.site.register(Derslik)
# admin.site.register(Ders)
# admin.site.register(OgretimUyesiKisiti)
# admin.site.register(DersProgramiSlotu)
