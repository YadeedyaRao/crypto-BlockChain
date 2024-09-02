from hashlib import sha256
from Crypto.Hash import RIPEMD160
from BLCKCHN.Backend.core.EllepticCurve.EllepticCurve import Sha256Point, BASE58_ALPHABET
import math
def hash256(s):
    return sha256(sha256(s).digest()).digest()

def hash160(s):
    return RIPEMD160.new(sha256(s).digest()).digest()

def bytes_needed(n):
    if n == 0:
        return 1
    else:
        return int(math.log(n, 256))+1 # no.of bytes

def int_to_little_endian(n, length):
    """takes a integer and returns in little endian format byte sequence of length length"""
    return n.to_bytes(length, 'little')

def little_endian_to_int(b):
    """return a integer sequence for a little endian fromatted seq"""
    return int.from_bytes(b, 'little')

def decode_base58(address):
    num = 0
    #since index of 1 is 0 in base58 encoding the prefix 1's we added while making address results in zeroes
    for alpha in address:
        num *= 58
        num += BASE58_ALPHABET.index(alpha)

    combined = num.to_bytes(25, byteorder='big')
    checksum = combined[-4:]

    if hash256(combined[:-4])[:4] != checksum:
        raise ValueError(f'bad Address {checksum} {hash256(combined[:-4][:4])}')
    
    return combined[1:-4] # return only the hash160 of the public_key

def hash_to_parent_lvl(hashes):
    if len(hashes) % 2 : 
        hashes.append(hashes[-1])
    parent_lvl = []
    for i in range(0, len(hashes), 2):
        #we already have hashes in byte format
        parent_lvl.append(hash256(hashes[i]+hashes[i+1])) # hash the concatination two adjacent hashes
    return parent_lvl
        

def merkle_root(hashes):
    current_lvl = hashes

    while len(current_lvl) > 1:
        current_lvl = hash_to_parent_lvl(current_lvl)

    return current_lvl[0]

def encode_varint(i):
    """encodes an integer as varint"""
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000: # less than 16^4 = 2 ^ 16 => 15 bits = 2 bytes
        return b'\xfd' + int_to_little_endian(i, 2)
    elif i < 0x100000000: # requires 4 bytes
        return b'\xfe' + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000: # requires 8 bytes
        return b'\xff' + int_to_little_endian(i, 8)
    else:
        return ValueError("integer too large: {}".format(i))
    
def target_to_bits(target):
    raw_bytes = target.to_bytes(32, 'big')
    raw_bytes = raw_bytes.lstrip(b'\x00') # <1>
    if raw_bytes[0] > 0x7f : 
        exponent = len(raw_bytes) + 1
        coefficient = b'\x00' + raw_bytes[:2]
    else:
        exponent = len(raw_bytes)
        coefficient = raw_bytes[:3]
    new_bytes = coefficient[::-1] + bytes([exponent])

    return new_bytes