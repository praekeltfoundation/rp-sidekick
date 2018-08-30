from django.utils import timezone


def get_today():
    return timezone.now().date()


def get_current_week_number():
    return int(get_today().strftime("%W"))
