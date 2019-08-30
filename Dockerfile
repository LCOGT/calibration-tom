FROM python:3.7

EXPOSE 80
ENTRYPOINT [ "/init.sh" ]

COPY requirements.txt /lco/calibration-tom/
RUN apt-get -y update \
        && apt-get -y install gfortran \
        && apt-get -y clean \ 
        && pip --no-cache-dir install numpy \
        && pip --no-cache-dir install -r /lco/calibration-tom/requirements.txt

COPY docker/ /

RUN ls -l /init.sh

COPY . /lco/calibration-tom/
