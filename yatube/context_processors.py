import datetime as dt

from django.conf import settings


def year(request):
    """
    Добавляет переменную с текущим годом.
    """
    return {'year': dt.datetime.now().year}


def cache_timeout(request):
    """
    Устанавливает продолжительность кеширования.
    """
    return {'cache_timeout': settings.CACHE_TIMEOUT}
