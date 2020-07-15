from threading import Thread

from flask_bootstrap import Bootstrap

from alertawebaddon import app, args
from alertawebaddon.views import github_bp

app.register_blueprint(github_bp, url_prefix="/webaddon")

Bootstrap(app)


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
