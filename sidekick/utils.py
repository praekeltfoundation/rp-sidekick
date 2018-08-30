import datetime


def get_today():
    return datetime.date.today()


def get_current_week_number():
    return int(get_today().strftime("%W"))
