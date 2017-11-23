import hashlib
import json
import sys
from time import time

import requests
from flask import Flask, jsonify, request

import black
import channel
import authority

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


@app.route('/<chan>/nodes/resolve', methods=['GET'])
def consensus(chan):
    replaced = black.CHANNELS[chan].chain.resolve_conflicts(chan)
    authority = black.CHANNELS[chan].chain.authority.votes
    chain = black.CHANNELS[chan].chain.chain

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': chain,
            'new_authority': [e.__dict__ for e in authority],
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': chain,
            'authority': [e.__dict__ for e in authority],
        }

    return jsonify(response), 200


@app.route('/<chan>/transactions/new', methods=['POST'])
def new_transaction(chan):
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['message', 'pub_key', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = black.CHANNELS[chan].chain.new_transaction(
        values['pub_key'], values['signature'], values['message']
    )

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/<chan>/votes/new', methods=['POST'])
def new_vote(chan):
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['vote', 'pub_key', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new vote
    vote = authority.Vote(values['vote'], values['pub_key'], values['signature'])
    if black.CHANNELS[chan].chain.authority.vote(vote):
        response = {'message': f'Vote added'}
        return jsonify(response), 201
    else:
        return jsonify({'message': 'No authority or bad signature or bad last sig reference'}, 401)



@app.route('/<chan>/chain', methods=['GET'])
def full_chain(chan):
    chain = black.CHANNELS[chan].chain.chain
    authority = black.CHANNELS[chan].chain.authority.votes
    response = {
        'messages': {
            'chain': chain,
            'length': len(chain),
        },
        'authority': {
            'chain': [e.__dict__ for e in authority],
            'length': len(authority),
        },
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


