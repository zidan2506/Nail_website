import sqlite3
from pathlib import Path

base_dir = Path(__file__).resolve().parent
db_path = base_dir / "database.db"

def get_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def reset_tables():
    conn = get_connection()
    conn.execute("DELETE FROM bookings")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='bookings';")
    conn.commit()
    conn.close()
reset_tables()