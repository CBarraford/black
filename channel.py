import hashlib
import sys
from time import time
from urllib.parse import urlparse
import json

import requests
from ecdsa import VerifyingKey

import authority


class Channel:
    def __init__(self, name):
        self.name = name
        self.created_at = time()
        self.ref = hashlib.sha256(f"{name} {self.created_at}".encode('utf-8')).hexdigest()
        self.chain = ChannelChain()


class ChannelChain:
    def __init__(self):
        self.current_msgs = []
        self.chain = []
        self.nodes = set()
        self.authority = authority.Authority()

        # Create the genesis block
        self.new_block({'msg':'init channel'}, previous_hash=1)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, msg, previous_hash=None):
        self.chain.append({
            'index': len(self.chain) + 1,
            'created_at': time(),
            'message': msg,
            'hash': self.hash(msg),
            'previous_hash': previous_hash or self.last_block['hash'],
            # auth_sig references the latest signature of the most recent auth blockchain block
            'authority_signature': previous_hash or self.authority.last_signature,
        })

    def new_transaction(self, pubKey, signature, msg):
        if not self.verify_message(msg, pubKey, signature):
            return 0

        if self.authority.priviledged(pubKey):
            self.new_block({
                'public_key': pubKey,
                'signature': signature,
                'msg': msg,
            })
            return self.last_block['index'] + 1

        return 0

    def verify_message(self, message, pubKey, signature):
        vk = VerifyingKey.from_string(bytearray.fromhex(pubKey))
        return vk.verify(bytearray.fromhex(signature), message.encode("utf-8"))

    def validate_chain(self, chain):
        # TODO we should validate also that the chain given is the same chain as we already have.
        # Otherwise a foreign node can create an entire new chain from scratch and replace all
        # messages with new messages (as long as the fake chain is longer than the current).
        # But this may no longer be an issue with signed messages or changing the consensus to
        # something like Proof of Authority
        last_block = chain[0]
        current_index = 1
        authority_index = 0

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != last_block['hash']:
                return False

            # verify message signature
            msg = block['message']
            if not self.verify_message(msg['msg'], msg['public_key'], msg['signature']):
                return False

            # verify authority
            # ensure we don't reference an older authority signature than we've seen before.
            auth_index = self.authority.signature_index(block['authority_signature'])
            if auth_index < authority_index:
                return False
            # ensure the author has authority at given authority chain index
            if not self.authority.priviledged(block['message']['public_key'], index=auth_index):
                return False

            # record new values for next run
            authority_index = auth_index
            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self, chan):
        # TODO: dont download the entire chain from another node just to resolve conflicts. That is
        # not scaleable. Instead provide the length of the chain we have and send us the diff.
        neighbours = self.nodes
        new_chain = None
        new_authority = None

        # We're only looking for chains longer than ours
        max_chain_length = len(self.chain)
        max_authority_length = len(self.authority.votes)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/{chan}/chain')

            if response.status_code == 200:
                length = response.json()['messages']['length']
                chain = response.json()['messages']['chain']

                # Check if the length is longer and the chain is valid
                if length > max_chain_length and self.validate_chain(chain):
                    max_chain_length = length
                    new_chain = chain

                length = response.json()['authority']['length']
                chain = response.json()['authority']['chain']

                # Check if the length is longer and the chain is valid
                chain = [authority.Vote(e['raw_vote'], e['voter_address'], e['signature']) for e in chain]
                if length > max_authority_length and self.authority.validate_chain(chain):
                    max_authority_length = length
                    new_authority = chain

        replaced = False
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            replaced = True
        if new_authority:
            self.authority.votes = new_authority
            replaced = True

        return replaced

    @property
    def last_block(self):
        # Returns the last Block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block):
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
