#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP (เหมือนเดิม)
export FLASK_APP=app.py

# 2. 🟢 สร้างตารางในฐานข้อมูล (ด้วยไวยากรณ์ที่ถูกต้อง)
# เราจะรัน 'python -c' และ import app context เข้ามาเอง
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 3. รัน Gunicorn (เหมือนเดิม)
exec gunicorn app:app -b 0.0.0.0:$PORT