import os
import re
import time
import uuid
import sqlite3
import secrets
import string
import unicodedata
import calendar
from flask import Blueprint, flash,render_template, request, jsonify, redirect, url_for, session, Response
from app.database.db import (
    get_report_totals, get_report_revenue_by_day, get_report_revenue_by_hour, get_report_booking_status,
    get_report_top_services, get_report_staff_performance, get_report_loyalty,
    get_report_customer_growth,
)
from app.database.db import get_connection, get_invoice_detail_by_id, get_customer_appointment_history, get_customer_invoices, get_active_services_with_category ,get_active_service_categories ,update_booking_schedule, get_customer_by_customer_id ,get_customer_bookings ,get_staff_by_user_id ,get_customer_by_user_id ,update_verification ,get_verification_by_id ,create_verification ,link_customer_to_user ,get_customer_by_email, create_user ,get_user_by_email, verify_customer,get_all_services, get_all_staff, get_service_by_id, get_staff_by_id, check_booking_conflict, get_customer_id, create_booking, create_customer,update_status, get_booking_by_id, update_new_code, get_booking_by_staff_and_date, get_loyalty_balance, get_active_rewards, get_loyalty_history, get_customer_current_tier, get_tier_by_name, get_tier_by_id, get_customer_subscription_row, get_active_subscription_rows, upgrade_membership, has_source_award, has_pending_review, get_customer_reward_status, redeem_reward, get_customer_vouchers, update_customer_profile, update_user_email, update_user_password, cancel_booking_with_reason, get_gallery_images, get_active_staff, get_admin_kpis, get_admin_today_appointments, get_admin_recent_activity, get_admin_revenue_chart, get_all_customers, get_admin_bookings, get_booking_status_counts, update_booking_details, get_staff_stats, get_staff_list, get_staff_role_list, create_staff, update_staff, delete_staff, toggle_staff_active, get_all_categories, get_service_categories_with_services, get_service_stats, create_service, update_service, delete_service, toggle_service_active, create_category, update_category, delete_category, get_admin_customer_stats, get_admin_customers, create_customer_admin, update_customer_admin, delete_customer_admin, get_gallery_images_admin, get_gallery_image_by_id, get_gallery_stats, create_gallery_images, update_gallery_image, delete_gallery_image, bulk_delete_gallery_images, reorder_gallery_images, get_admin_loyalty_customers, get_admin_loyalty_stats, get_rewards_admin, get_missions, create_reward, update_reward, get_reward_by_id, get_reward_redemption_count, delete_reward, deactivate_reward, update_mission_config, toggle_mission_config, get_active_membership_tiers, adjust_membership_admin, MISSION_KEYS, get_carousel_slides, get_carousel_slide_by_id, get_next_carousel_sort_order, create_homepage_slide, update_homepage_slide, create_offer_slide, update_offer_slide, delete_carousel_slide, get_mission_slides, update_mission_slide, reorder_carousel_slides, MISSION_SLOT_KEYS, auto_expire_bookings, get_admin_top_loyalty, get_admin_new_members, get_admin_top_services, get_popular_services, get_staff_bookings_range, get_invoice_by_booking, mark_invoice_paid, create_invoice, get_staff_history, get_staff_history_months, get_staff_history_stats, get_staff_profile_stats, update_staff_photo
from datetime import datetime, timedelta, date
from app.services.email_system import send_verification_email, send_thank_you_email, generate_verification_code
from app.services.booking_service import GuestService, BookingService, BookingValidatorError, GuestInfoMissingError,get_available_slots, get_following_days, complete_booking_txn, revert_booking_txn
from app.services.loyalty import get_active_multiplier, get_config_value, already_awarded, award_points, check_streak
from app.services.payment_service import create_booking_checkout_session, construct_event, handle_event, fulfill_from_session, create_subscription_checkout_session, cancel_subscription, create_billing_portal_session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from app.utils.helpers import split_customer_bookings, format_booking_date, format_booking_time, build_calendar_url, build_gg_map_url, build_services_by_category, mask_email, now_helsinki, today_helsinki
from collections import Counter
from app import oauth, csrf
from app.database.db import create_oauth_user, set_user_oauth
main = Blueprint("main",__name__)

_failed_logins = {}       # {ip: {"count": int, "blocked_until": float}}
_MAX_LOGIN_ATTEMPTS = 5
_LOGIN_LOCKOUT = 15 * 60  # 15 phút
_ADMIN_IDLE_TIMEOUT = 30 * 60  # 30 phút

_AVATAR_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "avatars")
_ALLOWED_AVATAR_EXT = {"jpg", "jpeg", "png", "gif"}
_MAX_AVATAR_SIZE = 800 * 1024  # 800KB

# Bảng màu cho avatar initials (dùng khi khách chưa upload ảnh)
_AVATAR_PALETTE = [
    ("#e0e7ff", "#3730a3"), ("#fce7f3", "#9d174d"),
    ("#fef3c7", "#92400e"), ("#f3e8ff", "#6b21a8"),
    ("#dcfce7", "#166534"), ("#fee2e2", "#991b1b"),
]

_SERVICE_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "services")
_ALLOWED_SERVICE_IMG_EXT = {"jpg", "jpeg", "png", "webp"}
_MAX_SERVICE_IMG_SIZE = 2 * 1024 * 1024  # 2MB

_GALLERY_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "gallery")
_ALLOWED_GALLERY_IMG_EXT = {"jpg", "jpeg", "png", "webp"}
_MAX_GALLERY_IMG_SIZE = 2 * 1024 * 1024  # 2MB

_REWARD_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "rewards")
_ALLOWED_REWARD_IMG_EXT = {"jpg", "jpeg", "png", "webp"}
_MAX_REWARD_IMG_SIZE = 2 * 1024 * 1024  # 2MB

_CAROUSEL_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "carousels")
_ALLOWED_CAROUSEL_IMG_EXT = {"jpg", "jpeg", "png", "webp"}
_MAX_CAROUSEL_IMG_SIZE = 2 * 1024 * 1024  # 2MB

_STAFF_IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "staff")
_ALLOWED_STAFF_IMG_EXT = {"jpg", "jpeg", "png", "webp"}
_MAX_STAFF_IMG_SIZE = 2 * 1024 * 1024  # 2MB

def _slugify(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text

def _save_service_image(file):
    """Validates and saves an uploaded service image. Returns the stored filename, or None if no file given."""
    if not file or not file.filename:
        return None
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_SERVICE_IMG_EXT:
        raise ValueError("Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPG, PNG, WEBP.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_SERVICE_IMG_SIZE:
        raise ValueError("Ảnh quá lớn. Kích thước tối đa 2MB.")

    os.makedirs(_SERVICE_IMG_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_SERVICE_IMG_DIR, filename))
    return filename

def _save_gallery_image(file):
    """Validates and saves an uploaded gallery image. Returns the stored filename, or None if no file given."""
    if not file or not file.filename:
        return None
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_GALLERY_IMG_EXT:
        raise ValueError("Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPG, PNG, WEBP.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_GALLERY_IMG_SIZE:
        raise ValueError("Ảnh quá lớn. Kích thước tối đa 2MB.")

    os.makedirs(_GALLERY_IMG_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_GALLERY_IMG_DIR, filename))
    return filename

def _save_reward_image(file):
    """Validates and saves an uploaded reward banner image. Returns the stored filename, or None if no file given."""
    if not file or not file.filename:
        return None
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_REWARD_IMG_EXT:
        raise ValueError("Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPG, PNG, WEBP.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_REWARD_IMG_SIZE:
        raise ValueError("Ảnh quá lớn. Kích thước tối đa 2MB.")

    os.makedirs(_REWARD_IMG_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_REWARD_IMG_DIR, filename))
    return filename

def _save_carousel_image(file):
    """Validates and saves an uploaded carousel/mission image. Returns the stored filename, or None if no file given."""
    if not file or not file.filename:
        return None
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_CAROUSEL_IMG_EXT:
        raise ValueError("Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPG, PNG, WEBP.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_CAROUSEL_IMG_SIZE:
        raise ValueError("Ảnh quá lớn. Kích thước tối đa 2MB.")

    os.makedirs(_CAROUSEL_IMG_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_CAROUSEL_IMG_DIR, filename))
    return filename

def _resolve_carousel_image(image):
    """carousel_slides.image holds either a bare uploaded filename (new admin uploads,
    served from static/uploads/carousels/) or a legacy absolute path/URL (the 3
    pre-existing homepage/mission images migrated from the old hardcoded lists).
    Returns a ready-to-use src, or None."""
    if not image:
        return None
    if image.startswith("http://") or image.startswith("https://") or image.startswith("/"):
        return image
    return url_for("static", filename=f"uploads/carousels/{image}")

def _resolve_staff_photo(photo):
    """staff.photo holds either a bare uploaded filename (new avatar uploads,
    served from static/uploads/staff/) or a legacy absolute URL (seed data).
    Returns a ready-to-use src, or None."""
    if not photo:
        return None
    if photo.startswith("http://") or photo.startswith("https://") or photo.startswith("/"):
        return photo
    return url_for("static", filename=f"uploads/staff/{photo}")

def _save_staff_image(file):
    """Validates and saves an uploaded staff avatar. Returns the stored filename, or None if no file given."""
    if not file or not file.filename:
        return None
    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_STAFF_IMG_EXT:
        raise ValueError("Định dạng ảnh không hợp lệ. Chỉ chấp nhận JPG, PNG, WEBP.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_STAFF_IMG_SIZE:
        raise ValueError("Ảnh quá lớn. Kích thước tối đa 2MB.")

    os.makedirs(_STAFF_IMG_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(_STAFF_IMG_DIR, filename))
    return filename

def _name_initials(full_name):
    """Returns up to 2 uppercase initials from a name, e.g. 'Ha Anh' -> 'HA'."""
    parts = (full_name or "").split()
    return "".join(p[0].upper() for p in parts[:2]) or "?"

def _resolve_customer_avatar(user_id):
    """Returns the customer's avatar URL with a cache-busting version tag, or None if not set.
    Avatars are stored as {user_id}.{ext} in static/uploads/avatars/."""
    for ext in _ALLOWED_AVATAR_EXT:
        path = os.path.join(_AVATAR_DIR, f"{user_id}.{ext}")
        if os.path.exists(path):
            version = int(os.path.getmtime(path))
            return url_for("static", filename=f"uploads/avatars/{user_id}.{ext}", v=version)
    return None

def _save_avatar_image(file, user_id):
    """Validates and saves a customer avatar as {user_id}.{ext} (max 800KB, JPG/GIF/PNG).
    Removes any previous avatar first. Raises ValueError on invalid input."""
    if not file or not file.filename:
        raise ValueError("No file selected.")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in _ALLOWED_AVATAR_EXT:
        raise ValueError("Invalid file type. JPG, GIF or PNG only.")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > _MAX_AVATAR_SIZE:
        raise ValueError("File is too large. Max size is 800KB.")

    os.makedirs(_AVATAR_DIR, exist_ok=True)
    for old_ext in _ALLOWED_AVATAR_EXT:
        old_path = os.path.join(_AVATAR_DIR, f"{user_id}.{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    file.save(os.path.join(_AVATAR_DIR, f"{user_id}.{ext}"))

@main.app_context_processor
def inject_customer_sidebar():
    """Exposes the logged-in customer's avatar + name to every customer template
    (sidebar in customer_base.html). Returns {} for non-customer requests."""
    if session.get("role") != "customer":
        return {}
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id) if user_id else None
    if not customer:
        return {}
    bg, fg = _AVATAR_PALETTE[user_id % len(_AVATAR_PALETTE)]
    return {"sidebar_customer": {
        "name": customer["full_name"],
        "avatar_url": _resolve_customer_avatar(user_id),
        "initials": _name_initials(customer["full_name"]),
        "avatar_bg": bg,
        "avatar_color": fg,
    }}

#Server config
def customer_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        customer_id = session.get('customer_id')
        if not customer_id or not get_customer_by_customer_id(customer_id):
            session.clear()
            flash("Please login!", "error")
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapped_view

def guest_only(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id"):
            role = session.get("role")
            if role == "staff":
                return redirect(url_for("main.staff_dashboard"))
            if role == "admin":
                return redirect(url_for("main.admin_dashboard"))
            return redirect(url_for("main.customer_dashboard"))
        return view_func(*args, **kwargs)
    return wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id") or session.get("role") != "admin":
            flash("Unauthorized.", "error")
            return redirect(url_for("main.staff_login"))
        now = time.time()
        if now - session.get("admin_last_activity", 0) > _ADMIN_IDLE_TIMEOUT:
            session.clear()
            flash("Session expired. Please log in again.", "error")
            return redirect(url_for("main.staff_login"))
        session["admin_last_activity"] = now
        return view_func(*args, **kwargs)
    return wrapped_view

def staff_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id") or session.get("role") != "staff":
            flash("Bạn không có quyền truy cập khu vực này.", "error")
            return redirect(url_for("main.staff_login"))
        return view_func(*args, **kwargs)
    return wrapped_view

def _get_current_staff():
    """current_staff dict cho staff portal. Bảng staff dùng cột full_name → map sang 'name'
    theo staff_base.html. Các field mở rộng (email/phone/photo/...) phục vụ trang Hồ sơ."""
    staff = get_staff_by_user_id(session.get("user_id"))
    if not staff:
        return None
    return {
        "id": staff["id"],
        "user_id": staff["user_id"],
        "name": staff["full_name"],
        "role": staff["role"],
        "email": staff["email"],
        "phone": staff["phone"],
        "avatar": _resolve_staff_photo(staff["photo"]),
        "hourly_rate": staff["hourly_rate"],
        "commission_rate": staff["commission_rate"],
        "created_at": staff["created_at"],
    }

#====================================
#               Public
#====================================


#====================================
#               customer
#====================================
@main.route("/customer/dashboard")
@customer_login_required
def customer_dashboard():
    user_id = session.get('user_id')
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for('main.login'))

    customer_id = customer["id"]
    today = today_helsinki()

    all_bookings = get_customer_bookings(customer_id) or []
    upcoming_booking = None
    for b in all_bookings:
        if b["status"] in ("confirmed", "pending") and b["booking_date"] >= str(today):
            _cal = build_calendar_url(
                b["service_name"], b["staff_name"],
                b["booking_date"], b["start_time"], b["end_time"],
            )
            _img = b["service_image"]
            upcoming_booking = {
                "id":           b["id"],
                "service_name": b["service_name"],
                "date":         format_booking_date(b["booking_date"]),
                "time":         format_booking_time(b["start_time"]),
                "staff_name":   b["staff_name"],
                "status":       b["status"],
                "calendar_url": _cal["url"],
                "url_target":   _cal["url_target"],
                "service_img":  url_for("static", filename=f"uploads/services/{_img}") if _img else None,
            }
            break

    all_rewards = get_active_rewards()
    carousel_rewards = []
    for s in get_carousel_slides("dashboard_offers", active_only=True):
        carousel_rewards.append({
            "title":     s["title"],
            "subtitle":  s["subtitle"],
            "badge":     s["badge"],
            "image":     _resolve_carousel_image(s["image"]),
            "cta_label": s["cta_label"],
            "cta_url":   s["cta_url"],
        })

    loyalty_points = get_loyalty_balance(customer_id)
    next_reward = None
    progress_pct = 0
    points_needed = 0
    for r in all_rewards:
        r = dict(r)
        if loyalty_points < r["cost"]:
            next_reward = r
            progress_pct = min(100, int(loyalty_points / r["cost"] * 100))
            points_needed = r["cost"] - loyalty_points
            break

    return render_template(
        "/customer/customer_dashboard.html",
        customer=customer,
        current_user={"name": customer["full_name"]},
        upcoming_booking=upcoming_booking,
        loyalty_points=loyalty_points,
        next_reward=next_reward,
        progress_pct=progress_pct,
        points_needed=points_needed,
        carousel_rewards=carousel_rewards,
    )

@main.route("/customer/booking")
@customer_login_required
def customer_booking():
    preselect_id = request.args.get("service_id", type=int)

    today = today_helsinki()
    max_date = today + timedelta(days=60)

    categories = get_active_service_categories()
    services = get_active_services_with_category()
    staffs = get_all_staff()

    if preselect_id and preselect_id not in [s["id"] for s in services]:
        flash("That service is no longer available. Showing our full menu.", "warning")
        preselect_id = None

    services_by_category = build_services_by_category(categories, services)

    customer_id = session.get("customer_id")
    multiplier = get_active_multiplier(customer_id)

    return render_template(
        "/customer/customer_booking.html",
        categories=categories,
        services_by_category=services_by_category,
        staffs=staffs,
        today=today,
        max_date=max_date,
        multiplier=multiplier,
        preselect_id=preselect_id,
    )

@main.route("/customer/cancel-booking/booking_id=<int:booking_id>", methods=["POST"])
@customer_login_required
def cancel_booking(booking_id):
    booking = get_booking_by_id(booking_id)

    if not booking:
        flash("Booking not found", "error")
        return redirect(url_for("main.my_bookings"))
    
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)

    if not customer or booking["customer_id"] != customer["id"]:
        flash("User not found!", "error") 
        return redirect(url_for("main.my_bookings"))
        
    if booking["status"] not in ("pending", "confirmed"):
        flash("This booking cannot be cancelled", "error")
        return redirect(url_for("main.view_booking_details", booking_id=booking_id))
    
    reason = request.form.get("cancellation_reason", "")
    cancel_booking_with_reason(booking_id, reason)

    flash("Booking cancelled successfully", "success")
    return redirect(url_for("main.my_bookings"))

@main.route("/customer/my-booking")
@customer_login_required
def my_bookings():
    user_id = session.get("user_id")
    if not user_id:
        flash("Session Expired. Please login again.")
        session.clear()
        return redirect(url_for('main.home'))
    
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found by some how :D", "error")
        return redirect(url_for('main.customer_dashboard'))
    customer_id = customer["id"]

    all_bookings = get_customer_bookings(customer_id) or []
    booking_groups = split_customer_bookings(all_bookings)

    # Next-visit card's data
    next_visit = booking_groups["next_visit"]

    nevi_status = nevi_service = nevi_staff = nevi_date = nevi_start = None
    calendar_url = url_target = None

    if next_visit:
        next_visit_service = get_service_by_id(next_visit["service_id"])
        next_visit_staff = get_staff_by_id(next_visit["staff_id"])

        if next_visit_service and next_visit_staff:
            nevi_status = next_visit["status"]
            nevi_service = next_visit_service["name"]
            nevi_staff = next_visit_staff["full_name"]
            nevi_date = format_booking_date(next_visit["booking_date"])
            nevi_start = format_booking_time(next_visit["start_time"])

            _cal = build_calendar_url(
                nevi_service, nevi_staff,
                next_visit["booking_date"],
                next_visit["start_time"],
                next_visit["end_time"],
            )
            calendar_url = _cal["url"]
            url_target = _cal["url_target"]

    # Manage Appointments card's data
    upcoming_bookings = booking_groups["upcoming_bookings"]
    pending_bookings = booking_groups["pending_bookings"]
    cancelled_bookings = booking_groups["cancelled_bookings"]

    # Recent history
    appointment_history = get_customer_appointment_history(customer_id) or []
    invoices = get_customer_invoices(customer_id) or []
    invoice_by_booking = {inv["booking_id"]: inv["invoice_id"] for inv in invoices}
    recent_history = []
    for appt in appointment_history[:5]:
        appt["invoice_id"] = invoice_by_booking.get(appt["booking_id"])
        recent_history.append(appt)

    # Loyalty card data
    all_rewards = get_active_rewards()
    loyalty_points = get_loyalty_balance(customer_id)
    next_reward = None
    progress_pct = 0
    points_needed = 0
    for r in all_rewards:
        r = dict(r)
        if loyalty_points < r["cost"]:
            next_reward = r
            progress_pct = min(100, int(loyalty_points / r["cost"] * 100))
            points_needed = r["cost"] - loyalty_points
            break

    return render_template(
        "/customer/my_bookings.html",
        nevi_status=nevi_status,
        nevi_service=nevi_service,
        nevi_staff=nevi_staff,
        nevi_date=nevi_date,
        nevi_start=nevi_start,
        next_visit=next_visit,
        calendar_url=calendar_url,
        url_target=url_target,
        upcoming_bookings=upcoming_bookings,
        pending_bookings=pending_bookings,
        cancelled_bookings=cancelled_bookings,
        recent_history=recent_history,
        loyalty_points=loyalty_points,
        next_reward=next_reward,
        progress_pct=progress_pct,
        points_needed=points_needed,
    )

@main.route("/customer/my-booking/booking_id=<int:booking_id>")
@customer_login_required
def view_booking_details(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Booking not found!", "error")
        return redirect(url_for('main.my_bookings'))

    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for('main.my_bookings'))

    if booking["customer_id"] != customer["id"]:
        flash("Booking not found!")
        return redirect(url_for('main.my_bookings'))
    
    service_id = booking["service_id"]
    service = get_service_by_id(service_id)
    if not service:
        flash("Service data unavailable.", "error")
        return redirect(url_for('main.my_bookings'))

    staff_id = booking["staff_id"]
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("Staff data unavailable.", "error")
        return redirect(url_for('main.my_bookings'))

    calendar_url = build_calendar_url(
        service["name"],
        staff["full_name"],
        booking["booking_date"],
        booking["start_time"],
        booking["end_time"],
    )
    
    booking_date_obj = datetime.strptime(booking["booking_date"], "%Y-%m-%d")
    booking_date1 = booking_date_obj.strftime("%b %d")
    booking_date2 = booking_date_obj.strftime("%a")
    
    booking_time = format_booking_time(booking["start_time"])
    
    address = "Kyyhkysmäki 9, 02650 Espoo"
    ggmap_url = build_gg_map_url(address)

    return render_template(
        "/customer/view_booking_details.html",
        calendar_url=calendar_url["url"],
        status=booking["status"],
        service=service["name"],
        duration=service["duration_minutes"],
        price=service["price"],
        date1=booking_date1,
        date2=booking_date2,
        time=booking_time,
        staff=staff["full_name"],
        map_url=ggmap_url,
        service_description=service["description"],
        booking=booking,
    )

@main.route("/customer/reschedule/booking_id=<int:booking_id>", methods=["GET", "POST"])
@customer_login_required
def customer_reschedule(booking_id):
    
    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Booking not found!", "error")
        return redirect(url_for('main.my_bookings'))

    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for('main.my_bookings'))

    if booking['customer_id'] != customer['id']:
        flash('Booking not found', 'error')
        return redirect(url_for('main.my_bookings'))
    
    service_id = booking["service_id"]
    service = get_service_by_id(service_id)
    if not service:
        flash("Service data unavailable.", "error")
        return redirect(url_for('main.my_bookings'))

    staff_id = booking["staff_id"]
    staff = get_staff_by_id(staff_id)
    if not staff:
        flash("Staff data unavailable.", "error")
        return redirect(url_for('main.my_bookings'))

    booking_date_obj = datetime.strptime(booking["booking_date"], "%Y-%m-%d")
    booking_date = booking_date_obj.strftime("%b %d")
    booking_time = format_booking_time(booking["start_time"])

    #BLOCK: Select new date
    today = today_helsinki()
    max_reschedule_date = today + timedelta(days=14)
    
    if request.method == "POST":
        new_date = request.form.get("new_date")
        new_time = request.form.get("new_time")
        
        #Validate backend
        if not new_date or not new_time:
            flash("Please select a new date and time", "error")
            return redirect(url_for('main.customer_reschedule',booking_id=booking_id))
        
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d").date()

        if new_date_obj < today or new_date_obj > max_reschedule_date:
            flash("You can only reschedule within the next 14 days", "error")
            return redirect(url_for('main.customer_reschedule',booking_id=booking_id))

        #TODO: Check available slots here!
        try:
            new_time_obj = datetime.strptime(new_time, "%H:%M").time()
        except ValueError:
            flash("Invalid time format", "error")
            return redirect(url_for('main.customer_reschedule', booking_id=booking_id))
        
        new_start_dt = datetime.combine(new_date_obj, new_time_obj)
        new_end_dt = new_start_dt + timedelta(minutes=service["duration_minutes"])

        new_date_string = new_date_obj.strftime("%Y-%m-%d")
        new_start_time = new_start_dt.strftime("%H:%M")
        new_end_time = new_end_dt.strftime("%H:%M")

        existing_bookings = get_booking_by_staff_and_date(
            staff_id,
            new_date_string
        )

        existing_bookings = [
            item for item in existing_bookings
            if item["id"] != booking["id"]
            and item["status"] in ("pending", "confirmed", "in-progress")
        ]

        available_slots = get_available_slots(
            service["duration_minutes"],
            existing_bookings,
            "09:00",
            "18:00",
            30
        )

        if new_start_time not in available_slots:
            flash("This time slot is no longer available.", "error")
            flash("Please choose another time.", "error")
            return redirect(url_for('main.customer_reschedule', booking_id=booking_id))
        
        #TODO: Update booking_date, start_at, end_at
        update_booking_schedule(
            booking_id,
            new_date_string,
            new_start_time,
            new_end_time
        )

        flash("Booking rescheduled successfully", "success")
        return redirect(url_for('main.view_booking_details',booking_id=booking_id))   
    
    #Data send to frontend:

    #Comparision block
    cp_booking_date = booking_date_obj.strftime("%b %d, %Y")


    return render_template(
        "/customer/reschedule.html",
        booking=booking,
        service=service,
        staff=staff,
        today=today,
        max_reschedule_date=max_reschedule_date,
        selected_date=today,
        booking_date=booking_date,
        booking_time=booking_time,
        cp_booking_date=cp_booking_date,
        duration=service['duration_minutes']

    )

@main.route("/customer/reschedule/booking_id=<int:booking_id>/available-slots")
@customer_login_required
def get_reschedule_available_slots(booking_id):
    booking = get_booking_by_id(booking_id)

    if not booking:
        return jsonify({
            "success": False,
            "message": "Booking not found",
            "slots": []
        }), 404
    
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)

    if not customer or booking["customer_id"] != customer["id"]:
        return jsonify({
            "success": False,
            "message": "Booking not found",
            "slots": []
        }), 403
    
    date_string = request.args.get("date", "").strip()

    if not date_string:
        return jsonify({
            "success": False,
            "message": "Missing date",
            "slots": []
        }), 400
    
    try:
        selected_date = datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid date format",
            "slots": []
        }), 400
    
    today = today_helsinki()
    max_reschedule_date = today + timedelta(days=14)

    if selected_date < today or selected_date > max_reschedule_date:
        return jsonify({
            "success": False,
            "message": "Date is outside reschedule range",
            "slots": []
        }), 400
    
    service = get_service_by_id(booking["service_id"])

    if not service:
        return jsonify({
            "success": False,
            "message": "Service not found",
            "slots": []
        }), 404
    
    service_duration = service["duration_minutes"]
    staff_id = booking["staff_id"]

    existing_bookings = get_booking_by_staff_and_date(staff_id, date_string)
    
    existing_bookings = [
        item for item in existing_bookings
        if item["id"] != booking["id"]
        and item["status"] in ("pending", "confirmed", "in-progress")
    ]

    raw_slots = get_available_slots(
        service_duration,
        existing_bookings,
        "09:00",
        "18:00",
        30
    )

    slots = [
        {
            "label": datetime.strptime(slot, "%H:%M").strftime("%I:%M %p"),
            "value": slot
        }
        for slot in raw_slots
    ]
    return jsonify({
        "success": True,
        "slots": slots
    })
    
@main.route("/customer/setting")
@customer_login_required
def customer_setting():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    dob_raw = customer["date_of_birth"]
    dob = datetime.strptime(dob_raw, "%Y-%m-%d").date() if dob_raw else None

    profile_picture = _resolve_customer_avatar(user_id)

    current_user = {
        "full_name": customer["full_name"],
        "email": customer["email"],
        "phone": customer["phone"] or "",
        "date_of_birth": dob,
        "profile_picture": profile_picture,
        "password_last_changed": None,
    }
    return render_template("/customer/customer_setting.html", current_user=current_user)

@main.route("/customer/setting/update-profile", methods=["POST"])
@customer_login_required
def update_profile():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    date_of_birth = request.form.get("date_of_birth", "").strip() or None

    if not full_name:
        flash("Name is required.", "error")
        return redirect(url_for("main.customer_setting"))

    update_customer_profile(customer["id"], full_name, customer["email"], phone, date_of_birth)
    flash("Profile updated successfully.", "success")
    return redirect(url_for("main.customer_setting"))


@main.route("/customer/setting/update-avatar", methods=["POST"])
@customer_login_required
def update_avatar():
    user_id = session.get("user_id")
    file = request.files.get("avatar")

    try:
        _save_avatar_image(file, user_id)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.customer_setting"))

    flash("Profile picture updated.", "success")
    return redirect(url_for("main.customer_setting"))


@main.route("/customer/setting/request-password-change", methods=["POST"])
@customer_login_required
def request_password_change():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."}), 404

    expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    code = generate_verification_code()
    verification_id = create_verification(code, "password_change", expires_at)
    send_verification_email(customer["email"], code, "password_change")
    session["password_change_verification_id"] = verification_id

    return jsonify({"success": True})


@main.route("/customer/setting/change-password", methods=["POST"])
@customer_login_required
def change_password():
    user_id = session.get("user_id")

    verification_id = session.get("password_change_verification_id")
    if not verification_id:
        flash("Verification session expired. Please request a new code.", "error")
        return redirect(url_for("main.customer_setting"))

    user_code = request.form.get("verification_code", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    verification = get_verification_by_id(verification_id)
    if not verification:
        flash("Verification code expired. Please request a new code.", "error")
        session.pop("password_change_verification_id", None)
        return redirect(url_for("main.customer_setting"))

    if user_code != verification["verification_code"]:
        flash("Incorrect verification code.", "error")
        return redirect(url_for("main.customer_setting"))

    if new_password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("main.customer_setting"))

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("main.customer_setting"))

    update_verification(verification_id, user_id, 1)
    update_user_password(user_id, generate_password_hash(new_password))
    session.pop("password_change_verification_id", None)
    flash("Password changed successfully.", "success")
    return redirect(url_for("main.customer_setting"))


@main.route("/customer/setting/request-email-change", methods=["POST"])
@customer_login_required
def request_email_change():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."}), 404

    expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    code = generate_verification_code()
    verification_id = create_verification(code, "email_change", expires_at)
    send_verification_email(customer["email"], code, "email_change")
    session["email_change_verification_id"] = verification_id

    return jsonify({"success": True})


@main.route("/customer/setting/update-email-address", methods=["POST"])
@customer_login_required
def update_email_address():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for("main.customer_setting"))

    verification_id = session.get("email_change_verification_id")
    if not verification_id:
        flash("Verification session expired. Please request a new code.", "error")
        return redirect(url_for("main.customer_setting"))

    user_code = request.form.get("verification_code", "").strip()
    new_email = request.form.get("new_email", "").strip().lower()

    if not user_code or not new_email:
        flash("Please fill in all fields.", "error")
        return redirect(url_for("main.customer_setting"))

    verification = get_verification_by_id(verification_id)
    if not verification:
        flash("Verification code expired. Please request a new code.", "error")
        session.pop("email_change_verification_id", None)
        return redirect(url_for("main.customer_setting"))

    if user_code != verification["verification_code"]:
        flash("Incorrect verification code.", "error")
        return redirect(url_for("main.customer_setting"))

    if new_email == customer["email"]:
        flash("New email is the same as your current email.", "error")
        return redirect(url_for("main.customer_setting"))

    existing = get_user_by_email(new_email)
    if existing and existing["id"] != user_id:
        flash("Email is already taken.", "error")
        return redirect(url_for("main.customer_setting"))

    update_verification(verification_id, user_id, 1)
    update_user_email(user_id, new_email)
    update_customer_profile(customer["id"], customer["full_name"], new_email, customer["phone"] or "", customer["date_of_birth"])
    session["user_email"] = new_email
    session.pop("email_change_verification_id", None)

    flash("Email updated successfully.", "success")
    return redirect(url_for("main.customer_setting"))


@main.route("/customer/history", methods=['GET'])
@customer_login_required
def customer_history():

    user_id = session.get("user_id")
    if user_id is None:
        flash("User not found. Please login!", "error")
        return redirect(url_for("main.login"))

    customer = get_customer_by_user_id(user_id)
    if customer is None:
        flash("Customer profile not found.", "error")
        return redirect(url_for("main.login"))
    
    customer_id = customer['id']

    appointments = get_customer_appointment_history(customer_id)
    invoices = get_customer_invoices(customer_id)
    
    #Categorize appt
    for appt in appointments:
        if appt['status'] == 'cancelled':
            appt['display_type'] = 'cancelled'
        elif appt['review_id']:
            appt['display_type'] = 'reviewed'
        else:
            appt['display_type'] = 'need_review'

    completed_appointments = [a for a in appointments if a['status'] == 'done']
    
    total_visits = len(completed_appointments)    
    total_spent = sum([i['amount'] or 0 for i in invoices if i['invoice_status'] == 'paid'])
    
    #Fav stylist
    stylist_names = [a['stylist_name'] for a in completed_appointments]
    stylist_counter = Counter(stylist_names)
    if stylist_counter:
        name, count = stylist_counter.most_common(1)[0]
        fav_stylist = {'name': name, 'count': count}
    else:
        fav_stylist = {'name': '-', 'count': 0}
        
    #Top service
    service_names = [a['service_name'] for a in completed_appointments]
    service_counter = Counter(service_names)
    if service_counter:
        name, count = service_counter.most_common(1)[0]
        top_service = {'name': name, 'count': count}
    else:
        top_service = {'name': "-", 'count': 0}
        
    ##Filter bar
    
    #stylist
    stylists = get_all_staff()

    #service
    services = get_all_services()

    return render_template(
        "customer/customer_history.html",
        total_visits=total_visits,
        total_spent=total_spent,
        fav_stylist=fav_stylist,
        top_service=top_service,
        appointments=appointments,
        invoices=invoices,
        stylists=stylists,
        services=services
    )

# Thêm vào import của routes.py:
# from app.database.db import get_invoice_detail_by_id

@main.route("/customer/history/invoice/<int:invoice_id>")
@customer_login_required
def invoice_detail(invoice_id):
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for('main.customer_history'))

    invoice = get_invoice_detail_by_id(invoice_id)
    if not invoice:
        flash("Invoice not found!", "error")
        return redirect(url_for('main.customer_history'))

    # Bảo vệ: chỉ cho xem invoice của chính mình
    if invoice["customer_id"] != customer["id"]:
        flash("Invoice not found!", "error")
        return redirect(url_for('main.customer_history'))

    # Format date/time để hiển thị
    booking_date_obj = datetime.strptime(invoice["booking_date"], "%Y-%m-%d")
    booking_date_display = booking_date_obj.strftime("%B %d, %Y")   # October 02, 2025

    issued_at_obj = datetime.strptime(invoice["issued_at"], "%Y-%m-%d %H:%M:%S")
    issued_at_display = issued_at_obj.strftime("%B %d, %Y")

    start_time_display = format_booking_time(invoice["start_time"])  # 10:00 AM
    end_time_display = format_booking_time(invoice["end_time"])      # 10:45 AM

    # Initials cho stylist avatar
    name_parts = invoice["staff_name"].split()
    staff_initials = "".join(p[0].upper() for p in name_parts[:2])

    return render_template(
        "/customer/invoice_detail.html",
        invoice=invoice,
        booking_date_display=booking_date_display,
        issued_at_display=issued_at_display,
        start_time_display=start_time_display,
        end_time_display=end_time_display,
        staff_initials=staff_initials,
    )

@main.route("/customer/history/download-invoice_id=<int:invoice_id>")
@customer_login_required
def download_invoice(invoice_id):
    return render_template("customer/coming_soon.html", feature_name="Download Invoice")

def _redirect_to_stripe(booking_id, service_id, fallback_endpoint):
    """Tạo Stripe Checkout session cho booking online và redirect khách sang Stripe.
    Nếu lỗi -> flash + quay lại trang đặt lịch."""
    booking = get_booking_by_id(booking_id)
    service = get_service_by_id(service_id)
    try:
        checkout_url = create_booking_checkout_session(
            booking, service,
            success_url=url_for('main.payment_success', _external=True),
            cancel_url=url_for('main.payment_cancel', _external=True),
        )
    except Exception as e:
        print(f"[payment] create session failed: {e}")
        flash("Không tạo được phiên thanh toán. Vui lòng thử lại.", "error")
        return redirect(url_for(fallback_endpoint))
    return redirect(checkout_url)


@main.route("/customer/create-booking", methods=['POST'])
@customer_login_required
def create_customer_booking():
    
    #User data
    user_id = session.get("user_id")
    if not user_id:
        flash("Something went wrong. Please login again!", "error")
        return redirect(url_for('main.customer_dashboard'))

    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found. Please login again!", "error")
        return redirect(url_for('main.login'))

    service_id_raw = request.form.get("service_id", "").strip()
    booking_date_raw = request.form.get("booking_date", "").strip()
    slot_raw = request.form.get("start_time", "").strip()

    if not service_id_raw or not booking_date_raw or not slot_raw:
        flash("Please select a service, date, and time slot before confirming.", "error")
        return redirect(url_for('main.customer_booking'))

    #Parse form
    data = BookingService.parse_form(request.form)

    booking_date = data["booking_date"]
    note = data["note"]
    service_id = int(data["service_id"])
    booking_slot = data["slot"]
    staff_id = int(data["staff_id"])
    

    service = get_service_by_id(data["service_id"])
    if not service:
        flash("Service not found. Please try again.", "error")
        return redirect(url_for('main.customer_booking'))
    service_duration = service["duration_minutes"]
    start_time, end_time = BookingService.parse_slot(booking_date, booking_slot, service_duration)

    customer_id = int(customer["id"])
    customer_email = customer['email']

    try:
        staff = BookingService.pick_staff(
            staff_id,
            service_id,
            booking_date,
            start_time,
            end_time
        )
    except BookingValidatorError as e:
        flash(str(e), "error")
        return redirect(url_for('main.customer_booking'))
    staff_id = staff["id"]

    # Online: tạo booking 'unverified' rồi chuyển sang Stripe (bỏ qua OTP; thanh
    # toán thành công sẽ tự confirm qua webhook).
    if data["payment_method"] == "online":
        booking_id = create_booking(customer_id, staff_id, service_id,
                                    booking_date, start_time, end_time,
                                    "unverified", note, "online")
        session["booking_id"] = booking_id  # để /success hiển thị chi tiết sau khi trả tiền
        return _redirect_to_stripe(booking_id, service_id, 'main.customer_booking')

    booking_id, verification_id = BookingService.create(
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        note,
        customer_email,
        data["payment_method"]
    )

    session["booking_id"] = booking_id
    session["verify_context"] = {
        "type": "booking",
        "booking_id": booking_id,
        "email": customer["email"],
        "verification_id": verification_id
    }

    return redirect(url_for('main.email_verification'))

@main.route("/customer/upgrade", methods=["POST"])
@customer_login_required
def upgrade_plan():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    tier_name = request.form.get("tier_name", "").strip()
    if not tier_name:
        flash("Invalid plan selected.", "error")
        return redirect(url_for("main.tier_benefits"))

    tier = get_tier_by_name(tier_name)
    if not tier:
        flash("Plan not found.", "error")
        return redirect(url_for("main.tier_benefits"))

    active_subs = get_active_subscription_rows(customer["id"])

    # Tier miễn phí (price = 0, vd Silver) -> không qua Stripe. Đang có sub trả phí
    # thì hẹn hủy TẤT CẢ (giữ quyền lợi tới hết kỳ, sau đó tự về Silver).
    if not tier["price"]:
        renewing = [s for s in active_subs if not s["cancel_at_period_end"]]
        if renewing:
            for s in renewing:
                try:
                    cancel_subscription(s["stripe_subscription_id"])
                except Exception as e:
                    print(f"[payment] cancel on downgrade failed: {e}")
            flash("Your paid membership will stop renewing and revert to Silver at the period end.", "success")
        else:
            flash("You're on the Silver plan.", "success")
        return redirect(url_for("main.tier_benefits"))

    # Tier trả phí nhưng chưa cấu hình Stripe Price -> lỗi cấu hình, báo rõ (thay vì
    # âm thầm coi như free). Thường do quên chạy setup_stripe_prices sau khi reset DB.
    if not tier["stripe_price_id"]:
        print(f"[payment] tier {tier['name']} thieu stripe_price_id -> chay: python -m app.database.setup_stripe_prices")
        flash("This plan isn't available for online payment right now. Please try again later.", "error")
        return redirect(url_for("main.tier_benefits"))

    # Đang gia hạn đúng tier này rồi -> thôi (khỏi mua trùng).
    if any(s["tier_id"] == tier["id"] and not s["cancel_at_period_end"] for s in active_subs):
        flash(f"You're already subscribed to {tier['name']}.", "success")
        return redirect(url_for("main.tier_benefits"))

    # Đổi tier = MUA MỚI: luôn tạo Checkout cho gói mới (kể cả đang có sub khác).
    # Gói cũ sẽ bị hủy gia hạn SAU KHI thanh toán mới thành công (trong fulfillment),
    # không refund gói cũ (giữ tới hết kỳ).
    try:
        checkout_url = create_subscription_checkout_session(
            customer, tier,
            success_url=url_for('main.payment_success', _external=True),
            cancel_url=url_for('main.payment_cancel', _external=True),
        )
    except Exception as e:
        print(f"[payment] create subscription session failed: {e}")
        flash("Could not start checkout. Please try again.", "error")
        return redirect(url_for("main.tier_benefits"))
    return redirect(checkout_url)


@main.route("/membership/cancel", methods=["POST"])
@customer_login_required
def cancel_membership():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    sub_row = get_customer_subscription_row(customer["id"])
    if not sub_row:
        flash("No active subscription to cancel.", "error")
        return redirect(url_for("main.tier_benefits"))
    try:
        cancel_subscription(sub_row["stripe_subscription_id"])
        flash("Your membership will not renew. You keep your benefits until the current period ends.", "success")
    except Exception as e:
        print(f"[payment] cancel failed: {e}")
        flash("Could not cancel your membership. Please try again.", "error")
    return redirect(url_for("main.tier_benefits"))

@main.route("/customer/redeem-reward", methods=["POST"])
@customer_login_required
def redeem_reward_route():
    is_json = request.is_json

    def _err(msg):
        if is_json:
            return jsonify({"success": False, "message": msg})
        flash(msg, "error")
        return redirect(url_for("main.customer_loyalty_points"))

    user_id  = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        if is_json:
            return jsonify({"success": False, "message": "Customer profile not found."})
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    payload  = (request.get_json(silent=True) or {}) if is_json else {}
    raw_id   = str(payload.get("reward_id", "")) if is_json else request.form.get("reward_id", "").strip()


    if not raw_id:
        return _err("Invalid reward.")
    try:
        reward_id = int(raw_id)
    except ValueError:
        return _err("Invalid reward.")

    customer_id = customer["id"]
    balance     = get_loyalty_balance(customer_id)

    raw_rewards = get_active_rewards()
    reward = next((dict(r) for r in raw_rewards if r["id"] == reward_id), None)
    if not reward:
        return _err("Reward not found.")

    if balance < reward["cost"]:
        return _err("Not enough points.")

    if reward["stock"] is not None and reward["stock"] <= 0:
        return _err("This reward is out of stock.")

    status = get_customer_reward_status(customer_id, reward_id)
    redeem_count     = status["redeem_count"] or 0
    last_redeemed_at = status["last_redeemed_at"]

    max_redeems       = reward["max_redeems_per_customer"]
    cooldown_days_val = reward["cooldown_days"]
    if max_redeems:
        cycles_completed = redeem_count // max_redeems
        redeems_in_cycle = redeem_count % max_redeems
        if cycles_completed > 0 and redeems_in_cycle == 0:
            if cooldown_days_val and last_redeemed_at:
                try:
                    last_dt  = datetime.strptime(last_redeemed_at, "%Y-%m-%d %H:%M:%S")
                    reset_dt = last_dt + timedelta(days=cooldown_days_val)
                    if now_helsinki() < reset_dt:
                        remaining = max((reset_dt - now_helsinki()).days, 1)
                        return _err(f"This reward resets in {remaining} day(s).")
                except (ValueError, TypeError):
                    pass
            else:
                return _err("You've reached the redeem limit for this reward.")

    redeem_reward(customer_id, reward_id, reward["cost"], reward["name"])
    flash(f"Successfully redeemed: {reward['name']}!", "success")
    if is_json:
        return jsonify({"success": True})
    return redirect(url_for("main.customer_loyalty_points"))

@main.route("/customer/refer-a-friend")
@customer_login_required
def refer_a_friend():
    return render_template("customer/coming_soon.html", feature_name="Refer a Friend")

@main.route("/customer/tier-benefits")
@customer_login_required
def tier_benefits():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))

    # "Current plan" = tier hiện tại (gói active mới nhất) — thống nhất với loyalty
    # page và hệ số điểm qua get_customer_current_tier.
    current = get_customer_current_tier(customer["id"])
    current_plan = current["name"].lower() if current else "silver"

    sub_row = get_customer_subscription_row(customer["id"])  # newest active sub (cho banner)
    has_subscription = sub_row is not None
    will_cancel = bool(sub_row and sub_row["cancel_at_period_end"])
    is_past_due = bool(sub_row and sub_row["subscription_status"] == "past_due")
    sub_plan = None
    sub_expires = None
    if sub_row:
        sub_tier = get_tier_by_id(sub_row["tier_id"])
        sub_plan = sub_tier["name"] if sub_tier else None
        try:
            sub_expires = datetime.strptime(sub_row["expires_at"], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
        except (ValueError, TypeError):
            sub_expires = sub_row["expires_at"]

    return render_template(
        "customer/customer_membership.html",
        current_plan=current_plan,
        has_subscription=has_subscription,
        will_cancel=will_cancel,
        is_past_due=is_past_due,
        sub_plan=sub_plan,
        sub_expires=sub_expires,
    )


@main.route("/membership/billing-portal", methods=["POST"])
@customer_login_required
def billing_portal():
    customer = get_customer_by_user_id(session.get("user_id"))
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for("main.login"))
    if not customer["stripe_customer_id"]:
        flash("No billing account found.", "error")
        return redirect(url_for("main.tier_benefits"))
    try:
        url = create_billing_portal_session(
            customer["stripe_customer_id"],
            return_url=url_for("main.tier_benefits", _external=True),
        )
    except Exception as e:
        print(f"[payment] billing portal failed: {e}")
        flash("Could not open the billing portal. Please try again later.", "error")
        return redirect(url_for("main.tier_benefits"))
    return redirect(url)

@main.route("/customer/rewards")
@customer_login_required
def all_rewards():
    return render_template("customer/coming_soon.html", feature_name="All Rewards")

_MISSION_SLOT_URLS = {
    "review":        lambda: url_for("main.customer_history"),
    "referral":      lambda: url_for("main.refer_a_friend"),
    "first_booking": lambda: url_for("main.customer_booking"),
}
_MISSION_SLOT_BG = {
    "review":        "linear-gradient(135deg, #fef3c7 0%, #fde68a 55%, #f59e0b 100%)",
    "referral":      "linear-gradient(135deg, #ede9fe 0%, #c4b5fd 55%, #8b5cf6 100%)",
    "first_booking": "linear-gradient(135deg, #d1fae5 0%, #6ee7b7 55%, #059669 100%)",
}
_MISSION_SLOT_CTA = {"review": "Start", "referral": "Start", "first_booking": "Claim"}

@main.route("/customer/loyalty-points")
@customer_login_required
def customer_loyalty_points():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Customer profile not found!", "error")
        return redirect(url_for('main.login'))

    customer_id = customer["id"]
    balance = get_loyalty_balance(customer_id)

    _tier_css = {
        "diamond": ("tier-diamond", "badge-diamond", "fill-diamond"),
        "gold":    ("tier-gold",    "badge-gold",    "fill-gold"),
        "silver":  ("tier-silver",  "badge-silver",  ""),
    }
    active_tier = get_customer_current_tier(customer_id)
    if active_tier:
        tier_name = active_tier["name"]
        tier_class, badge_class, fill_class = _tier_css.get(tier_name.lower(), ("tier-silver", "badge-silver", ""))
    else:
        tier_name, tier_class, badge_class, fill_class = "Silver", "tier-silver", "badge-silver", ""

    raw_rewards = get_active_rewards()
    rewards = []
    for r in raw_rewards:
        r = dict(r)
        status = get_customer_reward_status(customer_id, r["id"])
        redeem_count     = status["redeem_count"] or 0
        last_redeemed_at = status["last_redeemed_at"]

        max_redeems      = r["max_redeems_per_customer"]
        cooldown_days_val = r["cooldown_days"]

        not_enough_pts = balance < r["cost"]
        out_of_stock   = r["stock"] is not None and r["stock"] <= 0

        hit_limit          = False
        cooldown_remaining = None
        redeems_in_cycle   = redeem_count
        redeems_left       = None

        if max_redeems:
            cycles_completed = redeem_count // max_redeems
            redeems_in_cycle = redeem_count % max_redeems

            if cycles_completed > 0 and redeems_in_cycle == 0:
                # User just completed a full cycle — check if cooldown passed
                if cooldown_days_val and last_redeemed_at:
                    try:
                        last_dt   = datetime.strptime(last_redeemed_at, "%Y-%m-%d %H:%M:%S")
                        reset_dt  = last_dt + timedelta(days=cooldown_days_val)
                        if now_helsinki() < reset_dt:
                            hit_limit          = True
                            cooldown_remaining = max((reset_dt - now_helsinki()).days, 1)
                    except (ValueError, TypeError):
                        pass
                else:
                    hit_limit = True  # no cooldown → permanently at limit

            redeems_left = max_redeems - redeems_in_cycle if not hit_limit else 0

        redeemable = not any([not_enough_pts, out_of_stock, hit_limit])

        if not_enough_pts:                      lock_reason = "points"
        elif out_of_stock:                      lock_reason = "stock"
        elif hit_limit and cooldown_remaining:  lock_reason = "cooldown"
        elif hit_limit:                         lock_reason = "limit"
        else:                                   lock_reason = None

        rewards.append({
            "id":                r["id"],
            "name":              r["name"],
            "desc":              r["description"] or "",
            "pts":               r["cost"],
            "locked":            not redeemable,
            "img":               url_for("static", filename=f"uploads/rewards/{r['banner_image']}") if r["banner_image"] else "",
            "available":         redeemable,
            "lock_reason":       lock_reason,
            "cooldown_remaining": cooldown_remaining,
            "redeems_left":      redeems_left,
            "stock_left":        r["stock"],
        })

    next_locked = next((r for r in rewards if r["lock_reason"] == "points"), None)
    if next_locked:
        next_reward_name = next_locked["name"]
        next_reward_pts  = next_locked["pts"] or 1
        progress_pct = min(100, int(balance / next_reward_pts * 100))
    else:
        next_reward_name = "All rewards unlocked!"
        next_reward_pts  = balance or 1
        progress_pct = 100

    raw_history = get_loyalty_history(customer_id)
    history = []
    for row in raw_history:
        pts = row["points"]
        try:
            dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            date_str = row["created_at"]
        h_type = "earn" if pts > 0 else "redeem"
        history.append({
            "desc": row["note"] or row["source"].replace("_", " ").title(),
            "date": f"{'Earned on' if h_type == 'earn' else 'Redeemed on'} {date_str}",
            "pts": f"+{pts} pts" if pts > 0 else f"{pts} pts",
            "type": h_type,
            "ref": row["source"].replace("_", " ").title(),
        })

    first_booking_claimed = has_source_award(customer_id, "first_booking")
    pending_review = has_pending_review(customer_id)

    missions = []
    for m in get_mission_slides():
        slot = m["slot_key"]
        claimed, claimed_label = False, None
        if slot == "first_booking" and first_booking_claimed:
            claimed, claimed_label = True, "✓ Claimed"
        elif slot == "review" and not pending_review:
            claimed, claimed_label = True, "✓ All Reviewed"
        missions.append({
            "icon":          m["icon"],
            "name":          m["title"],
            "pts":           m["pts_label"],
            "img":           _resolve_carousel_image(m["image"]),
            "bg":            _MISSION_SLOT_BG.get(slot),
            "url":           _MISSION_SLOT_URLS[slot](),
            "cta":           _MISSION_SLOT_CTA.get(slot, "Start"),
            "claimed":       claimed,
            "claimed_label": claimed_label,
        })

    raw_vouchers = get_customer_vouchers(customer_id)
    vouchers = []
    for v in raw_vouchers:
        try:
            dt = datetime.strptime(v["redeemed_at"], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            date_str = v["redeemed_at"] or "—"
        vouchers.append({
            "name":        v["name"],
            "desc":        v["description"] or "",
            "date":        f"Redeemed on {date_str}",
            "redeemed_at": date_str,
            "code":        v["voucher_code"],
            "status":      "active",
            "icon":        "💅",
            "pts":         v["points_spent"],
            "expires_at":  "—",
        })

    return render_template(
        '/customer/loyalty_points.html',
        balance=balance,
        tier_name=tier_name,
        tier_class=tier_class,
        badge_class=badge_class,
        fill_class=fill_class,
        next_reward_name=next_reward_name,
        next_reward_pts=next_reward_pts,
        progress_pct=progress_pct,
        rewards=rewards,
        history=history,
        vouchers=vouchers,
        first_booking_claimed=first_booking_claimed,
        pending_review=pending_review,
        missions=missions,
    )

@main.route("/customer/loyalty-points/redeem-terms")
@customer_login_required
def redeem_terms():
    return render_template("customer/coming_soon.html", feature_name="Redeem Terms")

#====================================
#               Staff
#====================================

@main.route('/staff/login', methods=['POST', 'GET'])
def staff_login():
    if request.method == "GET":
        return render_template("staff/login.html")
    
    ip = request.remote_addr
    now = time.time()
    attempt = _failed_logins.get(ip, {"count": 0, "blocked_until": 0})
    if now < attempt["blocked_until"]:
        remaining = int((attempt["blocked_until"] - now) / 60) + 1
        flash(f"Too many failed attempts. Try again in {remaining} minute(s).", "error")
        return redirect(url_for("main.staff_login"))

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password","")

    def _record_failure():
        attempt["count"] += 1
        if attempt["count"] >= _MAX_LOGIN_ATTEMPTS:
            attempt["blocked_until"] = time.time() + _LOGIN_LOCKOUT
            attempt["count"] = 0
        _failed_logins[ip] = attempt

    if not email or not password:
        flash("Please enter email or password!", "error")
        return redirect(url_for("main.staff_login"))

    user = get_user_by_email(email)

    if not user:
        _record_failure()
        flash("Invalid email or password!", "error")
        return redirect(url_for("main.staff_login"))

    user_id = user['id']

    if not check_password_hash(user["password_hash"], password):
        _record_failure()
        flash("Invalid email or password!", "error")
        return redirect(url_for("main.staff_login"))

    if user["role"] not in ("staff", "admin"):
        flash("Please use the customer login portal", "error")
        return redirect(url_for("main.login"))

    _failed_logins.pop(ip, None)
    session.clear()
    session["user_id"] = user_id
    session["role"] = user["role"]
    session["user_email"] = user["email"]

    if user["role"] == "staff":
        staff = get_staff_by_user_id(user_id)
        if not staff:
            flash("Staff profile not found!", "error")
            return redirect(url_for("main.staff_login"))

        session["staff_id"] = staff['id']
        flash(f"Login successfully. Welcome {staff['full_name']}!", "success")
        return redirect(url_for("main.staff_dashboard"))

    if user["role"] == "admin":
        staff = get_staff_by_user_id(user_id)
        session["admin_name"] = staff["full_name"] if staff else "Admin"
        session["admin_email"] = user["email"]
        session["admin_last_activity"] = time.time()
        flash(f"Login successfully. Welcome master!", "success")
        return redirect(url_for("main.admin_dashboard"))
    
    flash("something went wrong :(", "error")
    return redirect(url_for("main.staff_login"))

_DOW_VI = {0: "Thứ hai", 1: "Thứ ba", 2: "Thứ tư", 3: "Thứ năm",
           4: "Thứ sáu", 5: "Thứ bảy", 6: "Chủ nhật"}

_STATUS_BORDER = {
    "in-progress": "#C084A0", "confirmed": "#60A5FA",
    "done": "#4ADE80", "pending": "#F59E0B", "cancelled": "#D4BAB0",
    "no-show": "#9B4444",
}
_STATUS_BADGE = {
    "pending":     ("b-pending", "Chờ xác nhận"),
    "confirmed":   ("b-confirm", "Đã xác nhận"),
    "in-progress": ("b-inprog", "Đang thực hiện"),
    "done":        ("b-done", "Hoàn thành"),
    "cancelled":   ("b-cancel", "Đã hủy"),
    "no-show":     ("b-noshow", "Không đến"),
}
_EMPTY_SCOPE = {
    "today":      "hôm nay",
    "week":       "trong tuần này",
    "month":      "trong tháng này",
    "last_month": "trong tháng trước",
    "all":        "",
}

def _dow_vi(date_str):
    try:
        return _DOW_VI[datetime.strptime(date_str, "%Y-%m-%d").weekday()]
    except (ValueError, TypeError):
        return ""

def _fmt_ddmmyyyy(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return date_str or ""

def _enrich_staff_booking(r):
    """Suy ra payment/badge/border cho 1 booking từ dữ liệu invoices (LEFT JOIN)."""
    method = r["invoice_method"]
    is_paid = 1 if r["invoice_status"] == "paid" else 0
    if method == "cash":
        pay_method = "cash"
        pay_tag = ("pt-paid", "Tiền mặt - đã thanh toán") if is_paid else ("pt-unpaid", "Tiền mặt - chưa thanh toán")
    elif method:
        pay_method, pay_tag = "online", ("pt-online", "Online")
    else:
        pay_method, pay_tag = "", None
    badge_class, badge_label = _STATUS_BADGE.get(r["status"], ("b-cancel", r["status"]))
    return {
        **r,
        "pay_method": pay_method,
        "is_paid": is_paid,
        "pay_tag_class": pay_tag[0] if pay_tag else "",
        "pay_tag_label": pay_tag[1] if pay_tag else "",
        "badge_class": badge_class,
        "badge_label": badge_label,
        "border": _STATUS_BORDER.get(r["status"], "#D4BAB0"),
        "faded": r["status"] == "done",
        "code": "BK-" + (r["booking_date"] or "").replace("-", "") + "-" + f'{r["id"]:03d}',
        "start": (r["start_time"] or "")[:5],
        "end": (r["end_time"] or "")[:5],
        "date_display": _fmt_ddmmyyyy(r["booking_date"]),
    }

def _enrich_history_booking(r):
    """Suy ra payment/badge cho 1 booking trang 'Lịch sử' (chỉ done/cancelled).
    Khác _enrich_staff_booking: cancelled -> pt-na, và thu nhập để trống nếu cancelled."""
    method = r["invoice_method"]
    is_paid = 1 if r["invoice_status"] == "paid" else 0
    if r["status"] == "cancelled":
        pay_tag_class, pay_tag_label = "pt-na", "—"
    elif method == "cash":
        pay_tag_class, pay_tag_label = ("pt-paid", "Tiền mặt – đã thanh toán") if is_paid else ("pt-unpaid", "Tiền mặt – chưa thanh toán")
    elif method:
        pay_tag_class, pay_tag_label = "pt-online", "Online"
    else:
        pay_tag_class, pay_tag_label = "pt-na", "—"
    badge_class, badge_label = ("b-done", "Hoàn thành") if r["status"] == "done" else ("b-cancelled", "Đã hủy")
    is_cancelled = r["status"] == "cancelled"
    return {
        **r,
        "pay_method": method or "",
        "is_paid": is_paid,
        "pay_tag_class": pay_tag_class,
        "pay_tag_label": pay_tag_label,
        "badge_class": badge_class,
        "badge_label": badge_label,
        "code": "BK-" + (r["booking_date"] or "").replace("-", "") + "-" + f'{r["id"]:03d}',
        "start": (r["start_time"] or "")[:5],
        "end": (r["end_time"] or "")[:5],
        "date_display": _fmt_ddmmyyyy(r["booking_date"]),
        "hourly_display": "" if is_cancelled else f'{r["staff_hourly_earning"] or 0:.2f}',
        "commission_display": "" if is_cancelled else f'{r["staff_commission"] or 0:.2f}',
        "total_income_display": "" if is_cancelled else f'{r["staff_total_earning"] or 0:.2f}',
    }

def _month_display_vi(ym):
    try:
        y, m = ym.split("-")
        return f"Tháng {int(m)}/{y}"
    except (ValueError, AttributeError):
        return ym

# Logic hoàn tất booking đã chuyển sang app/services/booking_service.complete_booking_txn
# (nguồn chân lý duy nhất, dùng chung cho staff portal / admin / dev_tools).
# Giữ alias để các call-site legacy trong file này không phải đổi.
_complete_booking_txn = complete_booking_txn

@main.route("/staff")
@staff_required
def staff_dashboard():
    auto_expire_bookings()

    current_staff = _get_current_staff()
    if not current_staff:
        flash("Không tìm thấy hồ sơ nhân viên.", "error")
        return redirect(url_for("main.staff_login"))

    today = today_helsinki()
    today_str = today.strftime("%Y-%m-%d")
    preset = request.args.get("preset", "today")
    active_status = request.args.get("status", "all")

    date_from = date_to = None
    if preset == "today":
        date_from = date_to = today
    elif preset == "week":
        date_from = today - timedelta(days=today.weekday())
        date_to = date_from + timedelta(days=6)
    elif preset == "month":
        date_from = today.replace(day=1)
        date_to = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif preset == "last_month":
        first_this = today.replace(day=1)
        date_to = first_this - timedelta(days=1)
        date_from = date_to.replace(day=1)
    elif preset == "all":
        date_from = date_to = None
    elif preset == "custom":
        try:
            date_from = datetime.strptime(request.args.get("date_from", ""), "%Y-%m-%d").date()
        except ValueError:
            date_from = today
        try:
            date_to = datetime.strptime(request.args.get("date_to", ""), "%Y-%m-%d").date()
        except ValueError:
            date_to = today
        if date_to < date_from:
            date_from, date_to = date_to, date_from
    else:
        preset, date_from, date_to = "today", today, today

    df = date_from.strftime("%Y-%m-%d") if date_from else None
    dt = date_to.strftime("%Y-%m-%d") if date_to else None

    # scope hiển thị cho empty-state theo date range đang chọn
    if preset == "custom":
        empty_scope = (f"vào ngày {_fmt_ddmmyyyy(df)}" if df == dt
                       else f"từ {_fmt_ddmmyyyy(df)} đến {_fmt_ddmmyyyy(dt)}")
    else:
        empty_scope = _EMPTY_SCOPE.get(preset, "")

    all_bookings = [_enrich_staff_booking(r)
                    for r in get_staff_bookings_range(current_staff["id"], df, dt)]

    now_hm = now_helsinki().strftime("%H:%M")
    def _is_upcoming(b):
        # confirmed = chưa được staff bắt đầu và chưa quá hạn (auto_expire_bookings
        # đã lo phần no-show), nên chỉ cần check status là đủ.
        return b["status"] == "confirmed"

    for b in all_bookings:
        # confirmed + đã tới giờ start_time hôm nay -> staff được phép bấm "Bắt đầu làm"
        b["can_start"] = (b["status"] == "confirmed"
                           and b["booking_date"] == today_str
                           and (b["start"] or "") <= now_hm)

    stats = {
        "total": len(all_bookings),
        "upcoming": sum(1 for b in all_bookings if _is_upcoming(b)),
        "in_progress": sum(1 for b in all_bookings if b["status"] == "in-progress"),
        "done": sum(1 for b in all_bookings if b["status"] == "done"),
        "pending_payment": sum(1 for b in all_bookings
                               if b["status"] == "done" and b["pay_method"] == "cash" and b["is_paid"] == 0),
    }

    if active_status != "all":
        list_bookings = [b for b in all_bookings if b["status"] == active_status]
    else:
        list_bookings = all_bookings

    # booking confirmed sắp tới gần nhất trong danh sách đang hiển thị (đã sort theo ngày/giờ ASC)
    next_upcoming_id = next((b["id"] for b in list_bookings if _is_upcoming(b)), None)

    is_multi_day = (preset == "all") or (date_from != date_to)

    grouped = {}
    for b in list_bookings:
        grouped.setdefault(b["booking_date"], []).append(b)

    days = []
    if is_multi_day:
        if preset == "all":
            date_keys = sorted(grouped.keys())
        else:
            date_keys, d = [], date_from
            while d <= date_to:
                date_keys.append(d.strftime("%Y-%m-%d"))
                d += timedelta(days=1)
        for k in date_keys:
            days.append({
                "date_str": k, "date_display": _fmt_ddmmyyyy(k), "dow_vi": _dow_vi(k),
                "is_today": k == today_str, "bookings": grouped.get(k, []),
            })
    else:
        the_date = df or today_str
        days.append({
            "date_str": the_date, "date_display": _fmt_ddmmyyyy(the_date), "dow_vi": _dow_vi(the_date),
            "is_today": the_date == today_str, "bookings": list_bookings,
        })

    return render_template(
        "/staff/staff_bookings.html",
        current_staff=current_staff,
        staff_name=current_staff["name"],
        now_display=f"{_dow_vi(today_str)}, {today.strftime('%d/%m/%Y')}",
        stats=stats,
        active_preset=preset,
        active_status=active_status,
        date_from_val=df or "",
        date_to_val=dt or "",
        today_str=today_str,
        is_multi_day=is_multi_day,
        days=days,
        has_any=len(list_bookings) > 0,
        next_upcoming_id=next_upcoming_id,
        empty_scope=empty_scope,
    )

@main.route("/staff/history")
@staff_required
def staff_history():
    current_staff = _get_current_staff()
    if not current_staff:
        flash("Không tìm thấy hồ sơ nhân viên.", "error")
        return redirect(url_for("main.staff_login"))

    today = today_helsinki()
    today_str = today.strftime("%Y-%m-%d")

    month_options = get_staff_history_months(current_staff["id"])

    if "month" in request.args:
        active_month = request.args.get("month", "")
    else:
        current_month = today.strftime("%Y-%m")
        active_month = current_month if current_month in month_options else ""

    active_search = request.args.get("search", "").strip()
    active_status = request.args.get("status", "all")

    stats = get_staff_history_stats(current_staff["id"], today_str)

    rows = get_staff_history(
        current_staff["id"],
        month=active_month,
        search=active_search,
        status=active_status,
        today_str=today_str,
    )
    bookings = [_enrich_history_booking(r) for r in rows]

    grouped_bookings = {}
    for b in bookings:
        ym = (b["booking_date"] or "")[:7]
        grouped_bookings.setdefault(ym, []).append(b)

    month_keys = sorted(grouped_bookings.keys(), reverse=True)
    month_display = {ym: _month_display_vi(ym) for ym in set(month_options) | set(month_keys)}

    return render_template(
        "/staff/staff_history.html",
        current_staff=current_staff,
        grouped_bookings=grouped_bookings,
        month_keys=month_keys,
        month_display=month_display,
        month_options=month_options,
        stats=stats,
        active_month=active_month,
        active_search=active_search,
        active_status=active_status,
        today_str=today_str,
        now=now_helsinki(),
    )

@main.route("/staff/profile")
@staff_required
def staff_profile():
    current_staff = _get_current_staff()
    stats = get_staff_profile_stats(current_staff["id"])
    return render_template("/staff/staff_profile.html", current_staff=current_staff, stats=stats, now=now_helsinki())


@main.route("/staff/profile/update-avatar", methods=["POST"])
@staff_required
def staff_update_avatar():
    current_staff = _get_current_staff()
    file = request.files.get("avatar")

    try:
        filename = _save_staff_image(file)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.staff_profile"))

    if not filename:
        flash("Vui lòng chọn ảnh.", "error")
        return redirect(url_for("main.staff_profile"))

    update_staff_photo(current_staff["id"], filename)
    flash("Đã cập nhật ảnh đại diện.", "success")
    return redirect(url_for("main.staff_profile"))


@main.route("/staff/profile/send-otp", methods=["POST"])
@staff_required
def staff_send_pw_otp():
    current_staff = _get_current_staff()
    expires_at = (now_helsinki() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    code = generate_verification_code()
    verification_id = create_verification(code, "password_change", expires_at)
    send_verification_email(current_staff["email"], code, "password_change")
    session["staff_pw_verification_id"] = verification_id
    return jsonify({"ok": True})


@main.route("/staff/profile/change-password", methods=["POST"])
@staff_required
def staff_change_password():
    current_staff = _get_current_staff()

    verification_id = session.get("staff_pw_verification_id")
    if not verification_id:
        flash("Phiên xác thực đã hết hạn. Vui lòng yêu cầu mã mới.", "error")
        return redirect(url_for("main.staff_profile"))

    user_code = request.form.get("verification_code", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    verification = get_verification_by_id(verification_id)
    if not verification:
        flash("Mã xác thực đã hết hạn. Vui lòng yêu cầu mã mới.", "error")
        session.pop("staff_pw_verification_id", None)
        return redirect(url_for("main.staff_profile"))

    if user_code != verification["verification_code"]:
        flash("Mã xác thực không đúng.", "error")
        return redirect(url_for("main.staff_profile"))

    if len(new_password) < 8:
        flash("Mật khẩu mới phải có ít nhất 8 ký tự.", "error")
        return redirect(url_for("main.staff_profile"))

    if new_password != confirm_password:
        flash("Mật khẩu xác nhận không khớp.", "error")
        return redirect(url_for("main.staff_profile"))

    update_verification(verification_id, current_staff["id"], 1)
    update_user_password(current_staff["user_id"], generate_password_hash(new_password))
    session.pop("staff_pw_verification_id", None)
    flash("Đổi mật khẩu thành công.", "success")
    return redirect(url_for("main.staff_profile"))

@main.route("/staff/booking/start", methods=["POST"])
@staff_required
def mark_in_progress():
    current_staff = _get_current_staff()
    booking_id = request.form.get("booking_id", type=int)
    booking = get_booking_by_id(booking_id) if booking_id else None

    now = now_helsinki()
    today_str = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")

    if (not booking or not current_staff
            or booking["staff_id"] != current_staff["id"]
            or booking["status"] != "confirmed"
            or not (booking["booking_date"] == today_str
                    and (booking["start_time"] or "")[:5] <= now_hm)):
        flash("Không có quyền thực hiện hành động này.", "error")
        return redirect(request.referrer or url_for("main.staff_dashboard"))

    update_status(booking_id, "in-progress")
    flash("Đã bắt đầu thực hiện dịch vụ.", "success")
    return redirect(request.referrer or url_for("main.staff_dashboard"))

@main.route("/staff/booking/done", methods=["POST"])
@staff_required
def mark_done():
    current_staff = _get_current_staff()
    booking_id = request.form.get("booking_id", type=int)
    booking = get_booking_by_id(booking_id) if booking_id else None

    if (not booking or not current_staff
            or booking["staff_id"] != current_staff["id"]
            or booking["status"] != "in-progress"):
        flash("Không có quyền thực hiện hành động này.", "error")
        return redirect(request.referrer or url_for("main.staff_dashboard"))

    if _complete_booking_txn(booking_id):
        flash("Đã đánh dấu hoàn thành.", "success")
    else:
        flash("Có lỗi xảy ra. Vui lòng thử lại.", "error")
    return redirect(request.referrer or url_for("main.staff_dashboard"))

@main.route("/staff/booking/paid", methods=["POST"])
@staff_required
def mark_paid():
    current_staff = _get_current_staff()
    booking_id = request.form.get("booking_id", type=int)
    booking = get_booking_by_id(booking_id) if booking_id else None
    invoice = get_invoice_by_booking(booking_id) if booking_id else None

    if (not booking or not current_staff
            or booking["staff_id"] != current_staff["id"]
            or not invoice or invoice["payment_method"] != "cash"
            or invoice["status"] == "paid"):
        flash("Không có quyền thực hiện hành động này.", "error")
        return redirect(request.referrer or url_for("main.staff_dashboard"))

    mark_invoice_paid(booking_id)
    flash("Đã xác nhận thanh toán.", "success")
    return redirect(request.referrer or url_for("main.staff_dashboard"))

@main.route("/staff/complete-booking/<int:booking_id>", methods=["POST"])
def complete_booking(booking_id):
    if session.get("role") not in ("staff", "admin"):
        flash("Unauthorized.", "error")
        return redirect(url_for("main.staff_login"))

    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Booking not found.", "error")
        return redirect(url_for("main.staff_dashboard"))

    if booking["status"] != "confirmed":
        flash("Only confirmed bookings can be marked as completed.", "error")
        return redirect(url_for("main.staff_dashboard"))

    if _complete_booking_txn(booking_id):
        flash("Booking marked as completed.", "success")
    else:
        flash("Something went wrong. Please try again.", "error")

    return redirect(url_for("main.staff_dashboard"))

#====================================
#               Admin
#====================================

##DASHBOARD
@main.route("/admin")
@admin_required
def admin_dashboard():
    auto_expire_bookings()
    today = today_helsinki()
    today_str = today.strftime("%Y-%m-%d")
    today_label = today.strftime("%A, %b %d")

    kpi = get_admin_kpis(today_str)

    _avatar_palette = [
        ("#e0e7ff", "#3730a3"), ("#fce7f3", "#9d174d"),
        ("#fef3c7", "#92400e"), ("#f3e8ff", "#6b21a8"),
        ("#dcfce7", "#166534"), ("#fee2e2", "#991b1b"),
    ]
    raw_appts = get_admin_today_appointments(today_str)
    today_appointments = []
    for i, a in enumerate(raw_appts):
        bg, fg = _avatar_palette[i % len(_avatar_palette)]
        parts = a["customer_name"].split()
        initials = "".join(p[0].upper() for p in parts[:2])
        today_appointments.append({
            "time": format_booking_time(a["start_time"]),
            "duration": f"{a['duration_minutes']} mins",
            "initials": initials,
            "avatar_bg": bg,
            "avatar_color": fg,
            "name": a["customer_name"],
            "service": a["service_name"],
            "staff": a["staff_name"],
            "status": a["status"],
        })

    _dot_colors = {
        "pending":     "#fca5a5",
        "confirmed":   "#6fb2fd",
        "in-progress": "#c4b5fd",
        "done":        "#6ee7b7",
        "cancelled":   "#cbd5e1",
        "no-show":     "#e4a3a3",
    }
    _activity_text = {
        "pending":     lambda r: f"<strong>{r['customer_name']}</strong> booked {r['service_name']}",
        "confirmed":   lambda r: f"Booking confirmed for <strong>{r['customer_name']}</strong>",
        "in-progress": lambda r: f"Service in progress for <strong>{r['customer_name']}</strong>",
        "done":        lambda r: f"<strong>{r['customer_name']}</strong> completed {r['service_name']}",
        "cancelled":   lambda r: f"<strong>{r['customer_name']}</strong> cancelled appointment",
        "no-show":     lambda r: f"<strong>{r['customer_name']}</strong> did not show up",
    }
    now = now_helsinki()
    activity_feed = []
    for r in get_admin_recent_activity(5):
        try:
            updated = datetime.strptime(r["updated_at"], "%Y-%m-%d %H:%M:%S")
            mins = int((now - updated).total_seconds() / 60)
            if mins < 2:
                time_str = "Just now"
            elif mins < 60:
                time_str = f"{mins} mins ago"
            elif mins < 1440:
                time_str = f"{mins // 60} hours ago"
            else:
                time_str = f"{mins // 1440} days ago"
        except (ValueError, TypeError):
            time_str = r["updated_at"]

        status = r["status"]
        text_fn = _activity_text.get(status, lambda r: f"Booking #{r['id']} updated")
        activity_feed.append({
            "dot_color": _dot_colors.get(status, "#cbd5e1"),
            "text": text_fn(r),
            "time": time_str,
        })

    revenue_chart = get_admin_revenue_chart(today_str)

    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")
    top_services = get_admin_top_services(month_start_str, today_str, limit=3)
    top_loyalty = get_admin_top_loyalty(limit=5)

    new_members = []
    for m in get_admin_new_members(today.strftime("%Y-%m"), limit=8):
        new_members.append({
            "full_name": m["full_name"],
            "email": m["email"],
            "joined_date": format_booking_date(m["created_at"]),
        })

    return render_template(
        "/admin/admin_dashboard.html",
        today_label=today_label,
        kpi=kpi,
        today_appointments=today_appointments,
        activity_feed=activity_feed,
        revenue_chart=revenue_chart,
        top_services=top_services,
        top_loyalty=top_loyalty,
        new_members=new_members,
    )

@main.route("/admin/bookings")
@admin_required
def admin_bookings():
    auto_expire_bookings()
    q          = request.args.get("q", "").strip()
    status     = request.args.get("status", "").strip()
    staff_id   = request.args.get("staff_id", "").strip()
    service_id = request.args.get("service_id", "").strip()
    date       = request.args.get("date", "").strip()
    page       = max(1, request.args.get("page", 1, type=int))
    per_page   = 15

    bookings, total = get_admin_bookings(
        q=q, status=status, staff_id=staff_id,
        service_id=service_id, date=date,
        page=page, per_page=per_page,
    )
    status_counts = get_booking_status_counts(
        q=q, staff_id=staff_id, service_id=service_id, date=date
    )
    pages = max(1, (total + per_page - 1) // per_page)
    pagination = {
        "start":    (page - 1) * per_page + 1 if total > 0 else 0,
        "end":      min(page * per_page, total),
        "total":    total,
        "page":     page,
        "pages":    pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }
    return render_template(
        "admin/admin_bookings.html",
        bookings=bookings,
        staff_list=get_active_staff(),
        service_list=get_all_services(),
        customer_list=get_all_customers(),
        status_counts=status_counts,
        pagination=pagination,
    )


@main.route("/admin/booking/<int:booking_id>/status", methods=["POST"])
@admin_required
def admin_update_booking_status(booking_id):
    new_status = request.form.get("status", "").strip()
    if new_status not in {"pending", "confirmed", "in-progress", "done", "cancelled", "no-show"}:
        flash("Trạng thái không hợp lệ.", "error")
        return redirect(url_for("main.admin_bookings"))

    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Booking không tồn tại.", "error")
        return redirect(request.referrer or url_for("main.admin_bookings"))
    old_status = booking["status"]

    # Rời khỏi 'done' → thu hồi side-effect (invoice + điểm + earnings) trước khi đổi status.
    if old_status == "done" and new_status != "done":
        revert_booking_txn(booking_id)

    if new_status == "cancelled":
        cancel_booking_with_reason(booking_id, None)
    elif new_status == "done":
        # 'done' phải đi qua transaction hoàn tất (invoice + earnings + loyalty),
        # không được ghi status trần bằng update_status. Bỏ qua nếu đã 'done'.
        if old_status != "done" and not complete_booking_txn(booking_id):
            flash("Không thể hoàn tất booking (thiếu dữ liệu dịch vụ/nhân viên).", "error")
            return redirect(request.referrer or url_for("main.admin_bookings"))
    else:
        update_status(booking_id, new_status)
    flash(f"Đã cập nhật trạng thái booking #{booking_id}.", "success")
    return redirect(request.referrer or url_for("main.admin_bookings"))


@main.route("/admin/booking/create", methods=["POST"])
@admin_required
def admin_create_booking():
    customer_id  = request.form.get("customer_id", type=int)
    service_id   = request.form.get("service_id", type=int)
    staff_id     = request.form.get("staff_id", type=int)
    booking_date = request.form.get("booking_date", "").strip()
    start_time   = request.form.get("start_time", "").strip()
    notes        = request.form.get("notes", "").strip() or None

    if not all([customer_id, service_id, staff_id, booking_date, start_time]):
        flash("Vui lòng điền đầy đủ thông tin.", "error")
        return redirect(url_for("main.admin_bookings"))

    service = get_service_by_id(service_id)
    if not service:
        flash("Dịch vụ không tồn tại.", "error")
        return redirect(url_for("main.admin_bookings"))

    start_dt = datetime.strptime(start_time, "%H:%M")
    end_time = (start_dt + timedelta(minutes=service["duration_minutes"])).strftime("%H:%M")

    if check_booking_conflict(staff_id, booking_date, start_time, end_time):
        flash("Stylist đã có lịch trong khung giờ này. Vui lòng chọn giờ khác.", "error")
        return redirect(url_for("main.admin_bookings"))

    create_booking(customer_id, staff_id, service_id, booking_date, start_time, end_time, "pending", notes, "cash")
    flash("Tạo booking thành công!", "success")
    return redirect(url_for("main.admin_bookings"))


@main.route("/admin/booking/<int:booking_id>/update", methods=["POST"])
@admin_required
def admin_update_booking(booking_id):
    staff_id     = request.form.get("staff_id", type=int)
    booking_date = request.form.get("booking_date", "").strip()
    start_time   = request.form.get("start_time", "").strip()
    notes        = request.form.get("notes", "").strip() or None

    if not all([staff_id, booking_date, start_time]):
        flash("Vui lòng điền đầy đủ thông tin.", "error")
        return redirect(url_for("main.admin_bookings"))

    booking = get_booking_by_id(booking_id)
    if not booking:
        flash("Booking không tồn tại.", "error")
        return redirect(url_for("main.admin_bookings"))

    service = get_service_by_id(booking["service_id"])
    start_dt = datetime.strptime(start_time, "%H:%M")
    end_time = (start_dt + timedelta(minutes=service["duration_minutes"])).strftime("%H:%M")

    update_booking_details(booking_id, staff_id, booking_date, start_time, end_time, notes)
    flash(f"Đã cập nhật booking #{booking_id}.", "success")
    return redirect(request.referrer or url_for("main.admin_bookings"))

@main.route("/admin/staffs")
@admin_required
def admin_staffs():
    today = today_helsinki()
    today_str = today.strftime("%Y-%m-%d")
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")

    q = request.args.get("q", "").strip()
    role = request.args.get("role", "").strip()
    active_raw = request.args.get("active", "").strip()
    active = int(active_raw) if active_raw in ("0", "1") else None

    return render_template(
        "/admin/admin_staff.html",
        staff_list=get_staff_list(today_str, month_start_str, q=q, role=role, active=active),
        stats=get_staff_stats(month_start_str),
        role_list=get_staff_role_list(),
    )


@main.route("/admin/staff/create", methods=["POST"])
@admin_required
def admin_create_staff():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "").strip() or None
    hourly_rate = request.form.get("hourly_rate", type=float) or 0
    commission_rate = request.form.get("commission_rate", type=float) or 0
    is_active = 1 if request.form.get("is_active") == "1" else 0

    if not full_name or not email:
        flash("Vui lòng điền đầy đủ họ tên và email.", "error")
        return redirect(url_for("main.admin_staffs"))

    if get_user_by_email(email):
        flash("Email này đã được dùng cho một tài khoản khác.", "error")
        return redirect(url_for("main.admin_staffs"))

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(12))
    user_id = create_user(email, password, role="staff")

    create_staff(full_name, email, phone, role, hourly_rate, commission_rate, is_active, user_id)
    flash(f"{email}|{password}", "staff_credentials")
    return redirect(url_for("main.admin_staffs"))


@main.route("/admin/staff/<int:staff_id>/update", methods=["POST"])
@admin_required
def admin_update_staff(staff_id):
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "").strip() or None
    hourly_rate = request.form.get("hourly_rate", type=float) or 0
    commission_rate = request.form.get("commission_rate", type=float) or 0
    is_active = 1 if request.form.get("is_active") == "1" else 0

    if not full_name or not email:
        flash("Vui lòng điền đầy đủ họ tên và email.", "error")
        return redirect(url_for("main.admin_staffs"))

    update_staff(staff_id, full_name, email, phone, role, hourly_rate, commission_rate, is_active)
    flash(f"Đã cập nhật nhân viên #{staff_id}.", "success")
    return redirect(url_for("main.admin_staffs"))


@main.route("/admin/staff/<int:staff_id>/delete", methods=["POST"])
@admin_required
def admin_delete_staff(staff_id):
    try:
        delete_staff(staff_id)
        flash("Đã xóa nhân viên.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa nhân viên đang có lịch hẹn liên kết.", "error")
    return redirect(url_for("main.admin_staffs"))


@main.route("/admin/staff/<int:staff_id>/toggle-active", methods=["POST"])
@admin_required
def admin_toggle_staff_active(staff_id):
    toggle_staff_active(staff_id)
    flash("Đã cập nhật trạng thái nhân viên.", "success")
    return redirect(url_for("main.admin_staffs"))

@main.route("/admin/services")
@admin_required
def admin_services():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("category_id", type=int)
    active_raw = request.args.get("active", "").strip()
    active = int(active_raw) if active_raw in ("0", "1") else None

    return render_template(
        "/admin/admin_services.html",
        categories=get_service_categories_with_services(q=q, category_id=category_id, active=active),
        all_categories=get_all_categories(),
        stats=get_service_stats(),
    )


@main.route("/admin/service/create", methods=["POST"])
@admin_required
def admin_create_service():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    category_id = request.form.get("category_id", type=int)
    icon = request.form.get("icon", "").strip() or "spa"
    price = request.form.get("price", type=float)
    duration_minutes = request.form.get("duration_minutes", type=int)
    points = request.form.get("points", type=int) or 0
    badge = request.form.get("badge", "").strip() or None
    is_active = 1 if request.form.get("is_active") == "1" else 0

    if not name or not category_id or price is None or not duration_minutes:
        flash("Vui lòng điền đầy đủ thông tin bắt buộc.", "error")
        return redirect(url_for("main.admin_services"))

    try:
        image = _save_service_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_services"))

    create_service(category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon)
    flash(f"Đã thêm dịch vụ {name}.", "success")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/service/<int:service_id>/update", methods=["POST"])
@admin_required
def admin_update_service(service_id):
    service = get_service_by_id(service_id)
    if not service:
        flash("Không tìm thấy dịch vụ.", "error")
        return redirect(url_for("main.admin_services"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    category_id = request.form.get("category_id", type=int)
    icon = request.form.get("icon", "").strip() or "spa"
    price = request.form.get("price", type=float)
    duration_minutes = request.form.get("duration_minutes", type=int)
    points = request.form.get("points", type=int) or 0
    badge = request.form.get("badge", "").strip() or None
    is_active = 1 if request.form.get("is_active") == "1" else 0
    remove_image = request.form.get("remove_image") == "1"

    if not name or not category_id or price is None or not duration_minutes:
        flash("Vui lòng điền đầy đủ thông tin bắt buộc.", "error")
        return redirect(url_for("main.admin_services"))

    try:
        new_image = _save_service_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_services"))

    if (new_image or remove_image) and service["image"]:
        old_path = os.path.join(_SERVICE_IMG_DIR, service["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    if new_image:
        image = new_image
    elif remove_image:
        image = None
    else:
        image = service["image"]

    update_service(service_id, category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon)
    flash(f"Đã cập nhật dịch vụ {name}.", "success")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/service/<int:service_id>/delete", methods=["POST"])
@admin_required
def admin_delete_service(service_id):
    try:
        delete_service(service_id)
        flash("Đã xóa dịch vụ.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa dịch vụ đang có lịch hẹn liên kết.", "error")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/service/<int:service_id>/toggle-active", methods=["POST"])
@admin_required
def admin_toggle_service_active(service_id):
    toggle_service_active(service_id)
    flash("Đã cập nhật trạng thái dịch vụ.", "success")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/category/create", methods=["POST"])
@admin_required
def admin_create_category():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip() or _slugify(name)
    is_active = 1 if request.form.get("is_active") == "1" else 0

    if not name:
        flash("Vui lòng nhập tên danh mục.", "error")
        return redirect(url_for("main.admin_services"))

    try:
        create_category(name, slug, is_active)
        flash(f"Đã thêm danh mục {name}.", "success")
    except sqlite3.IntegrityError:
        flash("Slug này đã tồn tại. Vui lòng chọn slug khác.", "error")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/category/<int:category_id>/update", methods=["POST"])
@admin_required
def admin_update_category(category_id):
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip() or _slugify(name)
    is_active = 1 if request.form.get("is_active") == "1" else 0

    if not name:
        flash("Vui lòng nhập tên danh mục.", "error")
        return redirect(url_for("main.admin_services"))

    try:
        update_category(category_id, name, slug, is_active)
        flash(f"Đã cập nhật danh mục {name}.", "success")
    except sqlite3.IntegrityError:
        flash("Slug này đã tồn tại. Vui lòng chọn slug khác.", "error")
    return redirect(url_for("main.admin_services"))


@main.route("/admin/category/<int:category_id>/delete", methods=["POST"])
@admin_required
def admin_delete_category(category_id):
    try:
        delete_category(category_id)
        flash("Đã xóa danh mục.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa danh mục đang có dịch vụ. Vui lòng xóa hoặc chuyển dịch vụ sang danh mục khác trước.", "error")
    return redirect(url_for("main.admin_services"))


##GALLERY
@main.route("/admin/gallery")
@admin_required
def admin_gallery():
    q = request.args.get("q", "").strip()
    filter_type = request.args.get("filter", "").strip()

    images = get_gallery_images_admin()
    if q:
        images = [img for img in images if q.lower() in (img["alt_text"] or "").lower()]
    if filter_type == "captioned":
        images = [img for img in images if img["alt_text"]]
    elif filter_type == "uncaptioned":
        images = [img for img in images if not img["alt_text"]]

    return render_template(
        "/admin/admin_gallery.html",
        images=images,
        stats=get_gallery_stats(),
    )


@main.route("/admin/gallery/upload", methods=["POST"])
@admin_required
def admin_gallery_upload():
    files = request.files.getlist("files[]")
    alt_text = request.form.get("alt_text", "").strip()
    sort_order_start = request.form.get("sort_order_start", type=int) or 0

    files = [f for f in files if f and f.filename]
    if not files:
        flash("Vui lòng chọn ít nhất 1 ảnh.", "error")
        return redirect(url_for("main.admin_gallery"))

    rows = []
    try:
        for i, file in enumerate(files):
            filename = _save_gallery_image(file)
            rows.append((filename, alt_text, sort_order_start + i))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_gallery"))

    create_gallery_images(rows)
    flash(f"Đã tải lên {len(rows)} ảnh thành công.", "success")
    return redirect(url_for("main.admin_gallery"))


@main.route("/admin/gallery/<int:image_id>/update", methods=["POST"])
@admin_required
def admin_gallery_update(image_id):
    image = get_gallery_image_by_id(image_id)
    if not image:
        flash("Không tìm thấy ảnh.", "error")
        return redirect(url_for("main.admin_gallery"))

    alt_text = request.form.get("alt_text", "").strip()
    sort_order = request.form.get("sort_order", type=int) or 0
    is_active = 1 if request.form.get("is_active") == "1" else 0

    try:
        new_image = _save_gallery_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_gallery"))

    if new_image:
        old_path = os.path.join(_GALLERY_IMG_DIR, image["image_url"])
        if os.path.exists(old_path):
            os.remove(old_path)
        update_gallery_image(image_id, alt_text, sort_order, is_active, image_url=new_image)
    else:
        update_gallery_image(image_id, alt_text, sort_order, is_active)

    flash("Đã cập nhật ảnh.", "success")
    return redirect(url_for("main.admin_gallery"))


@main.route("/admin/gallery/<int:image_id>/delete", methods=["POST"])
@admin_required
def admin_gallery_delete(image_id):
    image = get_gallery_image_by_id(image_id)
    if image:
        old_path = os.path.join(_GALLERY_IMG_DIR, image["image_url"])
        try:
            os.remove(old_path)
        except OSError:
            pass
        delete_gallery_image(image_id)
        flash("Đã xóa ảnh.", "success")
    return redirect(url_for("main.admin_gallery"))


@main.route("/admin/gallery/reorder", methods=["POST"])
@admin_required
def admin_gallery_reorder():
    data = request.get_json(silent=True) or {}
    order = data.get("order", [])
    reorder_gallery_images([(item["sort_order"], item["id"]) for item in order])
    return jsonify({"success": True})


@main.route("/admin/gallery/bulk-delete", methods=["POST"])
@admin_required
def admin_gallery_bulk_delete():
    ids_raw = request.form.get("image_ids", "")
    image_ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]

    for image_id in image_ids:
        image = get_gallery_image_by_id(image_id)
        if image:
            old_path = os.path.join(_GALLERY_IMG_DIR, image["image_url"])
            try:
                os.remove(old_path)
            except OSError:
                pass

    if image_ids:
        bulk_delete_gallery_images(image_ids)
        flash(f"Đã xóa {len(image_ids)} ảnh.", "success")
    return redirect(url_for("main.admin_gallery"))


@main.route("/admin/customers")
@admin_required
def admin_customers():
    today = today_helsinki()
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")

    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "newest").strip()
    tier = request.args.get("tier", "").strip()
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 15

    customers, total = get_admin_customers(q=q, sort=sort, tier=tier, page=page, per_page=per_page)
    pages = max(1, (total + per_page - 1) // per_page)
    pagination = {
        "start":    (page - 1) * per_page + 1 if total > 0 else 0,
        "end":      min(page * per_page, total),
        "total":    total,
        "page":     page,
        "pages":    pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }

    return render_template(
        "admin/admin_customers.html",
        customers=customers,
        stats=get_admin_customer_stats(month_start_str),
        pagination=pagination,
    )


@main.route("/admin/customers/create", methods=["POST"])
@admin_required
def admin_create_customer():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    date_of_birth = request.form.get("date_of_birth", "").strip() or None
    notes = request.form.get("notes", "").strip()
    email = request.form.get("email", "").strip()

    if not full_name:
        flash("Vui lòng điền họ và tên.", "error")
        return redirect(url_for("main.admin_customers"))

    if email and get_user_by_email(email):
        flash("Không thể tạo khách hàng: email này đã được dùng để tạo một tài khoản khác.", "error")
        return redirect(url_for("main.admin_customers"))

    customer_id = create_customer_admin(full_name, email, phone, date_of_birth, notes)

    silver_tier = get_tier_by_name("Silver")
    if silver_tier:
        upgrade_membership(customer_id, silver_tier["id"], silver_tier["duration_days"])

    if not email:
        flash("Đã thêm khách hàng mới.", "success")
        return redirect(url_for("main.admin_customers"))

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(12))
    user_id = create_user(email, password, role="customer")
    link_customer_to_user(customer_id, user_id)
    flash(f"{email}|{password}", "customer_credentials")
    return redirect(url_for("main.admin_customers"))


@main.route("/admin/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_customer(customer_id):
    customer = get_customer_by_customer_id(customer_id)
    if not customer:
        flash("Không tìm thấy khách hàng.", "error")
        return redirect(url_for("main.admin_customers"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip() or None
        notes = request.form.get("notes", "").strip()
        email = request.form.get("email", "").strip()

        if not full_name:
            flash("Vui lòng điền họ và tên.", "error")
            return redirect(url_for("main.admin_edit_customer", customer_id=customer_id))

        update_customer_admin(customer_id, full_name, email, phone, date_of_birth, notes)
        flash(f"Đã cập nhật khách hàng #{customer_id}.", "success")
        return redirect(url_for("main.admin_customers"))

    # No dedicated edit-page template yet — admin_customers.html's Detail modal
    # covers view-only info. Redirect back until an edit page/modal is built.
    flash("Trang chỉnh sửa khách hàng chưa được xây dựng.", "error")
    return redirect(url_for("main.admin_customers"))


@main.route("/admin/customers/<int:customer_id>/adjust-points", methods=["POST"])
@admin_required
def admin_adjust_points(customer_id):
    customer = get_customer_by_customer_id(customer_id)
    if not customer:
        flash("Không tìm thấy khách hàng.", "error")
        return redirect(url_for("main.admin_customers"))

    points = request.form.get("points", type=int)
    if not points:
        flash("Vui lòng nhập số điểm hợp lệ.", "error")
        return redirect(url_for("main.admin_customers"))

    admin_name = session.get("admin_name", "Admin")
    award_points(customer_id, points, "admin_adjustment", note=f"Điều chỉnh bởi {admin_name}")
    flash(f"Đã điều chỉnh {points:+d} điểm cho {customer['full_name']}.", "success")
    return redirect(url_for("main.admin_customers"))


@main.route("/admin/customers/<int:customer_id>/delete", methods=["POST"])
@admin_required
def admin_delete_customer(customer_id):
    customer = get_customer_by_customer_id(customer_id)
    if not customer:
        flash("Không tìm thấy khách hàng.", "error")
        return redirect(url_for("main.admin_customers"))

    try:
        delete_customer_admin(customer_id)
        flash(f"Đã xóa khách hàng {customer['full_name']}.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa khách hàng đang có booking hoặc dữ liệu liên kết.", "error")

    return redirect(url_for("main.admin_customers"))


#====================================
#         Admin — Loyalty
#====================================

# "Missions" = display metadata for the 5 real loyalty_config keys that
# already drive award_points() in the booking flow (see admin_loyalty()
# and get_missions() in db.py). Not a free-form namespace.
_MISSION_META = {
    "first_booking_bonus": {"name": "Đặt lịch đầu tiên",         "icon": "event_available",       "icon_color": "green"},
    "streak_bonus":        {"name": "Đặt lịch liên tục 3 tháng", "icon": "local_fire_department", "icon_color": "purple"},
    "review_bonus":        {"name": "Viết đánh giá",             "icon": "star",                  "icon_color": "orange"},
    "birthday_bonus":      {"name": "Sinh nhật",                 "icon": "cake",                  "icon_color": "pink"},
    "referral_bonus":      {"name": "Giới thiệu bạn bè",         "icon": "group_add",             "icon_color": "blue"},
}
_MISSION_DEFAULT_POINTS = {
    "first_booking_bonus": 99,
    "streak_bonus":        100,
    "review_bonus":        50,
    "birthday_bonus":      100,
    "referral_bonus":      200,
}


def _build_missions_context():
    missions = []
    for m in get_missions():
        meta = _MISSION_META.get(m["key"], {"name": m["key"], "icon": "target", "icon_color": "blue"})
        points = int(m["value"])
        missions.append({
            "source_key":  m["key"],
            "name":        meta["name"],
            "icon":        meta["icon"],
            "icon_color":  meta["icon_color"],
            "description": m["description"] or "",
            "points":      points,
            "is_active":   1 if points > 0 else 0,
        })
    return missions


@main.route("/admin/loyalty")
@admin_required
def admin_loyalty():
    return render_template(
        "admin/admin_loyalty.html",
        customers=get_admin_loyalty_customers(),
        vouchers=get_rewards_admin(),
        missions=_build_missions_context(),
        membership_tiers=get_active_membership_tiers(),
        stats=get_admin_loyalty_stats(),
    )


@main.route("/admin/loyalty/adjust-points", methods=["POST"])
@admin_required
def admin_loyalty_adjust_points():
    customer_id = request.form.get("customer_id", type=int)
    points = request.form.get("points", type=int)
    adj_type = request.form.get("type", "").strip()
    note = request.form.get("note", "").strip() or None

    customer = get_customer_by_customer_id(customer_id) if customer_id else None
    if not customer or not points or adj_type not in ("add", "sub"):
        flash("Vui lòng nhập đầy đủ thông tin điều chỉnh điểm.", "error")
        return redirect(url_for("main.admin_loyalty"))

    signed_points = abs(points) if adj_type == "add" else -abs(points)
    award_points(customer_id, signed_points, "admin_adjustment", note=note)
    flash(f"Đã điều chỉnh {signed_points:+d} điểm cho {customer['full_name']}.", "success")
    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/adjust-membership", methods=["POST"])
@admin_required
def admin_loyalty_adjust_membership():
    customer_id = request.form.get("customer_id", type=int)
    tier_id = request.form.get("tier_id", type=int)
    started_at = request.form.get("started_at", "").strip()
    expires_at = request.form.get("expires_at", "").strip()

    customer = get_customer_by_customer_id(customer_id) if customer_id else None
    if not customer or not tier_id or not started_at or not expires_at:
        flash("Vui lòng nhập đầy đủ thông tin membership.", "error")
        return redirect(url_for("main.admin_loyalty"))

    adjust_membership_admin(customer_id, tier_id, started_at, expires_at)
    flash(f"Đã cập nhật membership cho {customer['full_name']}.", "success")
    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/vouchers/create", methods=["POST"])
@admin_required
def admin_loyalty_create_voucher():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    cost = request.form.get("cost", type=int)
    stock = request.form.get("stock", type=int)
    max_redeems_per_customer = request.form.get("max_redeems_per_customer", type=int)
    cooldown_days = request.form.get("cooldown_days", type=int)

    if not name or not cost:
        flash("Vui lòng nhập tên và chi phí điểm cho voucher.", "error")
        return redirect(url_for("main.admin_loyalty"))

    try:
        banner_image = _save_reward_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_loyalty"))

    create_reward(name, description, cost, stock, max_redeems_per_customer, cooldown_days, banner_image)
    flash("Đã tạo voucher mới.", "success")
    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/vouchers/<int:reward_id>/update", methods=["POST"])
@admin_required
def admin_loyalty_update_voucher(reward_id):
    reward = get_reward_by_id(reward_id)
    if not reward:
        flash("Không tìm thấy voucher.", "error")
        return redirect(url_for("main.admin_loyalty"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    cost = request.form.get("cost", type=int)
    stock = request.form.get("stock", type=int)
    max_redeems_per_customer = request.form.get("max_redeems_per_customer", type=int)
    cooldown_days = request.form.get("cooldown_days", type=int)
    is_active = 1 if request.form.get("is_active") else 0
    remove_image = request.form.get("remove_image") == "1"

    if not name or not cost:
        flash("Vui lòng nhập tên và chi phí điểm cho voucher.", "error")
        return redirect(url_for("main.admin_loyalty"))

    try:
        new_image = _save_reward_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_loyalty"))

    if (new_image or remove_image) and reward["banner_image"]:
        old_path = os.path.join(_REWARD_IMG_DIR, reward["banner_image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    if new_image:
        banner_image = new_image
    elif remove_image:
        banner_image = None
    else:
        banner_image = reward["banner_image"]

    update_reward(reward_id, name, description, cost, stock, max_redeems_per_customer, cooldown_days, is_active, banner_image)
    flash("Đã cập nhật voucher.", "success")
    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/vouchers/<int:reward_id>/delete", methods=["POST"])
@admin_required
def admin_loyalty_delete_voucher(reward_id):
    reward = get_reward_by_id(reward_id)
    if not reward:
        flash("Không tìm thấy voucher.", "error")
        return redirect(url_for("main.admin_loyalty"))

    if get_reward_redemption_count(reward_id) > 0:
        deactivate_reward(reward_id)
        flash(f"Voucher \"{reward['name']}\" đã có khách đổi nên chỉ được ẩn, không xóa hẳn.", "success")
    else:
        if reward["banner_image"]:
            old_path = os.path.join(_REWARD_IMG_DIR, reward["banner_image"])
            if os.path.exists(old_path):
                os.remove(old_path)
        delete_reward(reward_id)
        flash(f"Đã xóa voucher \"{reward['name']}\".", "success")

    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/missions/<key>/update", methods=["POST"])
@admin_required
def admin_loyalty_update_mission(key):
    if key not in MISSION_KEYS:
        flash("Mission không hợp lệ.", "error")
        return redirect(url_for("main.admin_loyalty"))

    description = request.form.get("description", "").strip()
    points = request.form.get("points", type=int)
    if points is None or points < 0:
        flash("Vui lòng nhập số điểm hợp lệ.", "error")
        return redirect(url_for("main.admin_loyalty"))

    update_mission_config(key, description, points)
    flash("Đã cập nhật mission.", "success")
    return redirect(url_for("main.admin_loyalty"))


@main.route("/admin/loyalty/missions/<key>/toggle", methods=["POST"])
@admin_required
def admin_loyalty_toggle_mission(key):
    if key not in MISSION_KEYS:
        return jsonify({"success": False}), 404

    default_points = _MISSION_DEFAULT_POINTS.get(key, 50)
    new_value = toggle_mission_config(key, default_points)
    return jsonify({"success": True, "is_active": 1 if new_value > 0 else 0, "points": new_value})


#====================================
#         Admin — Carousels
#====================================

def _is_managed_carousel_image(image):
    """True if `image` is a bare filename we saved (and can safely delete from
    disk), as opposed to an external URL or a legacy /static/... path."""
    return bool(image) and not image.startswith("http://") and not image.startswith("https://") and not image.startswith("/")


@main.route("/admin/carousels")
@admin_required
def admin_carousels():
    homepage_slides = get_carousel_slides("homepage")
    for s in homepage_slides:
        s["image_url"] = _resolve_carousel_image(s["image"])

    mission_slides = get_mission_slides()
    for m in mission_slides:
        m["image_url"] = _resolve_carousel_image(m["image"])

    offer_slides = get_carousel_slides("dashboard_offers")
    for s in offer_slides:
        s["image_url"] = _resolve_carousel_image(s["image"])

    return render_template(
        "admin/admin_carousels.html",
        homepage_slides=homepage_slides,
        offer_slides=offer_slides,
        mission_slides=mission_slides,
    )


@main.route("/admin/carousels/homepage/create", methods=["POST"])
@admin_required
def admin_carousel_homepage_create():
    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    badge = request.form.get("badge", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = request.form.get("cta_url", "").strip()
    cta_style = request.form.get("cta_style", "primary").strip() or "primary"
    cta2_label = request.form.get("cta2_label", "").strip()
    cta2_url = request.form.get("cta2_url", "").strip()
    cta2_style = request.form.get("cta2_style", "outline").strip() or "outline"

    if not title:
        flash("Vui lòng nhập tiêu đề slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    try:
        image = _save_carousel_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_carousels"))

    if not image:
        flash("Vui lòng chọn ảnh cho slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    sort_order = get_next_carousel_sort_order("homepage")
    create_homepage_slide(title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, sort_order)
    flash("Đã tạo slide trang chủ mới.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/homepage/<int:slide_id>/update", methods=["POST"])
@admin_required
def admin_carousel_homepage_update(slide_id):
    slide = get_carousel_slide_by_id(slide_id)
    if not slide or slide["carousel_key"] != "homepage":
        flash("Không tìm thấy slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    badge = request.form.get("badge", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = request.form.get("cta_url", "").strip()
    cta_style = request.form.get("cta_style", "primary").strip() or "primary"
    cta2_label = request.form.get("cta2_label", "").strip()
    cta2_url = request.form.get("cta2_url", "").strip()
    cta2_style = request.form.get("cta2_style", "outline").strip() or "outline"
    is_active = 1 if request.form.get("is_active") else 0
    remove_image = request.form.get("remove_image") == "1"

    if not title:
        flash("Vui lòng nhập tiêu đề slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    try:
        new_image = _save_carousel_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_carousels"))

    if (new_image or remove_image) and _is_managed_carousel_image(slide["image"]):
        old_path = os.path.join(_CAROUSEL_IMG_DIR, slide["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    if new_image:
        image = new_image
    elif remove_image:
        image = None
    else:
        image = slide["image"]

    if not image:
        flash("Slide cần có ảnh.", "error")
        return redirect(url_for("main.admin_carousels"))

    update_homepage_slide(slide_id, title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, is_active)
    flash("Đã cập nhật slide.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/offers/create", methods=["POST"])
@admin_required
def admin_carousel_offer_create():
    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    badge = request.form.get("badge", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = request.form.get("cta_url", "").strip()
    cta_style = request.form.get("cta_style", "primary").strip() or "primary"

    if not title:
        flash("Vui lòng nhập tiêu đề slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    try:
        image = _save_carousel_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_carousels"))

    sort_order = get_next_carousel_sort_order("dashboard_offers")
    create_offer_slide(title, subtitle, badge, image, cta_label, cta_url, cta_style, sort_order)
    flash("Đã thêm slide ưu đãi.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/offers/<int:slide_id>/update", methods=["POST"])
@admin_required
def admin_carousel_offer_update(slide_id):
    slide = get_carousel_slide_by_id(slide_id)
    if not slide or slide["carousel_key"] != "dashboard_offers":
        flash("Không tìm thấy slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    badge = request.form.get("badge", "").strip()
    cta_label = request.form.get("cta_label", "").strip()
    cta_url = request.form.get("cta_url", "").strip()
    cta_style = request.form.get("cta_style", "primary").strip() or "primary"
    is_active = 1 if request.form.get("is_active") else 0
    remove_image = request.form.get("remove_image") == "1"

    if not title:
        flash("Vui lòng nhập tiêu đề slide.", "error")
        return redirect(url_for("main.admin_carousels"))

    try:
        new_image = _save_carousel_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_carousels"))

    if (new_image or remove_image) and _is_managed_carousel_image(slide["image"]):
        old_path = os.path.join(_CAROUSEL_IMG_DIR, slide["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    if new_image:
        image = new_image
    elif remove_image:
        image = None
    else:
        image = slide["image"]

    update_offer_slide(slide_id, title, subtitle, badge, image, cta_label, cta_url, cta_style, is_active)
    flash("Đã cập nhật slide ưu đãi.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/<int:slide_id>/delete", methods=["POST"])
@admin_required
def admin_carousel_delete(slide_id):
    slide = get_carousel_slide_by_id(slide_id)
    if not slide:
        flash("Không tìm thấy slide.", "error")
        return redirect(url_for("main.admin_carousels"))
    if slide["carousel_key"] == "loyalty_missions":
        flash("Không thể xóa mission cố định.", "error")
        return redirect(url_for("main.admin_carousels"))

    if _is_managed_carousel_image(slide["image"]):
        old_path = os.path.join(_CAROUSEL_IMG_DIR, slide["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    delete_carousel_slide(slide_id)
    flash("Đã xóa slide.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/missions/<slot_key>/update", methods=["POST"])
@admin_required
def admin_carousel_mission_update(slot_key):
    if slot_key not in MISSION_SLOT_KEYS:
        flash("Mission không hợp lệ.", "error")
        return redirect(url_for("main.admin_carousels"))

    slide = next((s for s in get_mission_slides() if s["slot_key"] == slot_key), None)

    icon = request.form.get("icon", "").strip()
    title = request.form.get("title", "").strip()
    pts_label = request.form.get("pts_label", "").strip()
    remove_image = request.form.get("remove_image") == "1"

    if not title:
        flash("Vui lòng nhập tên mission.", "error")
        return redirect(url_for("main.admin_carousels"))

    try:
        new_image = _save_carousel_image(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.admin_carousels"))

    if (new_image or remove_image) and slide and _is_managed_carousel_image(slide["image"]):
        old_path = os.path.join(_CAROUSEL_IMG_DIR, slide["image"])
        if os.path.exists(old_path):
            os.remove(old_path)

    if new_image:
        image = new_image
    elif remove_image:
        image = None
    else:
        image = slide["image"] if slide else None

    update_mission_slide(slot_key, icon, title, pts_label, image)
    flash("Đã cập nhật mission.", "success")
    return redirect(url_for("main.admin_carousels"))


@main.route("/admin/carousels/reorder", methods=["POST"])
@admin_required
def admin_carousel_reorder():
    data = request.get_json(silent=True) or {}
    order = data.get("order", [])
    reorder_carousel_slides([(item["sort_order"], item["id"]) for item in order])
    return jsonify({"success": True})


# ── Reports helpers ──────────────────────────────────────────
_REPORT_STATUS_COLORS = {
    "done":        "#1D9E75",
    "confirmed":   "#378ADD",
    "pending":     "#EF9F27",
    "in-progress": "#9B59D0",
    "cancelled":   "#E24B4A",
    "no-show":     "#9B4444",
}
_REPORT_STATUS_LABELS = {
    "done":        "Hoàn thành",
    "confirmed":   "Đã xác nhận",
    "pending":     "Chờ xác nhận",
    "in-progress": "Đang thực hiện",
    "cancelled":   "Đã hủy",
    "no-show":     "Không đến",
}
_REPORT_SOURCE_LABELS = {
    "booking":          "Hoàn thành booking",
    "first_booking":    "Booking đầu tiên",
    "birthday":         "Sinh nhật",
    "review":           "Viết đánh giá",
    "streak":           "Chuỗi ghé thăm",
    "admin":            "Admin điều chỉnh",
    "admin_adjustment": "Admin điều chỉnh",
    "referral":         "Giới thiệu bạn bè",
}
_REPORT_PRESETS = ("today", "7days", "month", "3months", "year")


def _months_ago(d, n):
    """First day of the month that is n months before d's month."""
    m = d.month - n
    y = d.year
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def _resolve_report_range(preset, date_from, date_to):
    """Return (date_from, date_to, active_preset) as YYYY-MM-DD strings.
    Custom date_from/date_to override the preset (active_preset = '')."""
    today = today_helsinki()
    if date_from or date_to:
        df = date_from or date_to
        dt = date_to or date_from
        if df > dt:
            df, dt = dt, df
        return df, dt, ""

    if preset == "today":
        start = end = today
    elif preset == "7days":
        start, end = today - timedelta(days=6), today
    elif preset == "3months":
        start, end = _months_ago(today, 2), today
    elif preset == "year":
        start, end = date(today.year, 1, 1), today
    else:
        preset = "month"
        start, end = date(today.year, today.month, 1), today
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), preset


def _pct_trend(cur, prev):
    """Signed percentage change vs previous period, rounded to 1 dp."""
    if prev == 0:
        return 100.0 if cur > 0 else 0.0
    return round((cur - prev) / prev * 100, 1)


_MONTH_ABBR_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_WEEKDAY_ABBR_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_WEEKDAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _month_span(d_from, d_to):
    """List of (year, month) tuples spanned by [d_from, d_to], inclusive."""
    months = []
    y, m = d_from.year, d_from.month
    while (y, m) <= (d_to.year, d_to.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _build_revenue_chart(df, dt, active_preset):
    """Bucket paid revenue for the 'Doanh thu theo ngày' card.

    Grouping is picked from active_preset; for a custom range (active_preset == '')
    it's auto-selected from the range length: <=1 day hourly, <=14 daily,
    <=90 biweekly, else monthly.
    """
    d_from = datetime.strptime(df, "%Y-%m-%d").date()
    d_to = datetime.strptime(dt, "%Y-%m-%d").date()
    length = (d_to - d_from).days
    today = today_helsinki()

    if active_preset == "today":
        grouping = "hourly"
    elif active_preset == "7days":
        grouping = "daily"
    elif active_preset == "month":
        grouping = "daily"
    elif active_preset == "3months":
        grouping = "biweekly"
    elif active_preset == "year":
        grouping = "monthly"
    elif length <= 1:
        grouping = "hourly"
    elif length <= 14:
        grouping = "daily"
    elif length <= 90:
        grouping = "biweekly"
    else:
        grouping = "monthly"

    buckets = []  # (label, amount, tooltip, is_current)

    if grouping == "hourly":
        hour_amounts = get_report_revenue_by_hour(df)
        now_hour = now_helsinki().hour
        for h in range(0, 24, 3):
            amt = sum(hour_amounts.get(x, 0) for x in range(h, h + 3))
            buckets.append((
                f"{h:02d}:00", amt,
                f"{h:02d}:00 - {(h + 3) % 24:02d}:00 · {amt:.0f}€",
                active_preset == "today" and h <= now_hour < h + 3,
            ))

    elif grouping == "daily":
        day_amount = {r["day"]: r["amount"] for r in get_report_revenue_by_day(df, dt)}
        # step > 1 (preset 'month') gộp mỗi 'step' ngày liên tiếp thành 1 cột và CỘNG
        # trọn cửa sổ — trước đây chỉ lấy doanh thu 1 ngày rồi nhảy qua ngày kế, làm
        # mất doanh thu các ngày bị bỏ qua khiến tổng cột không khớp KPI.
        step = 2 if active_preset == "month" else 1
        d = d_from
        while d <= d_to:
            win_end = min(d + timedelta(days=step - 1), d_to)
            amt, is_current, wd = 0.0, False, d
            while wd <= win_end:
                amt += day_amount.get(wd.strftime("%Y-%m-%d"), 0)
                is_current = is_current or wd == today
                wd += timedelta(days=1)
            label = _WEEKDAY_ABBR_EN[d.weekday()] if active_preset == "7days" else f"{d.day}/{d.month}"
            if step > 1 and win_end > d:
                tooltip = f"{d.day:02d}/{d.month:02d}–{win_end.day:02d}/{win_end.month:02d} · {amt:.0f}€"
            else:
                tooltip = f"{_WEEKDAY_VI[d.weekday()]} {d.day:02d}/{d.month:02d} · {amt:.0f}€"
            buckets.append((label, amt, tooltip, is_current))
            d += timedelta(days=step)

    elif grouping == "biweekly":
        day_amount = {r["day"]: r["amount"] for r in get_report_revenue_by_day(df, dt)}
        for (y, m) in _month_span(d_from, d_to):
            last_day = calendar.monthrange(y, m)[1]
            for half_start, half_end in ((1, 14), (15, last_day)):
                start = max(date(y, m, half_start), d_from)
                end = min(date(y, m, half_end), d_to)
                if start > end:
                    continue
                amt, is_current, d = 0.0, False, start
                while d <= end:
                    amt += day_amount.get(d.strftime("%Y-%m-%d"), 0)
                    is_current = is_current or d == today
                    d += timedelta(days=1)
                buckets.append((
                    f"{half_start}/{m}", amt,
                    f"{half_start}-{half_end}/{m}/{y} · {amt:.0f}€",
                    is_current,
                ))

    else:  # monthly
        day_amount = {r["day"]: r["amount"] for r in get_report_revenue_by_day(df, dt)}
        months = [(d_to.year, mo) for mo in range(1, 13)] if active_preset == "year" else _month_span(d_from, d_to)
        for (y, m) in months:
            last_day = calendar.monthrange(y, m)[1]
            start, end = max(date(y, m, 1), d_from), min(date(y, m, last_day), d_to)
            amt, d = 0.0, start
            while d <= end:
                amt += day_amount.get(d.strftime("%Y-%m-%d"), 0)
                d += timedelta(days=1)
            label = _MONTH_ABBR_EN[m - 1]
            buckets.append((label, amt, f"{label} {y} · {amt:.0f}€", (y, m) == (today.year, today.month)))

    max_amt = max((b[1] for b in buckets), default=0)
    chart_data = [
        {
            "label": label,
            "amount": amt,
            "pct": round(amt / max_amt * 100) if max_amt else 0,
            "tooltip": tooltip,
            "is_current": is_current,
        }
        for label, amt, tooltip, is_current in buckets
    ]
    return chart_data, grouping


def _build_report_context(df, dt, active_preset):
    """Assemble every context dict the reports template needs."""
    # Previous period of equal length, immediately before df.
    d_from = datetime.strptime(df, "%Y-%m-%d").date()
    d_to = datetime.strptime(dt, "%Y-%m-%d").date()
    length = (d_to - d_from).days
    prev_to = d_from - timedelta(days=1)
    prev_from = prev_to - timedelta(days=length)
    pdf, pdt = prev_from.strftime("%Y-%m-%d"), prev_to.strftime("%Y-%m-%d")

    cur = get_report_totals(df, dt)
    prev = get_report_totals(pdf, pdt)
    kpi = {
        "total_revenue":   cur["revenue"],
        "revenue_trend":   _pct_trend(cur["revenue"], prev["revenue"]),
        "total_bookings":  cur["bookings"],
        "bookings_trend":  _pct_trend(cur["bookings"], prev["bookings"]),
        "new_customers":   cur["new_customers"],
        "customers_trend": cur["new_customers"] - prev["new_customers"],  # absolute delta
        "points_issued":   cur["points_issued"],
        "points_trend":    _pct_trend(cur["points_issued"], prev["points_issued"]),
    }

    # Revenue chart → dynamic grouping based on active_preset (see _build_revenue_chart).
    revenue_chart_data, revenue_chart_grouping = _build_revenue_chart(df, dt, active_preset)

    # Booking status donut → pct + cumulative offset for stroke-dasharray.
    status_counts = get_report_booking_status(df, dt)
    total_bk = sum(status_counts.values())
    booking_status_breakdown = []
    offset = 0.0
    for status in ("done", "confirmed", "in-progress", "pending", "cancelled", "no-show"):
        count = status_counts.get(status, 0)
        if count == 0:
            continue
        pct = round(count / total_bk * 100, 1) if total_bk else 0
        booking_status_breakdown.append({
            "status": status,
            "label": _REPORT_STATUS_LABELS.get(status, status),
            "count": count,
            "pct": pct,
            "color": _REPORT_STATUS_COLORS.get(status, "#8591a5"),
            "cumulative_offset": round(offset, 2),
        })
        offset += pct

    # Top services → revenue share of total paid revenue.
    total_paid = kpi["total_revenue"]
    top_services = []
    for sv in get_report_top_services(df, dt):
        top_services.append({
            "name": sv["name"],
            "booking_count": sv["booking_count"],
            "revenue": sv["revenue"],
            "revenue_pct": round(sv["revenue"] / total_paid * 100, 1) if total_paid else 0,
        })

    # Staff performance → bar fill relative to the top performer.
    staff_rows = get_report_staff_performance(df, dt)
    max_staff_rev = max((s["revenue"] for s in staff_rows), default=0)
    staff_performance = []
    for s in staff_rows:
        parts = (s["full_name"] or "").split()
        initials = "".join(p[0].upper() for p in parts[:2]) or "?"
        staff_performance.append({
            "full_name": s["full_name"],
            "initials": initials,
            "booking_count": s["booking_count"],
            "revenue": s["revenue"],
            "revenue_pct": round(s["revenue"] / max_staff_rev * 100, 1) if max_staff_rev else 0,
        })

    # Customer growth → always the last 6 calendar months.
    today = today_helsinki()
    since = _months_ago(today, 5)
    growth_map = get_report_customer_growth(since.strftime("%Y-%m-%d"))
    months = [_months_ago(today, 5 - i) for i in range(6)]
    counts = [growth_map.get(m.strftime("%Y-%m"), 0) for m in months]
    max_count = max(counts, default=0)
    customer_growth = []
    for i, m in enumerate(months):
        prev_c = counts[i - 1] if i > 0 else 0
        customer_growth.append({
            "label": f"T{m.month}",
            "month": m.month,
            "year": m.year,
            "count": counts[i],
            "pct": round(counts[i] / max_count * 100, 1) if max_count else 0,
            "is_current": (m.year == today.year and m.month == today.month),
            "growth_pct": _pct_trend(counts[i], prev_c),
        })

    # Loyalty summary.
    loy = get_report_loyalty(df, dt)
    loyalty = {
        "total_issued": loy["total_issued"],
        "total_redeemed": loy["total_redeemed"],
        "net_points": loy["total_issued"] - loy["total_redeemed"],
        "redemption_count": loy["redemption_count"],
        "sources": [
            {
                "source": s["source"],
                "source_label": _REPORT_SOURCE_LABELS.get(s["source"], s["source"]),
                "points": int(s["points"]),
            }
            for s in loy["sources"]
        ],
    }

    return {
        "kpi": kpi,
        "revenue_chart_data": revenue_chart_data,
        "grouping": revenue_chart_grouping,
        "booking_status_breakdown": booking_status_breakdown,
        "total_bookings_count": total_bk,
        "top_services": top_services,
        "staff_performance": staff_performance,
        "customer_growth": customer_growth,
        "loyalty": loyalty,
    }


@main.route("/admin/reports")
@admin_required
def admin_reports():
    preset = request.args.get("preset", "month").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    df, dt, active_preset = _resolve_report_range(preset, date_from, date_to)
    ctx = _build_report_context(df, dt, active_preset)

    return render_template(
        "/admin/admin_reports.html",
        date_from=df,
        date_to=dt,
        active_preset=active_preset,
        **ctx,
    )


@main.route("/admin/reports/export.csv")
@admin_required
def export_report_csv():
    import csv, io
    preset = request.args.get("preset", "month").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    df, dt, active_preset = _resolve_report_range(preset, date_from, date_to)
    ctx = _build_report_context(df, dt, active_preset)
    kpi = ctx["kpi"]

    buf = io.StringIO()
    buf.write("﻿")  # BOM để Excel đọc đúng tiếng Việt
    w = csv.writer(buf)

    w.writerow(["Báo cáo DahaCare", f"Từ {df}", f"Đến {dt}"])
    w.writerow([])
    w.writerow(["Chỉ số", "Giá trị"])
    w.writerow(["Tổng doanh thu", f"{kpi['total_revenue']:.0f}"])
    w.writerow(["Tổng booking", kpi["total_bookings"]])
    w.writerow(["Khách hàng mới", kpi["new_customers"]])
    w.writerow(["Điểm loyalty đã phát", kpi["points_issued"]])
    w.writerow([])

    w.writerow(["Top dịch vụ", "Lượt", "Doanh thu", "Tỉ lệ %"])
    for sv in ctx["top_services"]:
        w.writerow([sv["name"], sv["booking_count"], f"{sv['revenue']:.0f}", sv["revenue_pct"]])
    w.writerow([])

    w.writerow(["Nhân viên", "Booking", "Doanh thu"])
    for s in ctx["staff_performance"]:
        w.writerow([s["full_name"], s["booking_count"], f"{s['revenue']:.0f}"])

    filename = f"dahacare-bao-cao-{df}-{dt}.csv"
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@main.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("main.staff_login"))

@main.route("/admin/booking/walk-in")
@admin_required
def booking_walkin():
    return redirect(url_for("main.admin_bookings"))

#====================================
#               Public
#====================================

@main.route("/")
def home():
    raw_slides = get_carousel_slides("homepage", active_only=True)
    slides = []
    for s in raw_slides:
        cta = []
        if s["cta_label"] and s["cta_url"]:
            cta.append({"label": s["cta_label"], "url": s["cta_url"], "style": s["cta_style"] or "primary"})
        if s["cta2_label"] and s["cta2_url"]:
            cta.append({"label": s["cta2_label"], "url": s["cta2_url"], "style": s["cta2_style"] or "outline"})
        slides.append({
            "image":    _resolve_carousel_image(s["image"]),
            "badge":    s["badge"],
            "title":    s["title"],
            "subtitle": s["subtitle"],
            "cta":      cta,
        })
    popular_services = get_popular_services(limit=4)
    gallery_images = get_gallery_images()[:5]
    return render_template("/public/index.html", slides=slides, services=popular_services, gallery_images=gallery_images)

@main.route("/public/booking")
def public_booking():
    preselect_id = request.args.get("service_id", type=int)

    if session.get("user_id"):
        role = session.get("role")
        if role == "staff":
            return redirect(url_for("main.staff_dashboard"))
        if role == "admin":
            return redirect(url_for("main.admin_dashboard"))
        return redirect(url_for("main.customer_booking", service_id=preselect_id))

    today = today_helsinki()
    max_date = today + timedelta(days=60)

    categories = get_active_service_categories()
    services = get_active_services_with_category()
    staffs = get_all_staff()

    if preselect_id and preselect_id not in [s["id"] for s in services]:
        flash("That service is no longer available. Showing our full menu.", "warning")
        preselect_id = None

    services_by_category = build_services_by_category(categories, services)


    return render_template(
        "/public/public_booking.html",
        categories=categories,
        services_by_category=services_by_category,
        staffs=staffs,
        today=today,
        max_date=max_date,
        preselect_id=preselect_id,
    )

@main.route("/public/create-booking", methods=['POST'])
def create_public_booking():
    #Data from booking form.
    
    try:
        customer = GuestService.resolve_customer_info(request.form)

    except GuestInfoMissingError as e:
        flash(str(e), "error")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400
    
    service_id_raw = request.form.get("service_id", "").strip()
    booking_date_raw = request.form.get("booking_date", "").strip()
    slot_raw = request.form.get("start_time", "").strip()

    if not service_id_raw or not booking_date_raw or not slot_raw:
        flash("Please select a service, date, and time slot before confirming.", "error")
        return redirect(url_for('main.public_booking'))

    #Parse form
    data = BookingService.parse_form(request.form)

    booking_date = data["booking_date"]
    note = data["note"]
    service_id = int(data["service_id"])
    booking_slot = data["slot"]
    staff_id = int(data["staff_id"])

    service = get_service_by_id(data["service_id"])
    if not service:
        flash("Service not found. Please try again.", "error")
        return redirect(url_for('main.public_booking'))
    service_duration = service["duration_minutes"]
    start_time, end_time = BookingService.parse_slot(booking_date, booking_slot, service_duration)

    customer_id = int(customer["id"])
    customer_email = customer["email"]
    try:
        staff = BookingService.pick_staff(
            staff_id,
            service_id,
            booking_date,
            start_time,
            end_time
        )
    except BookingValidatorError as e:
        flash(str(e), "error")
        return redirect(url_for('main.public_booking'))
    staff_id = staff["id"]

    # Online: tạo booking 'unverified' rồi chuyển sang Stripe (bỏ qua OTP).
    if data["payment_method"] == "online":
        booking_id = create_booking(customer_id, staff_id, service_id,
                                    booking_date, start_time, end_time,
                                    "unverified", note, "online")
        session["booking_id"] = booking_id  # để /success hiển thị chi tiết sau khi trả tiền
        return _redirect_to_stripe(booking_id, service_id, 'main.public_booking')

    booking_id, verification_id = BookingService.create(
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        note,
        customer_email,
        data["payment_method"]
    )

    session["booking_id"] = booking_id
    session["verify_context"] = {
        "type": "booking",
        "booking_id": booking_id,
        "email": customer_email,
        "verification_id": verification_id
    }

    return redirect(url_for('main.email_verification'))

@main.route("/payment/success")
def payment_success():
    # Fallback: xác nhận & fulfill ngay khi khách quay về (bù webhook trễ/thiếu),
    # rồi điều hướng theo loại thanh toán.
    next_url = url_for('main.home')
    next_label = "Continue"
    session_id = request.args.get("session_id")
    if session_id:
        try:
            ptype = fulfill_from_session(session_id)
        except Exception as e:
            print(f"[payment] success fallback failed: {e}")
            ptype = None
        if ptype == "booking":
            next_url, next_label = url_for('main.success'), "View booking now"
        elif ptype == "membership":
            next_url, next_label = url_for('main.tier_benefits'), "View my membership"
    return render_template("payment/success.html", next_url=next_url, next_label=next_label)

@main.route("/payment/cancel")
def payment_cancel():
    return render_template("payment/cancel.html")

@main.route("/payment/webhook", methods=["POST"])
@csrf.exempt
def payment_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = construct_event(payload, sig_header)
    except Exception as e:
        print(f"[payment] webhook verify failed: {e}")
        return "", 400

    handle_event(event)  # lỗi ở đây -> 500 để Stripe retry
    return "", 200

@main.route("/services")
def services():
    categories = get_active_service_categories()
    services_list = get_active_services_with_category()
    return render_template("/public/services.html", categories=categories, services=services_list)

@main.route("/gallery")
def gallery():
    images = get_gallery_images()
    return render_template("/public/gallery.html", images=images)

@main.route("/about")
def about():
    staff_members = get_active_staff()
    return render_template("/public/about.html", staff_members=staff_members)

@main.route("/success")
def success():
    booking_id = session.get("booking_id")
    if not booking_id:
        return redirect(url_for("main.home"))

    booking = get_booking_by_id(booking_id)
    if not booking:
        return redirect(url_for("main.home"))

    service = get_service_by_id(booking["service_id"])
    staff   = get_staff_by_id(booking["staff_id"])
    if not service or not staff:
        return redirect(url_for("main.home"))

    booking_date_obj = datetime.strptime(booking["booking_date"], "%Y-%m-%d")
    appointment_date = booking_date_obj.strftime("%A, %B %d, %Y")
    appointment_time = f"{format_booking_time(booking['start_time'])} (approx. {service['duration_minutes']} mins)"

    role_prefix   = f"{staff['role']}: " if staff["role"] else ""
    staff_display = f"With {role_prefix}{staff['full_name']}"

    service_image = (
        url_for("static", filename=f"uploads/services/{service['image']}")
        if service["image"] else None
    )

    cal           = build_calendar_url(service["name"], staff["full_name"], booking["booking_date"], booking["start_time"], booking["end_time"])
    salon_address = "Kyyhkysmäki 9, 02650 Espoo"

    return render_template(
        "/public/success.html",
        service_name=service["name"],
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        staff_display=staff_display,
        service_image=service_image,
        calendar_url=cal["url"],
        salon_address=salon_address,
        gg_map_url=build_gg_map_url(salon_address),
    )

@main.route("/register", methods=["GET", "POST"])
@guest_only
def register():
    if request.method == "GET":
        return render_template("Auth/customer_register.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    phone = request.form.get("phone", "").strip()


    if not full_name or not email or not password:
        flash("Please enter required information!", "error")
        return redirect(url_for('main.register'))

    existing_user = get_user_by_email(email)

    if existing_user:
        #Notice email existed
        flash("Email existed! Please try again.", "error")
        return redirect(url_for('main.register'))

    session.modified = True
    
    #Verification for register
    expires_at_raw = now_helsinki() + timedelta(minutes=5)
    expires_at = expires_at_raw.strftime("%Y-%m-%d %H:%M:%S")

    verification_code = generate_verification_code()
    verification_id = create_verification(verification_code, "register", expires_at)

    send_verification_email(email, verification_code, "register")

    session["pending_register"] = {
        "email": email,
        "full_name": full_name,
        "phone": phone,
        "password": password
    }
    session["verify_context"] = {
            "type": "register",
            "email": email,
            "verification_id":verification_id
    }

    #When user hit submit button from register form
    flash("A verification code has been sent to your email.", "success")
    return redirect(url_for('main.email_verification'))

@main.route("/login", methods=["GET", "POST"])
@guest_only
def login():
    if request.method == "GET":
        return render_template("/Auth/customer_login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Please enter email or password!", "error")
        return redirect(url_for('main.login'))
    
    user = get_user_by_email(email)

    if not user:
        flash("Invalid email or password!", "error")
        return redirect(url_for('main.login'))   

    user_id = user["id"]
    customer = get_customer_by_user_id(user_id)
    if not customer:
        flash("Profile not found! Please try again", "error")
        return redirect(url_for('main.login'))

    if not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password!", "error")
        return redirect(url_for('main.login'))
    else:
        ##set session
        session.clear()
        session["user_id"] = user_id
        session["role"] = user["role"]
        session["user_email"] = user["email"]
        session["customer_id"] = customer["id"]

        flash(f"Login successfully, welcome back {customer['full_name']}", "success")
        return redirect(url_for('main.customer_dashboard'))

@main.route("/auth/google")
@guest_only
def google_login():
    redirect_uri = url_for("main.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@main.route("/auth/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash("Google sign-in failed. Please try again.", "error")
        return redirect(url_for("main.login"))

    userinfo = token.get("userinfo") or {}
    email = (userinfo.get("email") or "").strip().lower()
    if not email or not userinfo.get("email_verified"):
        flash("Could not verify your Google email. Please try again.", "error")
        return redirect(url_for("main.login"))

    full_name = userinfo.get("name") or email.split("@")[0]
    sub = userinfo.get("sub")

    user = get_user_by_email(email)

    # OAuth chỉ dành cho customer — nếu email này là staff/admin thì chuyển sang cổng nhân viên
    if user and user["role"] != "customer":
        flash("Please use the staff login portal.", "error")
        return redirect(url_for("main.staff_login"))

    if user:
        user_id = user["id"]
        # Link tài khoản email/password cũ với Google nếu chưa gắn
        if not user["oauth_provider"]:
            set_user_oauth(user_id, "google", sub)
        customer = get_customer_by_user_id(user_id)
        if not customer:
            customer_id = create_customer(full_name, email, None)
            verify_customer(customer_id)
            link_customer_to_user(customer_id, user_id)
            customer = get_customer_by_user_id(user_id)
    else:
        user_id = create_oauth_user(email, "google", sub)
        customer = get_customer_by_email(email)
        if customer:
            link_customer_to_user(customer["id"], user_id)
        else:
            customer_id = create_customer(full_name, email, None)
            verify_customer(customer_id)
            link_customer_to_user(customer_id, user_id)
        customer = get_customer_by_user_id(user_id)

    session.clear()
    session["user_id"] = user_id
    session["role"] = "customer"
    session["user_email"] = email
    session["customer_id"] = customer["id"]

    flash(f"Login successfully, welcome {customer['full_name']}!", "success")
    return redirect(url_for("main.customer_dashboard"))

@main.route('/login/forgot-password', methods=['GET', 'POST'])
@guest_only
def forgot_password():
    if request.method == "GET":
        return render_template('/Auth/customer_forgot_password.html')

    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please enter your email address.", "error")
        return redirect(url_for("main.forgot_password"))

    user = get_user_by_email(email)
    if user and user["role"] == "customer":
        expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        code = generate_verification_code()
        verification_id = create_verification(code, "forgot_password", expires_at)
        send_verification_email(email, code, "forgot_password")
        session["verify_context"] = {
            "type": "forgot_password",
            "email": email,
            "verification_id": verification_id,
            "user_id": user["id"],
            "role": user["role"]
        }

    return redirect(url_for("main.email_verification"))

@main.route('/staff/forgot-password', methods=['GET', 'POST'])
@guest_only
def staff_forgot_password():
    if request.method == "GET":
        return render_template('/Auth/staff_forgot_password.html')

    email = request.form.get("email", "").strip().lower()
    if not email:
        flash("Please enter your email address.", "error")
        return redirect(url_for("main.staff_forgot_password"))

    user = get_user_by_email(email)
    if user and user["role"] in ("staff", "admin"):
        expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        code = generate_verification_code()
        verification_id = create_verification(code, "forgot_password", expires_at)
        send_verification_email(email, code, "forgot_password")
        session["verify_context"] = {
            "type": "forgot_password",
            "email": email,
            "verification_id": verification_id,
            "user_id": user["id"],
            "role": user["role"]
        }

    return redirect(url_for("main.email_verification"))

@main.route("/set-new-password", methods=["GET", "POST"])
@guest_only
def set_new_password():
    user_id = session.get("reset_user_id")
    if not user_id:
        flash("Session expired. Please try again.", "error")
        return redirect(url_for("main.forgot_password"))

    login_endpoint = "main.staff_login" if session.get("reset_role") in ("staff", "admin") else "main.login"

    if request.method == "GET":
        return render_template("/Auth/set_new_password.html", login_endpoint=login_endpoint)

    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if new_password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for("main.set_new_password"))

    if len(new_password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("main.set_new_password"))

    update_user_password(user_id, generate_password_hash(new_password))
    session.pop("reset_user_id", None)
    session.pop("reset_role", None)
    flash("Password reset successfully. Please log in.", "success")
    return redirect(url_for(login_endpoint))

@main.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('main.home'))

@main.route("/resend-verification-code", methods=["POST"])
def redo_verification():
    
    verify_context = session.get("verify_context")

    if not verify_context:
        flash("Your verification session has expired. Please start again.", "error")
        return redirect(url_for("main.home"))
    
    verification_id = verify_context.get("verification_id")
    email = verify_context.get("email")
    ##Clean up expired bookings (maybe not using this tool now)
    # delete_expired_verification_code()

    if not verification_id or not email:
        return jsonify({
            "success": False,
            "message": "Your verification has expired. Please start again."
        }), 400

    if not verification_id:
        return jsonify({
            "success": False,
            "message": "Your verification has expired. Please start again."
        }), 400
    
    verification = get_verification_by_id(verification_id)

    if not verification:
        return jsonify({
            "success": False,
            "message": "Your verification has expired. Please start again."
        }), 400
    

    
    expires_at_raw = now_helsinki() + timedelta(minutes=10)
    expires_at = expires_at_raw.strftime("%Y-%m-%d %H:%M:%S")
    
    #Cooldown resolve
    last_sent_raw = verification["last_sent_at"]
    last_sent_at = datetime.fromisoformat(last_sent_raw)
    now = now_helsinki()

    if now < last_sent_at + timedelta(seconds=60):
        remaining_sec = int(
            (last_sent_at + timedelta(seconds=60) - now).total_seconds()
        )
        
        return jsonify({
            "success": False,
            "message": f"Please wait {remaining_sec} seconds before requestion a new verification code!"
        }), 429 

    if not verification["is_used"]:
        
        new_code = generate_verification_code()
        update_new_code(verification_id, new_code, expires_at) 
        send_verification_email(email, new_code, verify_context.get("type", "booking"))
        
        return jsonify({
            "success": True,
            "message": "Resending new code success!"
        }), 200
    
    return jsonify({
        "success": False,
        "message": "Something went wrong :("
    }), 400

@main.route("/check-available-slots", methods=["GET"])
def check_available_slot():
    
    service_id_raw = request.args.get("service_id")
    staff_id_raw = request.args.get("staff_id")
    booking_date = request.args.get("booking_date")

    if not service_id_raw or not staff_id_raw or not booking_date:
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400

    try:
        service_id = int(service_id_raw)
        staff_id = int(staff_id_raw)
        datetime.strptime(booking_date.strip(), "%Y-%m-%d")
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid input data"
        }), 400
    
    service = get_service_by_id(service_id)
    if not service:
        return jsonify({
            "success": False,
            "message": "Service not found!"
        }), 404
    
    service_duration = service["duration_minutes"]

    #Case 1: When user select "No Preference"
    if staff_id == 0:
        staffs = get_all_staff()
        union_slots = set()

        for staff in staffs:
            if staff["is_active"] != 1:
                continue
            
            existing_bookings = get_booking_by_staff_and_date(
                staff['id'],
                booking_date
            )

            staff_slots = get_available_slots(
                service_duration,
                existing_bookings,
                "09:00",
                "18:00",
                30
            )
            union_slots.update(staff_slots)


        available_slots = [{
            "value": time,
            "label": datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
        } for time in sorted(union_slots)]

    else:
        staff = get_staff_by_id(staff_id)

        if not staff:
            return jsonify({
                "success": False,
                "message": "Staff not found"
            }),404

        existing_bookings = get_booking_by_staff_and_date(
            staff_id,
            booking_date
        )
        
        slots = get_available_slots(
            service_duration, 
            existing_bookings,
            "09:00", 
            "18:00", 
            30
        )
        
        available_slots = [{
            "value": time,
            "label": datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
        } for time in slots]
    
    return jsonify({
        "success": True,
        "available_slots": available_slots
    })

@main.route("/email-verification")
def email_verification():
    verify_context = session.get("verify_context", {})
    masked_email = mask_email(verify_context.get("email", ""))
    return render_template("/Auth/email_verification.html", email=masked_email)

@main.route("/verify-email", methods=["POST", "GET"])
def verify_email():


    #Browser send request "GET" to server (Request server to render template)
    if request.method == "GET":
        verify_context = session.get("verify_context", {})
        masked_email = mask_email(verify_context.get("email", ""))
        return render_template("/Auth/email_verification.html", email=masked_email)
    
    #Browser send request "POST" to server (Broswer send verification code to server for verifying then respone it back)
    if request.method == "POST":
 
        #Take data from browser
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid request format."
            }), 400
        user_code = data.get("verification_code", "").strip()

        verify_context = session.get("verify_context")
        if not verify_context:
            flash("Your verification session has expired. Please start again.","error")
            return jsonify({
                "success": False,
                "message": "Verification session has expired.",
                "redirect_url": url_for('main.home')
            }),400
        
        #Check verification có tồn tại hay không 
        verify_type = verify_context.get("type")
        verification_id = verify_context.get("verification_id")
        if not verification_id:
            return jsonify({
                "success": False,
                "message": "Verification code expired or not found. Please resend!",
                "redirect_url": url_for('main.home')
            }), 400
        verification = get_verification_by_id(verification_id)

        if not verification:
            return jsonify({
                "success": False,
                "message": "Verification code expired or not found. Please resend!"
            }), 400
        verification_code = verification["verification_code"]

        if verify_type == "register":

            #Register verification solve here!

            #register data
            pending_register = session.get("pending_register")
            if not pending_register:
                flash("Register session expired. Please register again.", "error")
                # return redirect(url_for("main.register"))
                return jsonify({
                    "success": False,
                    "message": "Register session expired. Please register again.",
                    "redirect_url": url_for('main.register')
                }),400

            full_name = pending_register.get("full_name")
            email = pending_register.get("email")
            phone = pending_register.get("phone")
            password = pending_register.get("password")

            if user_code == verification_code:
                    
                    #Register successfully solve
                    user_id = create_user(email, password)
                    customer = get_customer_by_email(email)
                    if customer:
                        customer_id = customer["id"]
                        link_customer_to_user(customer_id, user_id)
                    else:
                        customer_id = create_customer(full_name, email, phone)
                        link_customer_to_user(customer_id, user_id)

                    update_verification(verification_id, user_id, 1)
                    flash('Register successfully!', "success")
                    return jsonify({
                        "success": True,
                        "message": "Verify successfully!",
                        "redirect_url": url_for("main.login")
                    }), 200
            else:
                    flash('Invalid verification code!', "error")
                    return jsonify({
                        "success": False,
                        "message": "Invalid verification code"
                    }), 400

        if verify_type == "booking":
            #Booking verification solve here!
            booking_id = verify_context.get("booking_id")
            email = verify_context.get("email")

            if not booking_id or not email:
                return jsonify({
                    "success": False,
                    "message": "Booking not found. Please try again!"
                }), 400
            
            #Booking data
            booking = get_booking_by_id(booking_id)
            if not booking:
                return jsonify({
                    "success": False,
                    "message": "Booking not found. Please try again!",
                    "redirect_url": url_for('main.home')
                }), 400
            staff_id = booking["staff_id"]
            booking_date = booking["booking_date"]
            start_time = booking["start_time"]
            end_time = booking["end_time"]

            if user_code == verification_code:

                if check_booking_conflict(staff_id, booking_date, start_time, end_time):
                    flash("This slot has been booked by other customer! Please try again.", "error")
                    return jsonify({
                        "success": False,
                        "message": "This slot has been booked by other customer! Please try again.",
                        "redirect_url": url_for('main.public_booking')
                    }), 400

                #Booking successfully solve
                update_status(booking_id, "pending")
                customer_id = booking["customer_id"]
                customer = get_customer_by_customer_id(customer_id)
                if not customer:
                    return jsonify({
                        "success": False,
                        "message": "Customer not found. Please try again!",
                        "redirect_url": url_for('main.home')
                    }), 400
                verify_customer(customer_id)

                update_verification(verification_id, booking_id, 1)
                flash('Your booking is processing!', "success")

                ##Send thank you email to customer
                service = get_service_by_id(booking["service_id"])
                staff = get_staff_by_id(booking["staff_id"])
                if service and staff:
                    send_thank_you_email(customer["email"], customer["full_name"], service["name"], staff["full_name"], booking["booking_date"], booking["start_time"], booking["end_time"])

                return jsonify({
                    "success": True,
                    "message": "Verify successfully",
                    "redirect_url": url_for('main.success')
                }), 200
            
            else:
                return jsonify({
                    "success": False,
                    "message": "Invalid verification code. Please resend and try again!"
                })

        if verify_type == "forgot_password":
            user_id = verify_context.get("user_id")
            if not user_id:
                return jsonify({
                    "success": False,
                    "message": "Session expired. Please try again.",
                    "redirect_url": url_for("main.forgot_password")
                }), 400

            if user_code == verification_code:
                update_verification(verification_id, user_id, 1)
                session["reset_user_id"] = user_id
                session["reset_role"] = verify_context.get("role", "customer")
                session.pop("verify_context", None)
                return jsonify({
                    "success": True,
                    "message": "Code verified.",
                    "redirect_url": url_for("main.set_new_password")
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "message": "Invalid verification code. Please try again."
                }), 400

    #Clean up expired verifications



