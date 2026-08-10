from datetime import datetime, timedelta, UTC
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from app.business import BUSINESS

HELSINKI_TZ = ZoneInfo("Europe/Helsinki")

def now_helsinki():
    """Current Helsinki wall-clock time, naive (tzinfo stripped). SQLite has no
    timezone-aware column type, so every timestamp this app stores/compares is
    a naive string — this is the single source of truth for what that string
    means. Do not mix with datetime.now() (server-local) or datetime.now(UTC)."""
    return datetime.now(HELSINKI_TZ).replace(tzinfo=None)

def today_helsinki():
    return now_helsinki().date()

def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M")

def split_customer_bookings(bookings):
    
    upcoming_bookings = []
    pending_bookings = []
    cancelled_bookings = []
    completed_bookings = []
    next_visit = None

    for booking in bookings:
        status = booking["status"]

        if status == "confirmed":
            upcoming_bookings.append({
                "booking": booking,
                "booking_date": format_booking_date(booking["booking_date"]),
                "booking_time": format_booking_time(booking["start_time"])
            })
        elif status == "pending":
            pending_bookings.append({
                "booking": booking,
                "booking_date": format_booking_date(booking["booking_date"]),
                "booking_time": format_booking_time(booking["start_time"])
            })
        elif status == "cancelled":
            cancelled_bookings.append({
                "booking": booking,
                "booking_date": format_booking_date(booking["booking_date"]),
                "booking_time": format_booking_time(booking["start_time"]),
                "cancelled_date": format_booking_date(booking["updated_at"])

            })
        elif status == "completed":
            completed_bookings.append({
                "booking": booking,
                "booking_date": format_booking_date(booking["booking_date"]),
                "booking_time": format_booking_time(booking["start_time"]),
            })
        
    if upcoming_bookings:
        next_visit = upcoming_bookings[0]["booking"]
    elif pending_bookings:
        next_visit = pending_bookings[0]["booking"]
    return {
        "next_visit": next_visit,
        "upcoming_bookings": upcoming_bookings,
        "pending_bookings": pending_bookings,
        "cancelled_bookings": cancelled_bookings,
        "completed_bookings": completed_bookings,
    }

def format_booking_date(date_str):
    if len(date_str) > 11:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    else:
        date_obj = datetime.strptime(date_str,"%Y-%m-%d")
    return date_obj.strftime("%a, %b %d")

def format_booking_time(time_str):
    """Giờ hiển thị theo quy ước Phần Lan: 24h, không AM/PM."""
    time_obj = datetime.strptime(time_str, "%H:%M")
    return time_obj.strftime("%H:%M")

def combine_date_time(date_str, time_str):
    datetime_str = f"{date_str} {time_str}"

    if len(time_str) == 5:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

def build_gg_calendar_url(title, date, start_time, end_time, details="", location=""):
    """
    Định dang str đầu vào:
    start_date = '2026-04-18'
    start_time = '09:00'
    end_time = '14:00'
    """

    start_dt = combine_date_time(date, start_time)
    end_dt = combine_date_time(date, end_time)

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}",
        "details": details,
        "location": location,
        "ctz": "Europe/Helsinki",
    }

    return "https://calendar.google.com/calendar/render?" + urlencode(params)

def build_calendar_url( sevi_name, staff_name, date, start_time, end_time):
    
    
    brand = BUSINESS["brand_name"]

    title = f"{sevi_name} - {brand}"

    details = f"Appointment with {staff_name} at {brand}"

    location = BUSINESS["address"]

    return {
        "url": build_gg_calendar_url(title, date, start_time, end_time, details, location),
        "url_target": "_blank"
    }

def build_services_by_category(categories, services):
    services_by_category = {category['slug']: [] for category in categories}
    for service in services:
        services_by_category[service['category_slug']].append(service)
    return services_by_category

def mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    return f"{local[0]}***@{domain}"

def build_gg_map_url(address):
    params = {
        "api": "1",
        "query": address
    }
    return "https://www.google.com/maps/search/?" + urlencode(params)
