from datetime import datetime, timezone
from flask import session
from app.utils.helpers import now_helsinki, mask_email
from app.business import txt, perks


def translate_field(obj, field):
    """Chọn giá trị đã dịch của `field` theo ngôn ngữ session (i18n nội dung DB).
    Trả `field_<lang>` nếu có & không rỗng, ngược lại fallback về cột gốc (English).
    Hỗ trợ cả sqlite3.Row lẫn dict."""
    lang = session.get("lang") or "fi"
    if lang in ("fi", "vi"):
        try:
            val = obj[f"{field}_{lang}"]
        except (KeyError, IndexError):
            val = None
        if val:
            return val
    try:
        return obj[field]
    except (KeyError, IndexError):
        return ""

PAYMENT_METHOD_LABELS = {
    'visa': 'Visa',
    'mastercard': 'Mastercard',
    'mobile_pay': 'Mobile Pay',
    'apple_pay': 'Apple Pay',
    'google_pay': 'Google Pay',
    'cash': 'Cash',
    'bank_transfer': 'Bank Transfer',
}

PAYMENT_METHOD_ICONS = {
    'visa': '💳',
    'mastercard': '💳',
    'mobile_pay': '📱',
    'apple_pay': '📱',
    'google_pay': '📱',
    'cash': '💵',
    'bank_transfer': '🏦',
}

def format_date(value, format='%b %d, %Y'):
    """
    Convert date string từ DB → readable format.
    
    '2025-10-02' → 'Oct 02, 2025'
    Hoặc tùy chỉnh: format_date('2025-10-02', '%d/%m/%Y') → '02/10/2025'
    """
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value  # Trả về string gốc nếu parse lỗi
    return value.strftime(format)


def format_time(value, format='%H:%M'):
    """
    Convert time string → readable format. 24h theo quy ước Phần Lan.

    '10:00' → '10:00'
    '14:30' → '14:30'
    """
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%H:%M')
        except ValueError:
            try:
                value = datetime.strptime(value, '%H:%M:%S')
            except ValueError:
                return value
    return value.strftime(format)


def format_currency(value, currency='€'):
    """
    Format số → tiền tệ, quy ước Phần Lan: dấu phẩy thập phân, khoảng trắng
    ngăn hàng nghìn, ký hiệu đứng sau số.

    25 → '25,00 €'
    25.5 → '25,50 €'
    1234.5 → '1 234,50 €'
    """
    try:
        amount = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        amount = 0.0
    # '1,234.50' → '1 234,50'. Cả hai khoảng trắng đều là nbsp (U+00A0) nên
    # số và ký hiệu tiền không bị ngắt dòng giữa chừng.
    body = f'{amount:,.2f}'.replace(',', ' ').replace('.', ',')
    return f'{body} {currency}'


def short_name(value):
    """
    Convert tên đầy đủ → tên rút gọn.
    
    'Anna Nguyen' → 'Anna N.'
    'Mon' → 'Mon'
    """
    if not value:
        return ''
    parts = value.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f'{parts[0]} {parts[-1][0]}.'

def payment_label(value):
    """'mobile_pay' → 'Mobile Pay' (đã i18n; brand tự fallback về tên gốc)."""
    from flask_babel import gettext
    if not value:
        return ''
    labels = {
        'visa': gettext('Visa'),
        'mastercard': gettext('Mastercard'),
        'mobile_pay': gettext('Mobile Pay'),
        'apple_pay': gettext('Apple Pay'),
        'google_pay': gettext('Google Pay'),
        'cash': gettext('Cash'),
        'bank_transfer': gettext('Bank Transfer'),
    }
    return labels.get(value, value.replace('_', ' ').title())


def payment_icon(value):
    """'mobile_pay' → '📱'"""
    if not value:
        return '💳'   # default
    return PAYMENT_METHOD_ICONS.get(value, '💳')
    

def format_number(value):
    """
    1250 -> '1 250'

    Khoảng trắng ngăn hàng nghìn, cùng quy ước Phần Lan với
    format_currency(): ở fi/vi dấu phẩy là dấu THẬP PHÂN, nên '1,250'
    đọc ra thành "một phẩy hai lăm". Khoảng trắng là nbsp (U+00A0) để
    số không bị ngắt dòng giữa chừng.
    """
    try:
        return f"{int(value):,}".replace(",", " ")
    except (ValueError, TypeError):
        return value


def time_ago(value):
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    delta = now_helsinki() - value
    days = delta.days
    if days < 1:
        return 'today'
    if days < 30:
        return f'{days} day{"s" if days != 1 else ""} ago'
    months = days // 30
    if months < 12:
        return f'{months} month{"s" if months != 1 else ""} ago'
    years = days // 365
    return f'{years} year{"s" if years != 1 else ""} ago'


def register_filters(app):
    """Đăng ký tất cả filters với Flask app"""
    app.template_filter('format_date')(format_date)
    app.template_filter('format_time')(format_time)
    app.template_filter('format_currency')(format_currency)
    app.template_filter('short_name')(short_name)
    app.template_filter('payment_icon')(payment_icon)
    app.template_filter('payment_label')(payment_label)
    app.template_filter('format_number')(format_number)
    app.template_filter('time_ago')(time_ago)
    app.template_filter('mask_email')(mask_email)
    # i18n nội dung DB: {{ tr(service, 'name') }}
    app.jinja_env.globals['tr'] = translate_field
    # Nội dung tĩnh từ app/business.py: {{ txt('about.story_lead') }}
    app.jinja_env.globals['txt'] = txt
    app.jinja_env.globals['perks'] = perks
