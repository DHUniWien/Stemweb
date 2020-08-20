#!/bin/bash

# Wait for MySQL to come up
sleep 5 

# Do the necessary DB migrations
echo "Doing database migrations"
cd /home/stemweb
python manage.py makemigrations
python manage.py migrate --run-syncdb
python manage.py loaddata Stemweb/algorithms/init_algorithms.json
python manage.py loaddata Stemweb/files/files.json
python manage.py loaddata Stemweb/home/fixtures/bootstrap.json

# Start celery worker
echo "Starting Celery worker"
celery worker -A Stemweb &

# Start Django server
python manage.py runserver 0.0.0.0:8000