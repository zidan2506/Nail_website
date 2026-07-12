#!/usr/bin/env bash
# Backup file SQLite an toàn ngay cả khi app đang chạy (dùng online .backup API
# của sqlite3, không copy file thô). Chạy hằng ngày qua cron.
set -euo pipefail

DB="/var/www/nail-app/app/database/database.db"
DEST="/var/backups/nail-app"
KEEP=14   # giữ 14 bản gần nhất

mkdir -p "$DEST"
STAMP="$(date +%Y%m%d-%H%M%S)"
sqlite3 "$DB" ".backup '$DEST/database-$STAMP.db'"

# xoá bản cũ hơn KEEP
ls -1t "$DEST"/database-*.db 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "Backup done: $DEST/database-$STAMP.db"
