from django import template
from django.urls import translate_url


register = template.Library()


@register.simple_tag(takes_context=True)
def switch_i18n_url(context, language_code):
    request = context.get("request")
    current_url = request.get_full_path() if request else "/"
    translated = translate_url(current_url, language_code)
    return translated or f"/{language_code}/"
