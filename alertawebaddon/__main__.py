from threading import Thread

from alertawebaddon import app, args
from alertawebaddon.views import github_bp

class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)

app.register_blueprint(github_bp, url_prefix="/webaddon/login")
from flask_bootstrap import Bootstrap

Bootstrap(app)

def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
