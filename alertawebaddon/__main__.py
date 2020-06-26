from threading import Thread

from alertawebaddon import app, args
from alertawebaddon.views import auth

app.register_blueprint(auth)


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()


if __name__ == '__main__':
    main()
