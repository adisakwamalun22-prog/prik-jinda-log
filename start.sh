#!/usr/bin/env bash

# 1. Activate Virtual Environment ก่อน
source .venv/bin/activate

# 2. ตั้งค่า FLASK_APP (ถ้า Gunicorn ต้องการ)
export FLASK_APP=app.py

# 3. รัน Gunicorn (ตอนนี้ Gunicorn จะอยู่ใน PATH ที่ถูก Activate แล้ว)
gunicorn app:app