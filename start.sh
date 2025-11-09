#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP (สำคัญมากสำหรับ Flask ใน Production)
export FLASK_APP=app.py

# 2. รัน Gunicorn เป็น Python Module และกำหนด Host/Port ตามที่ Render กำหนด
exec python -m gunicorn app:app -b 0.0.0.0:$PORT
