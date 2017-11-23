#!/usr/bin/env python

from ecdsa import SigningKey, VerifyingKey

sk = SigningKey.generate() # uses NIST192p
vk = sk.get_verifying_key()
vk_hex = bytearray(vk.to_string()).hex().upper()
sk_hex = bytearray(sk.to_string()).hex().upper()

print("Signature Key: %s" % sk_hex)
print("Verify Key: %s" % vk_hex)
