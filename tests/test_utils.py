from utils import *

def test_dms_to_decimal():
    assert abs(dms_to_decimal(30, 0, 0, 1) - 30) < 1e-9

def test_decimal_to_dms_roundtrip():
    val = -73.9855
    sgn, d, m, s = decimal_to_dms(val)
    rec = (d + m/60 + s/3600) * (1 if sgn >= 0 else -1)
    assert abs(rec - val) < 1e-9

def test_tz_to_hms():
    s, h, m, s2 = tz_hours_to_hms(5.5)
    assert h == 5 and m == 30

def test_hms_to_hours():
    assert abs(hms_to_decimal_hours(5, 30, 0, 1) - 5.5) < 1e-9

def test_longitude_from_tz():
    assert longitude_from_timezone_hours(2) == 30
