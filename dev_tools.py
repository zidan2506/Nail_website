#!/usr/bin/env python3
"""
Dev/debug CLI for the nail booking app.

Usage:
  python dev_tools.py booking set-status <booking_id> <status>
  python dev_tools.py booking list [--status <status>] [--customer <customer_id>]
  python dev_tools.py points show <customer_id>
  python dev_tools.py points add <user_id> <amount> [--note "reason"]
  python dev_tools.py points subtract <user_id> <amount> [--note "reason"]

Examples:
  python dev_tools.py points add 3 500 --note "Manual top-up"
  python dev_tools.py points subtract 3 200 --note "Correction"
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Allow importing app modules from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.db import get_connection, get_booking_by_id, get_service_by_id
from app.services.loyalty import (
    get_active_multiplier, get_config_value,
    already_awarded, award_points, check_streak,
)

VALID_STATUSES = {"unverified", "pending", "confirmed", "completed", "cancelled"}


# ─────────────────────────────────────────────
#  booking set-status
# ─────────────────────────────────────────────

def cmd_booking_set_status(booking_id: int, status: str):
    booking = get_booking_by_id(booking_id)
    if not booking:
        print(f"Error: booking {booking_id} not found.")
        sys.exit(1)

    old_status = booking["status"]

    if status != "completed":
        conn = get_connection()
        conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        conn.commit()
        conn.close()
        print(f"Booking {booking_id}: {old_status} → {status}")
        return

    # completed → trigger loyalty flow in same transaction
    service = get_service_by_id(booking["service_id"])
    if not service:
        conn = get_connection()
        conn.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))
        conn.commit()
        conn.close()
        print(f"Booking {booking_id}: {old_status} → completed")
        print("Warning: service not found — no loyalty points awarded.")
        return

    customer_id   = booking["customer_id"]
    booking_date  = booking["booking_date"]
    multiplier    = get_active_multiplier(customer_id)
    base_points   = int((service["points"] or 0) * multiplier)
    double_day    = get_config_value("double_points_day")
    booking_day   = datetime.strptime(booking_date, "%Y-%m-%d").isoweekday()
    streak_ref    = int(datetime.strptime(booking_date, "%Y-%m-%d").strftime("%Y%m"))

    awarded = []

    conn = get_connection()
    try:
        conn.execute("UPDATE bookings SET status = 'completed' WHERE id = ?", (booking_id,))

        # 1. Base points
        if base_points > 0 and not already_awarded(customer_id, "booking", booking_id):
            award_points(customer_id, base_points, "booking", booking_id,
                         f"{service['name']} × {multiplier}", conn=conn)
            awarded.append(f"  +{base_points:>5}  base points  ({service['name']} × {multiplier})")

        # 2. Double points day bonus
        if double_day and booking_day == double_day:
            if not already_awarded(customer_id, "double_points", booking_id):
                award_points(customer_id, base_points, "double_points", booking_id,
                             "Double points day bonus", conn=conn)
                awarded.append(f"  +{base_points:>5}  double points day bonus")

        # 3. First booking bonus (count after UPDATE — same conn sees uncommitted write)
        row = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE customer_id = ? AND status = 'completed'",
            (customer_id,)
        ).fetchone()
        if row[0] == 1:
            first_bonus = get_config_value("first_booking_bonus")
            if first_bonus and not already_awarded(customer_id, "first_booking", booking_id):
                award_points(customer_id, first_bonus, "first_booking", booking_id,
                             "First booking bonus", conn=conn)
                awarded.append(f"  +{first_bonus:>5}  first booking bonus")

        # 4. Streak bonus
        if check_streak(customer_id, booking_date, conn=conn):
            streak_bonus = get_config_value("streak_bonus")
            if streak_bonus and not already_awarded(customer_id, "streak", streak_ref):
                award_points(customer_id, streak_bonus, "streak", streak_ref,
                             "3-month streak bonus", conn=conn)
                awarded.append(f"  +{streak_bonus:>5}  3-month streak bonus")

        conn.commit()
        print(f"Booking {booking_id}: {old_status} → completed")
        if awarded:
            print("Loyalty points awarded:")
            for line in awarded:
                print(line)
        else:
            print("No new loyalty points awarded (already awarded or service has 0 points).")

    except Exception as e:
        conn.rollback()
        print(f"Error: transaction rolled back — {e}")
        sys.exit(1)
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  booking list
# ─────────────────────────────────────────────

def cmd_booking_list(status=None, customer_id=None):
    conn = get_connection()

    query = """
        SELECT b.id, b.customer_id, c.full_name AS customer_name,
               s.name AS service_name,
               b.booking_date, b.start_time, b.status
        FROM bookings b
        JOIN customers c ON b.customer_id = c.id
        JOIN services  s ON b.service_id  = s.id
        WHERE 1=1
    """
    params = []

    if status:
        query += " AND b.status = ?"
        params.append(status)
    if customer_id:
        query += " AND b.customer_id = ?"
        params.append(customer_id)

    query += " ORDER BY b.booking_date DESC, b.start_time DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("No bookings found.")
        return

    col = (6, 24, 24, 12, 8, 12)
    header = (
        f"{'ID':<{col[0]}} {'Customer':<{col[1]}} {'Service':<{col[2]}}"
        f" {'Date':<{col[3]}} {'Time':<{col[4]}} {'Status':<{col[5]}}"
    )
    print(header)
    print("─" * len(header))
    for r in rows:
        print(
            f"{r['id']:<{col[0]}} {r['customer_name']:<{col[1]}} {r['service_name']:<{col[2]}}"
            f" {r['booking_date']:<{col[3]}} {r['start_time']:<{col[4]}} {r['status']:<{col[5]}}"
        )
    print(f"\n{len(rows)} booking(s) found.")


# ─────────────────────────────────────────────
#  points show
# ─────────────────────────────────────────────

def cmd_points_show(customer_id: int):
    conn = get_connection()

    customer = conn.execute(
        "SELECT full_name FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()

    if not customer:
        conn.close()
        print(f"Error: customer {customer_id} not found.")
        sys.exit(1)

    total = conn.execute(
        "SELECT COALESCE(SUM(points), 0) AS total FROM loyalty_points_log WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()["total"]

    logs = conn.execute("""
        SELECT id, points, source, reference_id, note, created_at
        FROM loyalty_points_log
        WHERE customer_id = ?
        ORDER BY created_at DESC
    """, (customer_id,)).fetchall()

    conn.close()

    print(f"Customer : {customer['full_name']} (id={customer_id})")
    print(f"Total    : {total} pts")

    if not logs:
        print("No points history.")
        return

    print()
    col = (6, 8, 16, 10, 36, 20)
    header = (
        f"{'ID':<{col[0]}} {'Points':>{col[1]}} {'Source':<{col[2]}}"
        f" {'Ref ID':<{col[3]}} {'Note':<{col[4]}} {'Created at':<{col[5]}}"
    )
    print(header)
    print("─" * len(header))
    for log in logs:
        ref  = str(log["reference_id"]) if log["reference_id"] is not None else "—"
        note = (log["note"] or "")[:35]
        sign = "+" if log["points"] >= 0 else ""
        print(
            f"{log['id']:<{col[0]}} {sign + str(log['points']):>{col[1]}} {log['source']:<{col[2]}}"
            f" {ref:<{col[3]}} {note:<{col[4]}} {log['created_at']:<{col[5]}}"
        )
    print(f"\n{len(logs)} log entr{'y' if len(logs) == 1 else 'ies'}.")


# ─────────────────────────────────────────────
#  points add / subtract
# ─────────────────────────────────────────────

def _resolve_customer_by_user_id(conn, user_id: int):
    row = conn.execute(
        "SELECT id, full_name FROM customers WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row:
        print(f"Error: no customer found for user_id={user_id}.")
        sys.exit(1)
    return row


def cmd_points_add(user_id: int, amount: int, note: str):
    conn = get_connection()
    customer = _resolve_customer_by_user_id(conn, user_id)
    customer_id = customer["id"]

    award_points(customer_id, amount, "manual_add", reference_id=None, note=note, conn=conn)
    conn.commit()
    conn.close()
    print(f"Customer : {customer['full_name']} (user_id={user_id})")
    print(f"Added    : +{amount} pts")
    print(f"Note     : {note or '—'}")


def cmd_points_subtract(user_id: int, amount: int, note: str):
    conn = get_connection()
    customer = _resolve_customer_by_user_id(conn, user_id)
    customer_id = customer["id"]

    earned = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM loyalty_points_log WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    redeemed = conn.execute(
        "SELECT COALESCE(SUM(points_spent), 0) FROM reward_redemptions WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    balance = int(earned - redeemed)

    if amount > balance:
        conn.close()
        print(f"Error: cannot subtract {amount} pts — current balance is only {balance} pts.")
        sys.exit(1)

    award_points(customer_id, -amount, "manual_subtract", reference_id=None, note=note, conn=conn)
    conn.commit()
    conn.close()
    print(f"Customer : {customer['full_name']} (user_id={user_id})")
    print(f"Subtracted: -{amount} pts  (balance before: {balance}, after: {balance - amount})")
    print(f"Note     : {note or '—'}")


# ─────────────────────────────────────────────
#  CLI entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="dev_tools.py",
        description="Dev/debug CLI for the nail booking app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── booking ──
    booking_p = sub.add_parser("booking", help="Booking operations")
    booking_sub = booking_p.add_subparsers(dest="booking_action", required=True)

    ss = booking_sub.add_parser("set-status", help="Change booking status")
    ss.add_argument("booking_id", type=int, help="Booking ID")
    ss.add_argument("status", choices=sorted(VALID_STATUSES), help="New status")

    ls = booking_sub.add_parser("list", help="List bookings")
    ls.add_argument("--status",   choices=sorted(VALID_STATUSES), default=None)
    ls.add_argument("--customer", type=int, default=None, dest="customer_id",
                    metavar="CUSTOMER_ID")

    # ── points ──
    points_p = sub.add_parser("points", help="Loyalty points operations")
    points_sub = points_p.add_subparsers(dest="points_action", required=True)

    ps = points_sub.add_parser("show", help="Show points for a customer")
    ps.add_argument("customer_id", type=int, help="Customer ID")

    pa = points_sub.add_parser("add", help="Add points to a user")
    pa.add_argument("user_id", type=int, help="User ID")
    pa.add_argument("amount", type=int, help="Points to add (positive integer)")
    pa.add_argument("--note", default="", help="Reason for adjustment")

    psu = points_sub.add_parser("subtract", help="Subtract points from a user")
    psu.add_argument("user_id", type=int, help="User ID")
    psu.add_argument("amount", type=int, help="Points to subtract (positive integer)")
    psu.add_argument("--note", default="", help="Reason for adjustment")

    args = parser.parse_args()

    if args.command == "booking":
        if args.booking_action == "set-status":
            cmd_booking_set_status(args.booking_id, args.status)
        elif args.booking_action == "list":
            cmd_booking_list(status=args.status, customer_id=args.customer_id)

    elif args.command == "points":
        if args.points_action == "show":
            cmd_points_show(args.customer_id)
        elif args.points_action == "add":
            cmd_points_add(args.user_id, args.amount, args.note)
        elif args.points_action == "subtract":
            cmd_points_subtract(args.user_id, args.amount, args.note)


if __name__ == "__main__":
    main()
 