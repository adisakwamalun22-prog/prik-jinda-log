#!/usr/bin/env bash

# กำหนดตัวแปรสภาพแวดล้อม
export FLASK_APP=app.py

# รัน Gunicorn พร้อมกำหนด Host และ Port
exec gunicorn app:app -b 0.0.0.0:$PORT