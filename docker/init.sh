#!/bin/bash

cd /lco/calibration-tom
# python manage.py collectstatic --noinput
exec gunicorn -k gevent -b 0.0.0.0:80 -w 4 --access-logfile - --error-logfile - calibration_tom.wsgi:application
