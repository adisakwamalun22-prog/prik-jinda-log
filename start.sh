#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP
export FLASK_APP=app.py

# 2. 🟢 รัน Gunicorn (app.py จะสร้างตารางเองโดยใช้ @app.before_request)
exec gunicorn app:app -b 0.0.0.0:$PORT