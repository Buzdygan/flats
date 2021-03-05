#!/bin/bash  

python manage.py crawl
python manage.py crawl --otodom
python manage.py extract_info --locations
python manage.py extract_info --geodata
python manage.py extract_info --parse-geodata
python manage.py extract_info --attach-areas
python manage.py extract_info
python manage.py match_posts
