#!/usr/bin/env bash
# 1. ตั้งค่า FLASK_APP ก่อน
export FLASK_APP=app.py 
# 2. รัน Gunicorn โดยใช้ Python Module
exec python -m gunicorn app:app