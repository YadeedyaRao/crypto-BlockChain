from flask import Flask, render_template, request
from BLCKCHN.client.sendBTC import sendBTC
from BLCKCHN.Backend.core.Txn import Txn

app = Flask(__name__)

@app.route('/', methods = ["GET", "POST"])
def wallet():
    message = ''
    if request.method == "POST":
        fromAddress = request.form.get("fromAddress")
        toAddress = request.form.get("toAddress")
        Amount = request.form.get("Amount", type = int)
        sendCoin = sendBTC(fromAddress, toAddress, Amount, UTXOS)
        TxnObj = sendCoin.prepareTransaction()
        verified = True

        if not TxnObj:
            message = "Invalid txn"
        else:
            if isinstance(TxnObj, Txn):
                for index, txn in enumerate(TxnObj.txs_in):
                    if not TxnObj.verify_input(index, sendCoin.scriptPublicKey(fromAddress)):
                        verified = False
                        break
                if verified:
                    MEMPOOL[TxnObj.TxId] = TxnObj # add txn to mempool if its verified
                    message = "Transaction added in memory pool"
                    print(f"[MEMPOOL]: Added txn with id {TxnObj.TxId} to Mempool")
                else:
                    message = "Failed adding txn verification"
        
    return render_template("wallet.html", message= message)

def main(utxos, memPool):
    global UTXOS
    global MEMPOOL
    UTXOS = utxos
    MEMPOOL = memPool
    app.run()

