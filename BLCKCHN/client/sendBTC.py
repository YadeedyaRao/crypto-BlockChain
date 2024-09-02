from BLCKCHN.Backend.util.util import decode_base58
from BLCKCHN.Backend.core.Script import Script
from BLCKCHN.Backend.core.Txn import Txn, TxnIn, TxnOut, MINER_ADDRESS
from BLCKCHN.Backend.core.database.database import AccountDB
from BLCKCHN.Backend.core.EllepticCurve.EllepticCurve import PrivateKey
import time
class sendBTC:
    def __init__(self, fromAccount, toAccount, amount, UTXOS):
        print(f"[sendBTC]: Intiated transaction from {fromAccount} to {toAccount} of amount {amount} units")
        self.COIN = 100000000
        self.from_public_address = fromAccount
        self.to_public_address = toAccount
        self.amount = amount * self.COIN
        self.UTXOS = UTXOS
        self.isEnoughBalance = True #by default assume honest request

    def scriptPublicKey(self, publicAddress):
        h160 = decode_base58(publicAddress) #get public key hash - also verifies if the address is valid [checksum  ]
        script_pubkey = Script().p2pkh_script(h160)
        return script_pubkey #return script obj with hash as element
    
    def getPrivateKey(self): #used to sign the txn
        Allaccounts = AccountDB().read()
        for account in Allaccounts:
            if account["public_address"] == self.from_public_address:
                return account["private_key"]
            

    def prepareTxIn(self):
        TxIns = []
        self.Total = 0
        """Convert public address into publick key hash to fin txns_out lock into this public key hash"""

        self.from_address_script_pubkey = self.scriptPublicKey(self.from_public_address)
        self.fromPubKeyHash = self.from_address_script_pubkey.cmds[2]

        newutxos = {} #its a dictionary {TxnId : TxnObj}, defined in blockchain.py

        try:
            while len(newutxos) < 1 :
                newutxos = dict(self.UTXOS) #UTXOs are Managed dictionary between front-end and back-end processes so we need to convert them into normal dictionary
                time.sleep(2)
        except Exception as e:
            print(f"Error in converting the Managed Dict to Normal Dict")

        for Txbyte in newutxos:
            TxObj = newutxos[Txbyte]
            for index, txout in enumerate(TxObj.txs_out):
                if txout.script_publickey.cmds[2] == self.fromPubKeyHash:
                    if self.Total < self.amount + self.COIN:
                            prev_tx = bytes.fromhex(TxObj.id())
                            self.Total += txout.amount
                            TxIns.append(TxnIn(prev_tx, index))
                    else:
                        break
        fee = self.COIN
        if self.from_public_address == MINER_ADDRESS:
            fee = 0
        if self.Total < self.amount+fee:
            self.isEnoughBalance = False

        return TxIns
        
    def prepareTxOut(self):
        TxnOuts = []
        """charge fee for miner"""
        fee = self.COIN
        to_address_script_pubkey = self.scriptPublicKey(self.to_public_address)
        #output for reciever
        TxnOuts.append(TxnOut(self.amount, script_publickey= to_address_script_pubkey))
        print(f"[sendBTC]: made tx_out for reciever {self.to_public_address} with {self.amount} units")

        #output for sender
        changeAmount = self.Total - self.amount - fee
        if changeAmount > 0:
            TxnOuts.append(TxnOut(changeAmount, self.from_address_script_pubkey))
            print(f"[sendBTC]: returning change tx_out for sender {self.from_public_address} with {changeAmount} units")

        return TxnOuts


    def signTxn(self):
        secret = self.getPrivateKey()
        priv = PrivateKey(secret= secret)

        for index, input in enumerate(self.TxnIns):
            self.TxnObj.sign_input(index, priv, self.from_address_script_pubkey)

        return True

    def prepareTransaction(self):
        self.TxnIns = self.prepareTxIn()
        if(self.isEnoughBalance):
            self.TxnOuts = self.prepareTxOut()
            self.TxnObj = Txn(1, self.TxnIns, self.TxnOuts, 0)
            self.signTxn()
            self.TxnObj.TxId = self.TxnObj.id()
            print(f"[sendBTC]: alien(non-coinbase) transaction done with id {self.TxnObj.TxId}")
            return self.TxnObj
        print("Not succeded")
        return False
