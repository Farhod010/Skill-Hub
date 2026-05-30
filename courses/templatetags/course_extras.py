from decimal import Decimal

from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.filter
def money(value):
    try:
        amount = Decimal(value)
    except Exception:
        return value
    return f"${amount:,.2f}"


@register.filter
def minutes_to_duration(value):
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return value
    hours, remainder = divmod(minutes, 60)
    if hours:
        return _("%(hours)sh %(minutes)sm") % {"hours": hours, "minutes": remainder}
    return _("%(minutes)sm") % {"minutes": remainder}


@register.filter
def translated_title(obj):
    if hasattr(obj, "get_translated_title"):
        return obj.get_translated_title()
    return getattr(obj, "title", obj)


@register.filter
def translated_description(obj):
    if hasattr(obj, "get_translated_description"):
        return obj.get_translated_description()
    return getattr(obj, "description", obj)


@register.filter
def translated_short_description(obj):
    if hasattr(obj, "get_translated_short_description"):
        return obj.get_translated_short_description()
    return getattr(obj, "short_description", obj)


@register.filter
def translated_prompt(obj):
    if hasattr(obj, "get_translated_prompt"):
        return obj.get_translated_prompt()
    return getattr(obj, "prompt", obj)


@register.filter
def translated_text(obj):
    if hasattr(obj, "get_translated_text"):
        return obj.get_translated_text()
    return getattr(obj, "text", obj)


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    request = context["request"]
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()
