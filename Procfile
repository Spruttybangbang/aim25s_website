web: gunicorn ai_companies_admin.wsgi --log-file -
release: python manage.py migrate && python manage.py collectstatic --noinput
