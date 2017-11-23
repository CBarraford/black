#!/usr/bin/env python

import sys

from ecdsa import SigningKey, VerifyingKey

if len(sys.argv) != 3:
    print("Missing inputs. Pass sig key and message")
    sys.exit(1)

sk = sys.argv[1]
message = sys.argv[2]

sk = SigningKey.from_string(bytearray.fromhex(sk))
vk = sk.get_verifying_key()
signature = sk.sign(message.encode("utf-8"))

print("Message: %s" % message)
print("Signature: %s" % bytearray(signature).hex().upper())
