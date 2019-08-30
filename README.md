# calibration-tom

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
