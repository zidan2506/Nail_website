import os
from flask import Blueprint, flash,render_template, request, jsonify, redirect, url_for, session
from app.database.db import get_connection, get_invoice_detail_by_id, get_customer_appointment_history, get_customer_invoices, get_active_services_with_category ,get_active_service_categories ,update_booking_schedule, get_customer_by_customer_id ,get_customer_bookings ,get_staff_by_user_id ,get_customer_by_user_id ,update_verification ,get_verification_by_id ,create_verification ,link_customer_to_user ,get_customer_by_email, create_user ,get_user_by_email, verify_customer,get_all_services, get_all_staff, get_service_by_id, get_staff_by_id, check_booking_conflict, get_customer_id, create_booking, create_customer,update_status, get_booking_by_id, update_new_code, get_booking_by_staff_and_date, get_loyalty_balance, get_active_rewards, get_loyalty_history, get_customer_active_tier, get_tier_by_name, upgrade_membership, has_source_award, has_pending_review, get_customer_reward_status, redeem_reward, get_customer_vouchers, update_customer_profile, update_user_email, update_user_password, cancel_booking_with_reason
from datetime import datetime, timedelta, UTC, date
from app.services.email_system import send_verification_email, send_thank_you_email, generate_verification_code
from app.services.booking_service import GuestService, BookingService, BookingValidatorError, GuestInfoMissingError,get_available_slots, get_following_days
from app.services.loyalty import get_active_multiplier, get_config_value, already_awarded, award_points, check_streak
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from app.utils.helpers import split_customer_bookings, format_booking_date, format_booking_time, build_calendar_url, build_gg_map_url, build_services_by_category
from collections import Counter
main = Blueprint("main",__name__)

_AVATAR_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "avatars")
_ALLOWED_AVATAR_EXT = {"jpg", "jpeg", "png", "gif"}

#Server config
def customer_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        customer_id = session.get('customer_id')
        if not customer_id:
            flash("Please login!", "error")
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapped_view

#Server routes
@main.route("/")
def home():
    return render_template("/public/home.html")

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
    today = date.today()

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
    carousel_rewards = [dict(r) for r in all_rewards[:3]]

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

@main.route("/customer/my-profile")
@customer_login_required
def my_profile():
    return render_template("customer_profile.html")

@main.route("/customer/booking")
@customer_login_required
def customer_booking():

    today = date.today()
    max_date = today + timedelta(days=60)

    categories = get_active_service_categories()
    services = get_active_services_with_category()
    staffs = get_all_staff()

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
    today = date.today()
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
            and item["status"] in ("pending", "confirmed")
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
    
    today = date.today()
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
        and item["status"] in ("pending", "confirmed")
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

    profile_picture = None
    for ext in _ALLOWED_AVATAR_EXT:
        candidate = os.path.join(_AVATAR_DIR, f"{user_id}.{ext}")
        if os.path.exists(candidate):
            profile_picture = url_for("static", filename=f"uploads/avatars/{user_id}.{ext}")
            break

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

    if not file or not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("main.customer_setting"))

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in _ALLOWED_AVATAR_EXT:
        flash("Invalid file type. JPG, GIF or PNG only.", "error")
        return redirect(url_for("main.customer_setting"))

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 800 * 1024:
        flash("File is too large. Max size is 800KB.", "error")
        return redirect(url_for("main.customer_setting"))

    os.makedirs(_AVATAR_DIR, exist_ok=True)
    for old_ext in _ALLOWED_AVATAR_EXT:
        old_path = os.path.join(_AVATAR_DIR, f"{user_id}.{old_ext}")
        if os.path.exists(old_path):
            os.remove(old_path)

    save_path = os.path.join(_AVATAR_DIR, f"{user_id}.{ext}")
    file.save(save_path)

    flash("Profile picture updated.", "success")
    return redirect(url_for("main.customer_setting"))


@main.route("/customer/setting/request-password-change", methods=["POST"])
@customer_login_required
def request_password_change():
    user_id = session.get("user_id")
    customer = get_customer_by_user_id(user_id)
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."}), 404

    expires_at = (datetime.now(UTC) + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
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

    expires_at = (datetime.now(UTC) + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
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

    completed_appointments = [a for a in appointments if a['status'] == 'completed']
    
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

    booking_id, verification_id = BookingService.create(
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        note,
        customer_email
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

    #redir tới page checkout ở đây
    upgrade_membership(customer["id"], tier["id"], tier["duration_days"])
    flash(f"Successfully upgraded to {tier['name']} plan!", "success")
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
                    if datetime.now() < reset_dt:
                        remaining = max((reset_dt - datetime.now()).days, 1)
                        return _err(f"This reward resets in {remaining} day(s).")
                except (ValueError, TypeError):
                    pass
            else:
                return _err("You've reached the redeem limit for this reward.")

    redeem_reward(customer_id, reward_id, reward["cost"], reward["name"])
    flash(f"Successfully redeemed: {reward['name']}!", "success")
    if is_json:
        return jsonify({"success": True})

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

    active_tier = get_customer_active_tier(customer["id"])
    current_plan = active_tier["name"].lower() if active_tier else "silver"

    expires_at = None
    if active_tier and active_tier.get("expires_at"):
        try:
            expires_at = datetime.strptime(active_tier["expires_at"], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
        except ValueError:
            expires_at = active_tier["expires_at"]

    return render_template(
        "customer/customer_membership.html",
        current_plan=current_plan,
        expires_at=expires_at,
    )

@main.route("/customer/rewards")
@customer_login_required
def all_rewards():
    return render_template("customer/coming_soon.html", feature_name="All Rewards")

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
    active_tier = get_customer_active_tier(customer_id)
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
                        if datetime.now() < reset_dt:
                            hit_limit          = True
                            cooldown_remaining = max((reset_dt - datetime.now()).days, 1)
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
            "img":               "",
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
    )

@main.route("/customer/loyalty-points/redeem-terms")
@customer_login_required
def redeem_terms():
    return render_template("customer/coming_soon.html", feature_name="Redeem Terms")

#====================================
#               Staff
#====================================
@main.route("/staff")
def staff_dashboard():
    return render_template("/staff/staff_dashboard.html")

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

    service = get_service_by_id(booking["service_id"])
    if not service:
        flash("Service not found.", "error")
        return redirect(url_for("main.staff_dashboard"))

    customer_id = booking["customer_id"]
    booking_date = booking["booking_date"]

    multiplier = get_active_multiplier(customer_id)
    base_points = int((service["points"] or 0) * multiplier)
    double_points_day = get_config_value("double_points_day")
    booking_day = datetime.strptime(booking_date, "%Y-%m-%d").isoweekday()
    streak_ref = int(datetime.strptime(booking_date, "%Y-%m-%d").strftime("%Y%m"))

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE bookings SET status = 'completed' WHERE id = ?",
            (booking_id,)
        )

        # 1. Base points
        if base_points > 0 and not already_awarded(customer_id, "booking", booking_id):
            award_points(customer_id, base_points, "booking", booking_id,
                         f"{service['name']} × {multiplier}", conn=conn)

        # 2. Double points day bonus
        if double_points_day and booking_day == double_points_day:
            if not already_awarded(customer_id, "double_points", booking_id):
                award_points(customer_id, base_points, "double_points", booking_id,
                             "Double points day bonus", conn=conn)

        # 3. First booking bonus — count AFTER the update (same conn sees uncommitted write)
        row = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE customer_id = ? AND status = 'completed'",
            (customer_id,)
        ).fetchone()
        if row[0] == 1:
            first_bonus = get_config_value("first_booking_bonus")
            if first_bonus and not already_awarded(customer_id, "first_booking", booking_id):
                award_points(customer_id, first_bonus, "first_booking", booking_id,
                             "First booking bonus", conn=conn)

        # 4. Streak bonus — pass conn so check sees uncommitted UPDATE
        if check_streak(customer_id, booking_date, conn=conn):
            streak_bonus = get_config_value("streak_bonus")
            if streak_bonus and not already_awarded(customer_id, "streak", streak_ref):
                award_points(customer_id, streak_bonus, "streak", streak_ref,
                             "3-month streak bonus", conn=conn)

        conn.commit()
        flash("Booking marked as completed.", "success")
    except Exception:
        conn.rollback()
        flash("Something went wrong. Please try again.", "error")
    finally:
        conn.close()

    return redirect(url_for("main.staff_dashboard"))

#====================================
#               Admin
#====================================
@main.route("/admin")
def admin_dashboard():
    return render_template("/admin/admin_dashboard.html")

#====================================
#               Public
#====================================
@main.route("/public/booking")
def public_booking():
    today = date.today()
    max_date = today + timedelta(days=60)

    categories = get_active_service_categories()
    services = get_active_services_with_category()
    staffs = get_all_staff()

    services_by_category = build_services_by_category(categories, services)

    return render_template(
        "/public/public_booking.html",
        categories=categories,
        services_by_category=services_by_category,
        staffs=staffs,
        today=today,
        max_date=max_date,
    )
@main.route("/public/create-booking", methods=['POST'])
def create_booking():
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

    booking_id, verification_id = BookingService.create(
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        note,
        customer_email
    )

    session["booking_id"] = booking_id
    session["verify_context"] = {
        "type": "booking",
        "booking_id": booking_id,
        "email": customer_email,
        "verification_id": verification_id
    }

    return redirect(url_for('main.email_verification'))


@main.route("/services")
def services():
    services_list = get_all_services()
    return render_template("/public/services.html", services=services_list)

@main.route("/success")
def success():
    return render_template("success.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("public/customer_register.html")


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
    expires_at_raw = datetime.now(UTC) + timedelta(minutes=5)
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
def login():
    if request.method == "GET":
        return render_template("/public/customer_login.html")

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


@main.route('/staff/login', methods=['POST', 'GET'])
def staff_login():
    if request.method == "GET":
        return render_template("/staff/staff_login.html")
    
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password","")

    if not email or not password:
        flash("Please enter email or password!", "error")
        return redirect(url_for("main.staff_login"))
    
    user = get_user_by_email(email)

    if not user:
        flash("Invalid email or password!", "error")
        return redirect(url_for("main.staff_login"))
    
    user_id = user['id']

    if not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password!", "error")
        return redirect(url_for("main.staff_login"))

    if user["role"] not in ("staff", "admin"):
        flash("Please use the customer login portal", "error")
        return redirect(url_for("main.login"))

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
        flash(f"Login successfully. Welcome master!", "success")
        return redirect(url_for("main.admin_dashboard"))
    
    flash("something went wrong :(", "error")
    return redirect(url_for("main.staff_login"))

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
    

    
    expires_at_raw = datetime.now(UTC) + timedelta(minutes=10)
    expires_at = expires_at_raw.strftime("%Y-%m-%d %H:%M:%S")
    
    #Cooldown resolve
    last_sent_raw = verification["last_sent_at"]
    last_sent_at = datetime.fromisoformat(last_sent_raw).replace(tzinfo=UTC)
    now_utc = datetime.now(UTC)

    if now_utc < last_sent_at + timedelta(seconds=60):
        remaining_sec = int(
            (last_sent_at + timedelta(seconds=60) - now_utc).total_seconds()
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
    return render_template("email_verification.html")

@main.route("/verify-email", methods=["POST", "GET"])
def verify_email():


    #Browser send request "GET" to server (Request server to render template)
    if request.method == "GET":
        return render_template("email_verification.html")
    
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
                        "redirect_url": url_for('main.book')
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
            

    
        

    #Clean up expired verifications



