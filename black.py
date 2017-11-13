import sys
from uuid import uuid4

import channel
import api

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# place to store all channels (blockchains)
# TODO: all uppercase usually mean immutable, but alas, this var is mutable :(
CHANNELS = {}


def pp(msg):
    print(msg, file=sys.stderr)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app = api.app

    app.run(host='0.0.0.0', port=port, debug=True)
