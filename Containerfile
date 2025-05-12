FROM docker.io/library/python:3.12.7-slim-bullseye

RUN python3 -m venv /opt/venv

# Install dependencies:
COPY etc/webserver_requirements.txt requirements.txt
RUN . /opt/venv/bin/activate && pip install -r requirements.txt

WORKDIR /opt/webserver/cgi-bin/
COPY cgi-bin/controller.py /opt/webserver/cgi-bin/
COPY cgi-bin/gunicorn_config.py /opt/webserver/cgi-bin/
COPY cgi-bin/wsgi.py /opt/webserver/cgi-bin/

WORKDIR /opt/webserver/etc/
COPY etc/config.ini /opt/webserver/etc/

WORKDIR /opt/webserver/cgi-bin/
COPY lib/. /opt/webserver/lib/

#PYTHONPATH=../../dns_admin/lib/
WORKDIR /opt/webserver/

### FIXME: workers 1 to avoid state issues on ubiquity - need another URL to get status, that's cheap...
### FIXME: move from --reload to --preload (to fix a weird issue of locking up)
### https://github.com/benoitc/gunicorn/issues/1923
CMD . /opt/venv/bin/activate && exec gunicorn -k uvicorn.workers.UvicornWorker -c cgi-bin/gunicorn_config.py  --timeout 10 --preload  --chdir cgi-bin wsgi:app --workers 7
#CMD . /opt/venv/bin/activate && exec fastapi run --host 0.0.0.0 --port 19000 --root-path /opt/webserver/cgi-bin cgi-bin/wsgi.py --workers 2
