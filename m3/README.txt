General notes:
    - Do not use "python manage.py crawl" too often as it interacts with external pages
      and there's always risk of exceeding quotas on access (if any exist)
    - Do not work on master branch.


How to install:

1. Enter directory where you'll keep the project.
2. Switch on virtualenv on which you'll work (e.g. workon m3)
3. git clone git@github.com:Buzdygan/flats.git .
4. pip install -r requirements.txt
5. create file m3/m3/settings.py  (same dir as settings_defaults) with contents:
    SECRET_KEY = '<SECRET KEY YOU WILL GET FROM OWNER>'
    from m3.settings_defaults import *
6. Install sqlite3 (if not installed)
7. cd m3
8. sqlite3 db.sqlite3 (Creates database file, exit by ctr-d)
9. python manage.py migrate
10. python manage.py crawl --page-start 1 --page-end 10 (Fetches data, ignore errors)
11. python manage.py match_posts (Ignore errors, necessary step after fetching new data)
12. python manage.py runserver
13. Enter link displayed (http://127.0.0.1:8000/)
14. (optional). In top directory, run `cp git_exclude .git/info/exclude` to stop
    displaying unnecessary files when using git status.


Development cycle:

To start making change on a separate branch (Try to keep changes small, finish one and get it
to be merged to master, before starting another on a new branch.)
1. git checkout master
2. git pull
3. git checkout -b <YOUR_BRANCH_NAME>
4. Do work, commit.
5. Remember to run regularly: "git pull origin master" on your branch, to merge latest changes
   from master. If you run into conflicts, you can try to solve them, or contact Owner.
6. To push your branch to github, run "git push -u origin <YOUR_BRANCH_NAME>"
7. Do not ever merge your branch to master (neither locally nor on github). It will be done once
   changes on the branch are approved.


Useful commands:
    - python manage.py match_posts --reset-matching (To clear matching data. Don't run without
      need. Afterwards, you'll need to run "python manage.py match_posts" to restore it.)
