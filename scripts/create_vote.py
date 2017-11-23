#!/usr/bin/env python

import sys

from ecdsa import SigningKey, VerifyingKey

if len(sys.argv) < 4:
    print("Missing inputs. Pass signing key, vote (1|2), and last signature")
    sys.exit(1)

sk = sys.argv[1]
vote = sys.argv[2]
last_sig = sys.argv[3]
recipient = sys.argv[4] or None

sk = SigningKey.from_string(bytearray.fromhex(sk))
vk = sk.get_verifying_key()
if not recipient:
    recipient = bytearray(vk.to_string()).hex().upper()

message = f'{vote} {recipient} {last_sig}'
signature = sk.sign(message.encode("utf-8"))

print("Message: %s" % message)
print("Signature: %s" % bytearray(signature).hex().upper())
