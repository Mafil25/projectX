import re
from functools import lru_cache

from django import template
import pyphen


register = template.Library()
_dictionary = pyphen.Pyphen(lang='ru_RU')
_words = re.compile(r'[А-Яа-яЁё]+')


@lru_cache(maxsize=2048)
def _hyphenate_word(word):
    return _dictionary.inserted(word, hyphen='\u00ad')


@register.filter
def hyphenate_ru(value):
    """Soft hyphens are invisible until the browser wraps a Russian word."""
    return _words.sub(lambda match: _hyphenate_word(match.group()), str(value))
