FROM docker.io/library/python:3.9.9-slim-bullseye

RUN python3 -m venv /opt/venv

# Install dependencies:
COPY etc/webserver_requirements.txt requirements.txt
RUN . /opt/venv/bin/activate && pip install -r requirements.txt

WORKDIR /opt/webserver/cgi-bin/
COPY cgi-bin/dns_server.py /opt/webserver/cgi-bin/
COPY cgi-bin/gunicorn_config.py /opt/webserver/cgi-bin/
COPY cgi-bin/wsgi.py /opt/webserver/cgi-bin/

WORKDIR /opt/webserver/etc/
COPY etc/config.ini /opt/webserver/etc/

#PYTHONPATH=../../dns_admin/lib/ 
WORKDIR /opt/webserver/
CMD . /opt/venv/bin/activate && exec gunicorn -c cgi-bin/gunicorn_config.py --reload  --chdir cgi-bin wsgi:app
