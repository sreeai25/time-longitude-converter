def dms_to_decimal(deg, minutes, seconds, sign=1):
    decimal = abs(deg) + abs(minutes)/60 + abs(seconds)/3600
    return decimal if sign >= 0 else -decimal

def decimal_to_dms(value):
    sign = 1 if value >= 0 else -1
    a = abs(value)
    deg = int(a)
    rem = (a - deg) * 60
    minutes = int(rem)
    seconds = (rem - minutes) * 60
    return sign, deg, minutes, seconds

def tz_hours_to_hms(hours):
    sign = 1 if hours >= 0 else -1
    a = abs(hours)
    h = int(a)
    rem = (a - h) * 60
    m = int(rem)
    s = (rem - m) * 60
    return sign, h, m, s

def hms_to_decimal_hours(h, m, s, sign=1):
    total = abs(h) + abs(m)/60 + abs(s)/3600
    return total if sign >= 0 else -total

def longitude_from_timezone_hours(hours):
    return hours * 15
