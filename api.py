import hashlib
import json
import sys
from time import time

import requests
from flask import Flask, jsonify, request

import black
import channel

app = Flask(__name__)

@app.route('/join', methods=['POST'])
def join_channel():
    values = request.get_json()

    required = ['remote_node', 'local_node', 'chan']
    if not all(k in values for k in required):
        return "Missing required fields", 400

    remote_node = values['remote_node']
    local_node = values['local_node']
    chan = values['chan']
    data = {'nodes': [local_node] }
    response = requests.post(
        f'{remote_node}/{chan}/nodes/register',
        data = json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    body = response.json()
    chan_info = body['channel']

    # manually cloning the channel? gross
    chan = channel.Channel(chan_info['name'])
    chan.created_at = chan_info['created_at']
    chan.ref = chan_info['ref']
    # TODO: clone all registered nodes on remote machine
    chan.chain.register_node(remote_node)

    black.CHANNELS[chan.ref] = chan
    # TODO: return a better response than just "OK"
    return jsonify({'message': "OK"})


@app.route('/<chan>/nodes/register', methods=['POST'])
def register_nodes(chan):
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
        black.CHANNELS[chan].chain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(black.CHANNELS[chan].chain.nodes),
        'channel': {
            'name': black.CHANNELS[chan].name,
            'ref': black.CHANNELS[chan].ref,
            'created_at': black.CHANNELS[chan].created_at,
        }
    }
    return jsonify(response), 201


@app.route('/<chan>/mine', methods=['GET'])
def mine(chan):
    # We run the proof of work algorithm to get the next proof...
    last_block = black.CHANNELS[chan].chain.last_block
    last_proof = last_block['proof']
    proof = black.CHANNELS[chan].chain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    black.CHANNELS[chan].chain.new_transaction(
        sender=black.node_identifier,
        msg="mined.",
    )

    # Forge the new Block by adding it to the chain
    block = black.CHANNELS[chan].chain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'messages': block['messages'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/<chan>/nodes/resolve', methods=['GET'])
def consensus(chan):
    replaced = black.CHANNELS[chan].chain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': black.CHANNELS[chan].chain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': black.CHANNELS[chan].chain.chain
        }

    return jsonify(response), 200


@app.route('/<chan>/transactions/new', methods=['POST'])
def new_transaction(chan):
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'message']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = black.CHANNELS[chan].chain.new_transaction(values['sender'], values['message'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/<chan>/chain', methods=['GET'])
def full_chain(chan):
    chain = black.CHANNELS[chan].chain.chain
    response = {
        'chain': chain,
        'length': len(chain),
    }
    return jsonify(response), 200


@app.route('/channels/new', methods=['POST'])
def new_channel():
    values = request.get_json()

    required = ['name']
    if not all(k in values for k in required):
        return 'Missing values', 400

    chan = channel.Channel(values['name'])
    black.CHANNELS[chan.ref] = chan

    response = {'channel': chan.ref}
    return jsonify(response), 200


@app.route('/channels')
def list_channels():
    return jsonify(black.CHANNELS), 200


@app.route('/channels/<chan>')
def list_channel(chan):
    return jsonify(black.CHANNELS[chan]), 200


