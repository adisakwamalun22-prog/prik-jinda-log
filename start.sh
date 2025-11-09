#!/usr/bin/env bash

# 1. ตั้งค่า FLASK_APP (สำคัญมาก)
export FLASK_APP=app.py

# 2. รัน Gunicorn Binary โดยตรงจาก Virtual Environment (นี่คือการแก้ไขปัญหา PATH ที่ดีที่สุด)
exec .venv/bin/gunicorn app:app