from django import forms
from .models import GlobalKisiti # Bu sefer GlobalKisiti için

# Admin panelinde kullanılacak günler için seçenekler
GUN_CHOICES_FORM = [
    ('Pazartesi', 'Pazartesi'),
    ('Salı', 'Salı'),
    ('Çarşamba', 'Çarşamba'),
    ('Perşembe', 'Perşembe'),
    ('Cuma', 'Cuma'),
]

class GlobalKisitiAdminForm(forms.ModelForm):
    gunler = forms.MultipleChoiceField(
        choices=GUN_CHOICES_FORM,
        widget=forms.CheckboxSelectMultiple,
        label="Günler",
        help_text="Genel kısıtlamanın geçerli olacağı günleri seçin.",
        required=True
    )

    class Meta:
        model = GlobalKisiti
        # Açıklama, başlangıç/bitiş saati ve çoklu günleri göster
        fields = ['aciklama', 'baslangic_saati', 'bitis_saati', 'gunler'] 