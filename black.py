import hashlib
import json
import sys
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request

def p(msg):
    print(msg, file=sys.stderr)

class ChannelChain:
    def __init__(self):
        self.current_msgs = []
        self.chain = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'messages': self.current_msgs,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_msgs = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, msg):
        self.current_msgs.append({
            'sender': sender,
            'msg': msg,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:1] == "0"

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block):
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the general channel
chan_general = ChannelChain()

# Instantiate the Node
app = Flask(__name__)
p("Node started.")

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    if values is None:
        return "Error: Please supply a valid list of nodes", 400

    required = ['nodes']
    if not all(k in values for k in required):
        return "Error: Please supply a valid list of nodes", 400

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        chan_general.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(chan_general.nodes),
    }
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = chan_general.last_block
    last_proof = last_block['proof']
    proof = chan_general.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    chan_general.new_transaction(
        sender=node_identifier,
        msg="mined.",
    )

    # Forge the new Block by adding it to the chain
    block = chan_general.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'messages': block['messages'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = chan_general.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': chan_general.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': chan_general.chain
        }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'message']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = chan_general.new_transaction(values['sender'], values['message'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': chan_general.chain,
        'length': len(chan_general.chain),
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port, debug=True)
