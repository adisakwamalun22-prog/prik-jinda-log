#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP
export FLASK_APP=app.py

# 2. รัน Gunicorn โดยใช้ Python Interpreter ที่ Render สร้างไว้โดยตรง
# $VIRTUAL_ENV คือตัวแปรที่ชี้ไปที่โฟลเดอร์ venv
exec $VIRTUAL_ENV/bin/gunicorn app:app