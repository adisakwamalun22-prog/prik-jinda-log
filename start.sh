#!/usr/bin/env bash

# Run the Gunicorn application using the Python from the created venv
exec .venv/bin/gunicorn app:app