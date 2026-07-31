"""Khởi tạo database — điểm khởi tạo duy nhất.

    python -m app.init_db                   # tạo schema (bảng rỗng)
    python -m app.init_db --seed            # tạo schema + nạp seed.sql
    python -m app.init_db --seed-services   # thêm seed_services.sql (kéo theo seed.sql)

Lưu ý: schema.sql bắt đầu bằng DROP TABLE — chạy sẽ xoá sạch dữ liệu cũ.
seed_services.sql cần service_categories từ seed.sql nên --seed-services luôn
nạp seed.sql trước.
"""
import argparse
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent / "database"
DB_PATH = DB_DIR / "database.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"
SEED_SERVICES_PATH = DB_DIR / "seed_services.sql"


def _run_sql(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def init_db(seed=False, seed_services=False):
    conn = sqlite3.connect(DB_PATH)
    try:
        _run_sql(conn, SCHEMA_PATH)
        print(f"Schema created ({SCHEMA_PATH.name})")
        if seed or seed_services:
            _run_sql(conn, SEED_PATH)
            print(f"Seed data loaded ({SEED_PATH.name})")
        if seed_services:
            _run_sql(conn, SEED_SERVICES_PATH)
            print(f"Seed data loaded ({SEED_SERVICES_PATH.name})")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Init the app database (schema, optional seed).")
    parser.add_argument("--seed", action="store_true", help="also load seed.sql")
    parser.add_argument("--seed-services", action="store_true",
                        help="also load seed_services.sql (implies --seed)")
    args = parser.parse_args()
    init_db(seed=args.seed, seed_services=args.seed_services)
