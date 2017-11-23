# proof of authority
from ecdsa import VerifyingKey
import sys
import json


class Authority:
    def __init__(self):
        self.votes = []

    def vote(self, vote):
        # this is our first vote, no need to verify it
        if len(self.votes) == 0:
            self.votes.append(vote)
            return True

        # make sure voter has rights to vote
        if not self.priviledged(vote.voter_address):
            return False

        # validate message. Don't validate the first vote.
        if not vote.verify_message():
            return False

        # make sure signatures match before appending to the blockchain
        if self.last_vote.signature == vote.last_signature:
            self.votes.append(vote)
            return True

        return False

    def signature_index(self, sig):
        '''
        Find the index on the auth chain for a specific vote signature
        '''
        for i, vote in self.votes():
            if sig == vote.signature:
                return i
        return 0

    def priviledged(self, address, votes=None, index=None):
        '''
        Check that a given address has authority on the chain
        If index number is given, it will check if the address has authority at the time of that
        index number.
        '''

        if votes is None:
            votes = self.votes


        # if no votes have been cast, anyone can vote
        if len(votes) == 0:
            return True

        # index of zero is not valid (as it would always return true)
        if index == 0:
            return False

        poll = {}

        # count the votes
        last_sig = ""
        for vote in votes[:index]:
            # check that the last sign matches the last_sig mentioned in this vote. If they don't
            # match, omit the vote
            # If we're on the first vote, no need to check this
            if last_sig != "" and last_sig == vote.last_signature:
                continue
            last_sig = vote.last_signature

            if not vote.recipient_address in poll:
                poll[vote.recipient_address] = {}

            poll[vote.recipient_address][vote.voter_address] = vote.priviledged

        # The tally counts the up/down votes. If an address has equal up/down votes or higher, that
        # address is privileged (to vote)
        tally = 0
        for voter_address, priviledged in poll[vote.recipient_address].items():
            # NOTE: we check specifically true/false in case privileged is NOT a bool
            if priviledged is True:
                tally += 1
            elif priviledged is False:
                tally -= 1

        return tally > 0

    def validate_chain(self, chain):
        if len(chain) == 0:
            return True

        last_vote = chain[0]
        current_index = 1

        while current_index < len(chain):
            vote = chain[current_index]

            # Check that the hash of the block is correct
            if vote.last_signature != last_vote.signature:
                return False

            # validate the message
            if not self.verify_message(vote.raw_vote, vote.voter_address, vote.signature):
                return False

            # verify voter has rights to vote
            if not self.priviledged(vote.voter_address, chain, current_index):
                return False

            last_vote = vote
            current_index += 1

        return True

    def verify_message(self, message, pubKey, signature):
        vk = VerifyingKey.from_string(bytearray.fromhex(pubKey))
        return vk.verify(bytearray.fromhex(signature), message.encode("utf-8"))

    @property
    def last_vote(self):
        # returns the last vote
        return self.votes[-1]

    @property
    def last_signature(self):
        vote = self.last_vote
        return vote.signature


def str2bool(v):
    return v.lower() in ('yes', 'true', 't', '1')


class Vote:
    def __init__(self, raw_vote, voter_address, signature):
        self.signature = signature
        self.raw_vote = raw_vote
        self.voter_address = voter_address

        parts = self.raw_vote.split()
        if not len(parts) == 3:
            # invalid vote string (not enough parts)
            raise ValueError('Invalid vote message format.')

        self.priviledged = str2bool(parts[0])
        self.recipient_address = parts[1]
        self.last_signature = parts[2]

    def verify_message(self):
        vk = VerifyingKey.from_string(bytearray.fromhex(self.voter_address))
        return vk.verify(bytearray.fromhex(self.signature), self.raw_vote.encode("utf-8"))

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
