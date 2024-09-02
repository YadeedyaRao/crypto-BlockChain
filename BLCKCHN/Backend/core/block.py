class Block:
    def __init__(self, Height, Blocksize, BlockHeader, TxnCount, Txns):
        self.Height = Height
        self.Blocksize = Blocksize
        self.BlockHeader = BlockHeader
        self.TxnCount = TxnCount
        self.Txns = Txns