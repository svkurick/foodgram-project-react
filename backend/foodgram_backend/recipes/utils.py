from django.utils.text import slugify as django_slugify

alphabet = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ы': 'i', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}


def slugify(slug: str) -> str:
    """
    Транслитерация slug.
    """
    trans_slug = ''
    for symbol in slug.lower():
        trans_symbol = alphabet.get(symbol, symbol)
        trans_slug += trans_symbol
    return django_slugify(trans_slug)