# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

ETH_EPOCH = 1724221

ETH_MONTH_NAMES = [
    '',
    'Meskerem',  # 1
    'Tikimt',    # 2
    'Hidar',     # 3
    'Tahsas',    # 4
    'Tir',       # 5
    'Yekatit',   # 6
    'Megabit',   # 7
    'Miazia',    # 8
    'Ginbot',    # 9
    'Sene',      # 10
    'Hamle',     # 11
    'Nehase',    # 12
    'Pagume',    # 13
]

def gregorian_to_jdn(year, month, day):
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

def jdn_to_gregorian(jdn):
    l = jdn + 68569
    n = (4 * l) // 146097
    l = l - (146097 * n + 3) // 4
    i = (4000 * (l + 1)) // 1461001
    l = l - (1461 * i) // 4 + 31
    j = (80 * l) // 2447
    day = l - (2447 * j) // 80
    l = j // 11
    month = j + 2 - 12 * l
    year = 100 * (n - 49) + i + l
    return date(year, month, day)

def ethiopian_to_jdn(year, month, day):
    return ETH_EPOCH + 365 * (year - 1) + (year - 1) // 4 + 30 * (month - 1) + day - 1

def jdn_to_ethiopian(jdn):
    days_since = jdn - ETH_EPOCH
    year = (4 * days_since + 1464) // 1461
    days_in_prior = 365 * (year - 1) + (year - 1) // 4
    day_of_year = days_since - days_in_prior
    month = (day_of_year // 30) + 1
    day = (day_of_year % 30) + 1
    return year, month, day

def gregorian_to_ethiopian_date(greg_date):
    if not greg_date:
        return None
    jdn = gregorian_to_jdn(greg_date.year, greg_date.month, greg_date.day)
    return jdn_to_ethiopian(jdn)

def get_ethiopian_fiscal_year_months(fiscal_year):
    """
    Returns the 12 columns for the Ethiopian fiscal year:
    Hamle/(FY-1) through Sene/(FY).
    Each month has:
      - code (e.g. 'm11_prev', 'm10_curr')
      - label (e.g. 'Hamle / 2017')
      - start_date (Gregorian date)
      - end_date (Gregorian date, inclusive)
    """
    prev_year = fiscal_year - 1
    months_def = [
        ('Hamle', prev_year, 11),
        ('Nehase', prev_year, 12),
        ('Meskerem', fiscal_year, 1),
        ('Tikimt', fiscal_year, 2),
        ('Hidar', fiscal_year, 3),
        ('Tahsas', fiscal_year, 4),
        ('Tir', fiscal_year, 5),
        ('Yekatit', fiscal_year, 6),
        ('Megabit', fiscal_year, 7),
        ('Miazia', fiscal_year, 8),
        ('Ginbot', fiscal_year, 9),
        ('Sene', fiscal_year, 10),
    ]

    result = []
    for idx, (m_name, y, m_num) in enumerate(months_def):
        # Ethiopian months 1 to 12 each have 30 days
        jdn_start = ethiopian_to_jdn(y, m_num, 1)
        jdn_end = ethiopian_to_jdn(y, m_num, 30)
        # For Nehase, we also include Pagume (5 or 6 days) so no dates in year are missed
        if m_num == 12:
            is_leap = (y % 4 == 3)
            pagume_days = 6 if is_leap else 5
            jdn_end = ethiopian_to_jdn(y, 13, pagume_days)

        start_greg = jdn_to_gregorian(jdn_start)
        end_greg = jdn_to_gregorian(jdn_end)

        result.append({
            'index': idx,
            'code': f'm_{idx}',
            'name': m_name,
            'year': y,
            'label': f'{m_name}/{y}',
            'start_date': start_greg,
            'end_date': end_greg,
        })
    return result
