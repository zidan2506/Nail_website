"""One-time setup: tạo Stripe Product + recurring Price (monthly) cho các tier
trả phí (price > 0, vd Gold/Diamond) rồi lưu stripe_price_id vào membership_tiers.

Idempotent: tier đã có stripe_price_id sẽ bỏ qua. Silver (miễn phí) không tạo.
Charge phẳng theo membership_tiers.price (chưa cộng VAT — VAT cho subscription
cần Stripe Tax, làm sau nếu cần).

Chạy:  python -m app.database.setup_stripe_prices
"""

import os
import sys

import stripe

# Cho phép chạy trực tiếp (python app/database/setup_stripe_prices.py) lẫn dạng
# module (python -m app.database.setup_stripe_prices): thêm project root vào path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from app.database.db import get_connection


def setup():
    app = create_app()
    with app.app_context():
        stripe.api_key = app.config["STRIPE_SECRET_KEY"]
        conn = get_connection()
        tiers = conn.execute(
            "SELECT id, name, price, stripe_price_id FROM membership_tiers "
            "WHERE is_active = 1 AND price > 0"
        ).fetchall()
        for t in tiers:
            if t["stripe_price_id"]:
                print(f"skip {t['name']} (da co {t['stripe_price_id']})")
                continue
            product = stripe.Product.create(name=f"DahaCare {t['name']} Membership")
            price = stripe.Price.create(
                product=product.id,
                currency="eur",
                unit_amount=int(round(t["price"] * 100)),
                recurring={"interval": "month"},
            )
            conn.execute(
                "UPDATE membership_tiers SET stripe_price_id = ? WHERE id = ?",
                (price.id, t["id"]),
            )
            conn.commit()
            print(f"{t['name']}: created {price.id} (EUR {t['price']}/thang)")
        conn.close()


if __name__ == "__main__":
    setup()
