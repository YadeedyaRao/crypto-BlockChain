import sys
sys.path.append('E:/blockchain')

from BLCKCHN.Backend.core.block import Block
from BLCKCHN.Backend.core.blockheader import BlockHeader
from BLCKCHN.Backend.util.util import hash256, merkle_root, target_to_bits
from BLCKCHN.Backend.core.database.database import BlockchainDB
from BLCKCHN.Backend.core.Txn import CoinbaseTxn
from multiprocessing import Process, Manager
from BLCKCHN.Frontend.run import main
from BLCKCHN.p2p.client import client_p2p_main
import time


ZERO_HASH = '0' * 64

VERSION = 1

INITIAL_TARGET = 0x0000ffff00000000000000000000000000000000000000000000000000000000 #4 leading zeros


class Blockchain:
    def __init__(self, utxos, memPool, block_buffer):
        self.utxos = utxos
        self.memPool = memPool
        self.block_buffer = block_buffer
        self.current_target = INITIAL_TARGET
        self.bits = target_to_bits(INITIAL_TARGET) #stored in bytes format

    def write_on_disk(self, block):
        blockchainDB = BlockchainDB()
        blockchainDB.write(block)

    def fetch_last_block(self):
        blockchainDB = BlockchainDB()
        return blockchainDB.lastBlock()
    
    def GenesisBlock(self):
        BlockHeight = 0
        prevBlockHash = ZERO_HASH
        self.addBlock(BlockHeight, prevBlockHash)
    """Keep track of all the unspent transaction in cache memory for fast transactions for fast retrival"""
    def store_utxos_in_cache(self):
        for txn in self.addTransactionsInBLock:
            print(f"[UTXOS]: Added txn with txn id {txn.TxId}")
            self.utxos[txn.TxId] = txn

    def remove_spent_txns(self):
        for [txn_id, txn_index] in self.rmv_spnt_txns:
            if txn_id.hex() in self.utxos:
                if len(self.utxos[txn_id.hex()].txs_out) < 2 :
                    del self.utxos[txn_id.hex()]
                    print(f"[UTXOS]: Deleted spent txn with id {txn_id.hex()}")
                else:
                    del self.utxos[txn_id.hex()].txs_out[txn_index]
                    print(f"[UTXOS]: Deleted spent txn_out for transaction with id {txn_id.hex()} at index {txn_index}")
            else:
                print("[UTXSO]: Error in handling spent transactions?")

    def calculate_fee(self):
        self.fee = 0
        input_amount = 0
        output_amount = 0
        """Calculate input amount"""
        for [txn_id, txn_index] in self.rmv_spnt_txns:
            if txn_id.hex() in self.utxos:
                input_amount += self.utxos[txn_id.hex()].txs_out[txn_index].amount

        """Calculate output amount"""
        for txn in self.addTransactionsInBLock:
            for tx_out in txn.txs_out:
                output_amount += tx_out.amount
        
        self.fee = input_amount - output_amount
        

    """Read txns from memory pool"""
    def read_transaction_from_mempool(self):
        self.BlockSize = 80 # 4(version) + 32(prevBlockHash) +32(merkleroot) + 4(timestamp) + 4(bits) + 4(nonce) = 64 + 16 = 80
        self.TxIds = []
        self.addTransactionsInBLock= []
        self.rmv_spnt_txns = []

        for tx_id in self.memPool:
            self.TxIds.append(bytes.fromhex(tx_id))
            self.addTransactionsInBLock.append(memPool[tx_id])
            self.BlockSize += len(self.memPool[tx_id].serialize())
            for spent in self.memPool[tx_id].txs_in:
                self.rmv_spnt_txns.append([spent.prev_tx, spent.prev_index])
        self.memPool.clear()

    def remove_txns_from_mempool(self):
        for txn_id in self.TxIds:
            if txn_id.hex() in self.memPool:
                del self.memPool[txn_id.hex()]

    def convert_to_json(self):
        self.TxJson = []

        for tx in self.addTransactionsInBLock:
            self.TxJson.append(tx.to_dict())

    def overlay_to_network(self, blck_obj):
        self.block_buffer[blck_obj[0]["BlockHeader"]["blockHash"]] = blck_obj


    def addBlock(self, BlockHeight, prevBlockHash):
        self.read_transaction_from_mempool() #adds all txns from mempool
        self.calculate_fee()
        timestamp = int(time.time())
        coinbase_instance = CoinbaseTxn(BlockHeight)
        coinbaseTxn = coinbase_instance.CoinbaseTransaction() #coinbase txn
        coinbaseTxn.txs_out[0].amount += self.fee
        self.BlockSize += len(coinbaseTxn.serialize())
        self.TxIds.insert(0, bytes.fromhex(coinbaseTxn.id()))
        self.addTransactionsInBLock.insert(0, coinbaseTxn)
        
        
        merkleroot = merkle_root(self.TxIds)[::-1].hex()#since bytes are in little_endian_format
        Block_Header = BlockHeader(VERSION, prevBlockHash, merkleroot, timestamp, self.bits)
        Block_Header.mine(self.current_target)
        self.remove_spent_txns()
        #self.remove_txns_from_mempool()
        self.store_utxos_in_cache()
        self.convert_to_json()
        print(f"[BLCKCHN]: Block {BlockHeight} mined successfully with nonce value of {Block_Header.nonce}")
        dict_block = [Block(BlockHeight, self.BlockSize, Block_Header.__dict__, 1, self.TxJson).__dict__]
        self.overlay_to_network(dict_block)
        self.write_on_disk(dict_block)

    def main(self):
        lastBlock = self.fetch_last_block()
        if lastBlock is None:
            self.GenesisBlock()
        while True:
            lastBlock = self.fetch_last_block()
            BlockHeight = lastBlock["Height"]+1
            prevBlockHash = lastBlock["BlockHeader"]["blockHash"]
            self.addBlock(BlockHeight, prevBlockHash)


if __name__ == "__main__":
    with Manager() as manager:
        utxos = manager.dict()
        memPool = manager.dict()
        block_buffer = manager.dict()
        utxos_buffer = manager.dict()
        memPool_buffer = manager.dict()
        webApp = Process(target = main, args = (utxos, memPool,))
        p2p_overlay = Process(target = client_p2p_main, args = (block_buffer, utxos_buffer, memPool_buffer,))
        webApp.start()
        p2p_overlay.start()

        Blockchain = Blockchain(utxos, memPool, block_buffer)
        Blockchain.main()