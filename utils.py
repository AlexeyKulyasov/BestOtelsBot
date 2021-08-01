from datetime import datetime


def is_valid_number(value: str, min_val: int = 0, max_val: int = None) -> bool:
    if not value.isdigit():
        return False
    if max_val is not None and min_val <= int(value) <= max_val:
        return True
    if max_val is None and int(value) >= min_val:
        return True
    return False


def is_valid_date(date: str) -> bool:
    try:
        result = datetime.strptime(date, '%Y-%m-%d').date() >= datetime.today().date()
    except ValueError:
        return False
    return result
