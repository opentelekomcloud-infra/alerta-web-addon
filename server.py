from argparse import ArgumentParser
from threading import Thread

from flask import Flask, jsonify
from flask_cors import CORS

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app)

@app.route('/', methods=['GET'])
def root():
    return jsonify('200')


AGP = ArgumentParser(prog='Web server for alerta', description='')
AGP.add_argument('--port', help='port to be listened', default=23456, type=int)
AGP.add_argument('--debug', help='debug mode', default=False, type=bool)
args, _ = AGP.parse_known_args()


def main():
    Thread(target=app.run, kwargs={'port': args.port, 'debug': args.debug}).start()

if __name__ == '__main__':
    main()
