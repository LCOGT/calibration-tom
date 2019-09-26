# calibration-tom

## Local development
For the moment, here's how to get started with local development:
```
 git clone git@github.com:LCOGT/calibration-tom.git
 cd calibration-tom
 /opt/lcogt-python36/bin/python3.6 -m venv tom_env
 source tom_env/bin/activate
 pip install --upgrade pip
 pip install -r requirements.txt 
 ./manage.py migrate
 ./manage.py runservser &
 ```
 You may also want to
 ```
 ./manage.py createsuperuser
```
## Building an image and running via the Dockerfile
```
cd /path/to/dir/containing/Dockerfile
docker build -t calibration-tom .
docker run --rm  -p 8910:80 calibration-tom:latest  # replace 8910 with your favorite PORT number
# point your browser to localhost:8910/
```
### To run commands in the container:
```
docker ps # find the name of the container (eg. vigorous_newton)
docker exec vigorous_newton /lco/calibration-tom/manage.py  # run a manage.py command

# alternatively, "bash" into the container:
docker exec  -it vigorous_newton /bin/bash
```