#!/usr/bin/env bash
# รัน Python Module Gunicorn โดยใช้ Python Binary ใน Environment
exec python -m gunicorn app:app