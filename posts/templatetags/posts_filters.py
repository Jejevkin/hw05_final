import pymorphy2
from django import template

register = template.Library()


@register.filter
def word_form(word, number):
    morph = pymorphy2.MorphAnalyzer()
    default_word = morph.parse(word)[0]
    changed_word = default_word.make_agree_with_number(number).word
    return changed_word
