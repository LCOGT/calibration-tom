FROM python:3.7
LABEL maintainer="llindstrom@lco.global"

# the exposed port must match the deployment.yaml containerPort value
EXPOSE 80
ENTRYPOINT [ "/usr/local/bin/gunicorn", "calibration_tom.wsgi", "-b", "0.0.0.0:80", "--access-logfile", "-", "--error-logfile", "-", "-k", "gevent", "--timeout", "300", "--workers", "2"]

WORKDIR /calibration-tom

COPY requirements.txt /calibration-tom
RUN pip install --no-cache-dir -r /calibration-tom/requirements.txt

COPY . /calibration-tom

RUN python manage.py collectstatic --noinput
