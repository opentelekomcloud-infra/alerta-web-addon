from threading import Thread

from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from alertawebaddon import app, args
from alertawebaddon.views import github_bp

app.register_blueprint(github_bp, url_prefix="/login")
from flask_bootstrap import Bootstrap

Bootstrap(app)

def main():
    application = DispatcherMiddleware(app, {
        app.config['APPLICATION_ROOT']: app
    })
    run_simple('localhost', args.port, application, use_reloader=True)
    # Thread(target=application.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
