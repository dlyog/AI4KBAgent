#!/bin/bash

# Run your application server with SSL
# gunicorn --certfile=/etc/ssl/certs/certificate.crt --keyfile=/etc/ssl/private/private.key --log-level debug -b 0.0.0.0:5011 app:app

python app.py
