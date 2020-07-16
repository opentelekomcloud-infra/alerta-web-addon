from threading import Thread

from flask_bootstrap import Bootstrap
from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from alertawebaddon import app, args
from alertawebaddon.views import github_bp

app.register_blueprint(github_bp, url_prefix="/login")

Bootstrap(app)
application = DispatcherMiddleware(
    None, {
        '/webaddon': app
    }
)

def main():
    run_simple('localhost', args.port, application, use_reloader=True)
    # Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
