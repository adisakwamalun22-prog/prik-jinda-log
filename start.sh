#!/usr/bin/env bash

export FLASK_APP=app.py
exec gunicorn app:app -b 0.0.0.0:$PORT