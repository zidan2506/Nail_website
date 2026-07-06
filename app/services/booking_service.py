from app.utils.helpers import parse_time, now_helsinki, today_helsinki
from datetime import timedelta
from datetime import datetime
from app.services.email_system import generate_verification_code, send_verification_email
from app.database.db import get_staff_by_id, get_available_staff_for_slot , get_customer_by_email , create_customer, create_verification, create_booking, get_customer_id
import random

def is_overlap(candidate_start, candidate_end, existing_start, existing_end):
    return candidate_start < existing_end and candidate_end > existing_start

def get_available_slots(duration_min, existing_bookings, open_time="09:00", close_time="18:00", step_minutes=30):
    available_slots = []
    
    current = parse_time(open_time)
    close_dt = parse_time(close_time)
    service_duration = timedelta(minutes=duration_min)

    while current + service_duration <= close_dt:
        candidate_start = current
        candidate_end = current + service_duration

        conflict = False

        for booking in existing_bookings:
            existing_start = parse_time(booking["start_time"])
            existing_end = parse_time(booking["end_time"])

            if is_overlap(candidate_start, candidate_end, existing_start, existing_end):
                conflict = True
                break
        
        if not conflict:
            available_slots.append(candidate_start.strftime("%H:%M"))

        current += timedelta(minutes=step_minutes)

    return available_slots

def get_following_days(n_days):
    date_list = []
    today = today_helsinki()

    for i in range(n_days):
        current_date = today + timedelta(days=i)
        date_list.append({
            "value": current_date.strftime("%Y-%m-%d"),
            "label": current_date.strftime("%d %b")
        })
    return date_list


#Error handling
class GuestInfoMissingError(Exception):
    pass

class BookingValidatorError(Exception):
    pass

class GuestService:
    @staticmethod
    def resolve_customer_info(form):
        name = form.get("full_name", "").strip()
        phone = form.get("phone", "").strip()
        email = form.get("email", "").strip()


        if not name or not phone or not email:
            raise GuestInfoMissingError("Please fill in guest information")

        customer = get_customer_by_email(email)
        if customer is None:
            create_customer(name, email, phone)
            customer = get_customer_by_email(email)
        return customer
        
    
class BookingService:
    @staticmethod
    def parse_form(form):
        return {
            "note": form.get("note", "").strip(),
            "service_id": int(form.get("service_id", "").strip()),
            "staff_id": int(form.get("staff_id", "").strip()),
            "booking_date": form.get("booking_date", "").strip(),
            "slot": form.get("start_time", "").strip(),
        }
    
    def parse_slot(booking_date, slot, duration_minutes):
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(slot, "%H:%M").time()
        start_at = datetime.combine(date_obj, time_obj)
        end_at = start_at + timedelta(minutes=duration_minutes)
        return start_at.strftime("%H:%M"), end_at.strftime("%H:%M")
    
    def pick_staff(staff_id, service_id, booking_date, start_time, end_time):
        
        staff_id = int(staff_id)
        service_id = int(service_id)

        if staff_id != 0:
            staff = get_staff_by_id(staff_id)
            return staff 

        availalble = get_available_staff_for_slot(
            booking_date,
            start_time,
            end_time
        )
        
        if not availalble:
            raise BookingValidatorError("No staff availalble for this slot")
        
        picked = random.choice(availalble)
        return picked
    
    def create(customer_id, staff_id, service_id, booking_date, start_time, end_time, note, email):
        booking_id = create_booking(customer_id, staff_id, service_id, booking_date, start_time, end_time, "unverified", note)
        verification_id = VerificationService.create_booking_verification(email)
        return booking_id, verification_id
    
class VerificationService:
    @staticmethod
    def create_booking_verification(email):
        code = generate_verification_code()
        send_verification_email(email, code, "booking")
        expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        verification_id = create_verification(code, "booking", expires_at)
        return verification_id

