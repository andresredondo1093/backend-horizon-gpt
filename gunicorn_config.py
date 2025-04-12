# Gunicorn configuration file
bind = "0.0.0.0:10000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
