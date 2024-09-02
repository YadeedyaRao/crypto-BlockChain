import sys
sys.path.append('E:/blockchain')
from BLCKCHN.Backend.util.util import hash160
from BLCKCHN.Backend.util.util import hash256
from BLCKCHN.Backend.core.EllepticCurve.EllepticCurve import Sha256Point, BASE58_ALPHABET
from BLCKCHN.Backend.core.database.database import AccountDB
import secrets

# y^2 = x^3 + 0*x+ 7

class Account:
    def create_keys(self):
        Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
        Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

        G = Sha256Point(Gx, Gy)

        private_key = secrets.randbits(256)

        #uncompressed public key
        uc_public_key = private_key * G
        xPoint = uc_public_key.x
        yPoint = uc_public_key.y

        #we are using yPoint

        if yPoint.num % 2 == 0:
            comp_key = b'\x02' + xPoint.num.to_bytes(32, 'big') # big endian stores bytes from left -> right
        else:
            comp_key = b'\x03' + xPoint.num.to_bytes(32, 'big')

        hsh160 = hash160(comp_key) # 20 bytes
        """Prefix for mainnet"""

        main_prefix = b'\x00'
        newAddress =  main_prefix + hsh160 # 1 + 20 = 21 bytes

        """Checksum"""
        checksum = hash256(newAddress)[:4] # first four bytes of hash256

        newAddress = newAddress + checksum # 21+4 = 25 bytes

        count = 0 # count leading zeroes - inherently main_prefix adds a zero byte

        for c in newAddress:
            if c == 0: # checks if any leading zero bytes
                count += 1
            else:
                break
        
        num = int.from_bytes(newAddress, 'big')
        prefix = '1' * count
        result = ''

        #base 58 encoding
        while num  > 0:
            num, mod = divmod(num, 58)
            result = BASE58_ALPHABET[mod] + result

        public_address = prefix + result
        self.private_key = private_key
        self.public_address = public_address
        print(f"private key is {private_key} \n public address {public_address}")


if __name__ == '__main__':
    acct = Account()
    acct.create_keys()
    AccountDB().write([acct.__dict__])