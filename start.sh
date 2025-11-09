#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP
export FLASK_APP=app.py

# 2. รัน Gunicorn โดยชี้ไปที่ Application Factory
exec gunicorn "app:create_app()" -b 0.0.0.0:$PORT