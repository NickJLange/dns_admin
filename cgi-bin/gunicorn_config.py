# [label gunicorn_config.py]
bind = "0.0.0.0:19000"
workers = 2
timeout = 240
read_timeout = 240
accesslog = "-"
