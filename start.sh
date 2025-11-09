#!/usr/bin/env bash
# รัน Gunicorn โดยใช้ Python Module เพื่อให้หา Gunicorn ที่ติดตั้งใน venv เจอ
exec python -m gunicorn app:app