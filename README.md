Run in prod with gunicorn -w 4 'proxy_auth.app:create_app("config.yaml")'
To add a user run poetry run proxy_auth config.yaml --add_user
