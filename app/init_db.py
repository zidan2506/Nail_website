"""Khởi tạo database — điểm khởi tạo duy nhất.

    python -m app.init_db           # tạo schema (bảng rỗng)
    python -m app.init_db --seed    # tạo schema + nạp seed.sql

Lưu ý: schema.sql bắt đầu bằng DROP TABLE — chạy sẽ xoá sạch dữ liệu cũ.
"""
import argparse
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent / "database"
DB_PATH = DB_DIR / "database.db"
SCHEMA_PATH = DB_DIR / "schema.sql"
SEED_PATH = DB_DIR / "seed.sql"


def _run_sql(conn, path):
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def init_db(seed=False):
    conn = sqlite3.connect(DB_PATH)
    try:
        _run_sql(conn, SCHEMA_PATH)
        print(f"Schema created ({SCHEMA_PATH.name})")
        if seed:
            _run_sql(conn, SEED_PATH)
            print(f"Seed data loaded ({SEED_PATH.name})")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Khởi tạo database cho app.")
    parser.add_argument("--seed", action="store_true", help="nạp thêm seed.sql")
    args = parser.parse_args()
    init_db(seed=args.seed)
