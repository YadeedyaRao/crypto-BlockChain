from BLCKCHN.Backend.core.Script import Script
from BLCKCHN.Backend.util.util import int_to_little_endian, bytes_needed, decode_base58, little_endian_to_int, encode_varint, hash256

ZERO_HASH = b'\x00' * 32 # 32bytes = 32*8 = 256 bits
REWARD = 50
PRIVATE_KEY = '31016520329153619396624450785665981848385738899339014334548670158841195721081'
MINER_ADDRESS = 'NTjLVWgQYgHT87NeYjSJ1a76EXmftWBgJ'
VERSION = 1
SIGNHASH_ALL = 1

class CoinbaseTxn:
    def __init__(self, BlockHeight):
        self.BlockHeightInLittleEndian = int_to_little_endian(BlockHeight, bytes_needed(BlockHeight))

    def CoinbaseTransaction(self):
        prev_tx = ZERO_HASH
        prev_index = 0xffffffff

        txns_in = []
        txns_in.append(TxnIn(prev_tx, prev_index))
        #remember coinbase transaction has only one txn_in and one txn out
        txns_in[0].script_sig.cmds.append(self.BlockHeightInLittleEndian)

        txns_out = []
        target_amount = REWARD * 100000000
        target_h160 = decode_base58(MINER_ADDRESS)
        target_script = Script.p2pkh_script(target_h160)
        txns_out.append(TxnOut(amount = target_amount, script_publickey = target_script))

        coinbase_txn = Txn(VERSION, txns_in, txns_out, 0)
        coinbase_txn.TxId = coinbase_txn.id()
        return coinbase_txn


class Txn:
    def __init__(self, version, txs_in, txs_out, locktime):
        self.version = version
        self.txs_in = txs_in
        self.txs_out = txs_out
        self.locktime = locktime # transaction wont be proccessed until locktime is elapsed(measured in blocks in block chain -- k-depth security?)

    def id(self):
        """Human redable tx id"""
        return self.hash().hex()
    def hash(self):
        """Binary hash of serialization"""
        #its how done in official bitcoin documentation
        return hash256(self.serialize())[::-1]
    def serialize(self): # convert into binary
        result = int_to_little_endian(self.version, 4)
        result += encode_varint(len(self.txs_in))

        for tx in self.txs_in:
            result += tx.serialize()
        

        result += encode_varint(len(self.txs_out))
        for tx_out in self.txs_out:
            result += tx_out.serialize()

        result += int_to_little_endian(self.locktime, 4)

        return result
    

    def sign_hash(self, input_index, script_pubkey):
        # convert whole txn into bytes to hash it
        s = int_to_little_endian(self.version , 4)
        s += encode_varint(len(self.txs_in))

        for i, txn_in in enumerate(self.txs_in):
            if(i == input_index):
                s += TxnIn(txn_in.prev_tx, txn_in.prev_index, script_pubkey).serialize()
            else:
                s += TxnIn(txn_in.prev_tx, txn_in.prev_index).serialize()
        
        s += encode_varint(len(self.txs_out))

        for txn_out in self.txs_out:
            s += txn_out.serialize()

        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGNHASH_ALL, 4)
        h256 = hash256(s)

        return int.from_bytes(h256, 'big')



    def sign_input(self, input_index, private_key, script_pubkey):
        z = self.sign_hash(input_index, script_pubkey)
        der = private_key.sign(z).der()
        sig = der + SIGNHASH_ALL.to_bytes(1, 'big') # adds a hash type at the end
        sec = private_key.point.sec()
        self.txs_in[input_index].script_sig = Script([sig, sec])

    def verify_input(self, input_index, script_pubkey):
        txn_in = self.txs_in[input_index]
        z = self.sign_hash(input_index, script_pubkey)
        combined = txn_in.script_sig + script_pubkey # normal addtion is overrided
        return combined.evaluate(z)

    def is_coinbase(self):
        """
        #Check that there is exactly 1 input
        # grab the first input and check if the prev_tx is b'\x00' * 32
        #Check that the first inoput prev_txn is 0xffffffff
        """

        if len(self.txs_in) != 1:
            return False
        
        first_input = self.txs_in[0]

        if first_input.prev_tx != ZERO_HASH:
            return False
        
        if first_input.prev_index != 0xffffffff:
            return False
        return True


    def to_dict(self):
        """returns dict formatted object
        # convert prev_tx Hash in hex from bytes
        # convert BlockHeight in hex which is stored in script signature
        """
        for tx_index, tx_inp in enumerate(self.txs_in):
            if self.is_coinbase():#script sign for that is blockHeight in little endian
                tx_inp.script_sig.cmds[0] = little_endian_to_int(tx_inp.script_sig.cmds[0])
            tx_inp.prev_tx = tx_inp.prev_tx.hex()

            for index, cmd in enumerate(tx_inp.script_sig.cmds):
                if isinstance(cmd, bytes):
                    tx_inp.script_sig.cmds[index] = cmd.hex()
            
            tx_inp.script_sig = tx_inp.script_sig.__dict__
            self.txs_in[tx_index] = tx_inp.__dict__


        for tx_index, tx_out in enumerate(self.txs_out):
            #script publickey has publickey hash at 2 index, convert it to hex
            tx_out.script_publickey.cmds[2] = tx_out.script_publickey.cmds[2].hex()
            tx_out.script_publickey = tx_out.script_publickey.__dict__
            self.txs_out[tx_index] = tx_out.__dict__

        return self.__dict__

class TxnIn:
    def __init__(self, prev_tx, prev_index, script_sig = None, sequence = 0xffffffff):
        self.prev_tx = prev_tx # id of the prev_tx => hash of the prev_transaction
        self.prev_index = prev_index

        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig

        self.sequence = sequence

    def serialize(self):
        result = self.prev_tx[::-1]
        result += int_to_little_endian(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_little_endian(self.sequence, 4)
        return result


class TxnOut:
    def __init__(self, amount, script_publickey):
        self.amount = amount
        self.script_publickey = script_publickey

    def serialize(self):
        result = int_to_little_endian(self.amount, 8)
        result += self.script_publickey.serialize()
        return result