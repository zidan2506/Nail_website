from flask import Blueprint, flash,render_template, request, jsonify, redirect, url_for, session
from app.database.db import get_customer_appointment_history, get_customer_invoices, get_active_services_with_category ,get_active_service_categories ,update_booking_schedule, get_customer_by_customer_id ,get_customer_bookings ,get_staff_by_user_id ,get_customer_by_user_id ,update_verification ,get_verification_by_id ,create_verification ,link_customer_to_user ,get_customer_by_email, create_user ,get_user_by_email, verify_customer,get_all_services, get_all_staff, get_service_by_id, get_staff_by_id, check_booking_conflict, get_customer_id, create_booking, create_customer,update_status, get_booking_by_id, update_new_code, get_booking_by_staff_and_date
from datetime import datetime, timedelta, UTC, date
from app.services.email_authentication import send_verification_email, send_thank_you_email, generate_verification_code
from app.services.booking_service import GuestService, BookingService, BookingValidatorError, GuestInfoMissingError,get_available_slots, get_following_days
from werkzeug.security import check_password_hash
from functools import wraps
from app.utils.helpers import split_customer_bookings, format_booking_date, format_booking_time, build_calendar_url, build_gg_map_url, build_services_by_category
from collections import Counter
main = Blueprint("main",__name__)

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
@main.route("/customer")
@customer_login_required
def customer_dashboard():    
    user_id = session.get('user_id')
    customer = get_customer_by_user_id(user_id)
    
    return render_template("/customer/customer_dashboard.html", customer=customer)

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

    return render_template(
        "/customer/customer_booking.html",
        categories=categories,
        services_by_category=services_by_category,
        staffs=staffs,
        today=today,
        max_date=max_date,
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
    
    update_status(booking_id, "cancelled")

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

    all_bookings = get_customer_bookings(customer_id)

    if not all_bookings:
        flash("Bookings not found!", "error")
        return redirect(url_for('main.customer_dashboard'))
    
    booking_groups = split_customer_bookings(all_bookings)

    #Next-visit card's data
    next_visit = booking_groups["next_visit"]

    if not next_visit:
        flash("No upcoming bookings!", "error")
        return redirect(url_for('main.customer_dashboard'))
    
    next_visit_status = next_visit["status"] #frontend
    next_visit_service_id = next_visit["service_id"]
    next_visit_service = get_service_by_id(next_visit_service_id)
    if not next_visit_service:
        flash("Service data unavailable.", "error")
        return redirect(url_for('main.customer_dashboard'))
    next_visit_service_name = next_visit_service["name"] #frontend
    next_visit_staff_id = next_visit["staff_id"]
    next_visit_staff = get_staff_by_id(next_visit_staff_id)
    if not next_visit_staff:
        flash("Staff data unavailable.", "error")
        return redirect(url_for('main.customer_dashboard'))
    next_visit_staff_name = next_visit_staff["full_name"] #frontend
    next_visit_booking_date_raw = next_visit["booking_date"]
    next_visit_booking_date = format_booking_date(next_visit_booking_date_raw)
    next_visit_start_time_raw = next_visit["start_time"]
    next_visit_start_time = format_booking_time(next_visit_start_time_raw) #frontend
    next_visit_end_time_raw = next_visit["end_time"]

    #Manage Appointments card's data
    upcoming_bookings = booking_groups["upcoming_bookings"]
    pending_bookings = booking_groups["pending_bookings"]
    cancelled_bookings = booking_groups["cancelled_bookings"]

    ##Add calendar btn solve
    next_visit_calendar_url = build_calendar_url( next_visit_service_name, next_visit_staff_name, next_visit_booking_date_raw, next_visit_start_time_raw,next_visit_end_time_raw)
    return render_template(
        "/customer/my_bookings.html",
        nevi_status=next_visit_status,
        nevi_service= next_visit_service_name,
        nevi_staff=next_visit_staff_name,
        nevi_date=next_visit_booking_date,
        nevi_start=next_visit_start_time,
        next_visit= next_visit,
        calendar_url= next_visit_calendar_url["url"],
        url_target= next_visit_calendar_url["url_target"],
        upcoming_bookings=upcoming_bookings,
        pending_bookings=pending_bookings,
        cancelled_bookings=cancelled_bookings,
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
    return render_template("/customer/customer_setting.html")

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

#====================================
#               Staff
#====================================
@main.route("/staff")
def staff_dashboard():
    return render_template("/staff/staff_dashboard.html")

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

@main.route("/book")
def book():
    services_list = get_all_services()
    staff_list = get_all_staff()
    date_list = get_following_days(7)

    user_id = session.get('user_id')
    role = session.get('role')
    if user_id:
        if role == 'customer':
            return redirect(url_for('main.customer_booking'))
    #Renew session's data
    session.pop("booking_id", None)


    return render_template("book.html", services=services_list, staffs=staff_list, dates=date_list)

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

    send_verification_email(email, verification_code)

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
        send_verification_email(email,new_code)
        
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



