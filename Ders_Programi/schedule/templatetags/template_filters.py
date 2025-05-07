from django import template
register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Allows accessing dictionary items with a variable key in templates."""
    # Filtreye gelen 'dictionary' gerçekten sözlük benzeri mi diye kontrol et
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, '') # Anahtar yoksa veya obje sözlük değilse boş string dön
    return '' # Eğer obje sözlük değilse doğrudan boş string dön