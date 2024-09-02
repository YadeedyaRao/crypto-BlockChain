import socket
import threading
import sys
import json
import time
randezvous = ('192.168.137.1', 55555)
my_port = 50001
def getPeers(sock):
    print("conneting to randezvous server")
    sock.sendto(b'0', randezvous) # dummy message

    while True:
        data = sock.recv(1024).decode()
        if data.strip() == 'ready':
            print('checked with the server, waiting')
            break

    data = sock.recv(1024).decode()
    ip, s_port, d_port = data.split(' ')
    s_port = int(s_port)
    d_port = int(d_port)
    return [(ip, s_port, d_port)] # for now only one peer

def send_block_msg(msg, addr, sock):
    message = {'type' : 'BLOCK_UPDATE', 'data' : json.dumps(msg)}
    message = json.dumps(message)
    sock.sendto(message.encode(), addr)

def send_utxos_msg(msg, addr, sock):
    message = {'type' : 'UTXOS_STATE', 'data' : json.dumps(msg)}
    sock.sendto(message.encode(), addr)

def send_txns_msg(msg, addr, sock):
    message = [{'type' : 'MEMPOOL', 'data' : msg}]
    message = json.dumps(message)
    sock.sendto(message.encode(), addr)

def verify_transactions(txns):
    pass
    # for txn in txns:
    #     #check for valid utxos
    #     newutxos = {}
    #     try:
    #         while len(newutxos) < 1:
    #             newutxos = dict(UTXOS)
    #             time.sleep(2)
    #     except Exception as e:
    #         print("Error converting managed dict to dict")

    #         for TxByte in memPool:
    #             TxObj = newutxos[TxByte]

    #             if 

def verify_block(block_dict):
    for blck_hash in block_dict:
        blck = block_dict[blck_hash]
        #verify transactions
        verify_transactions(blck["Txns"])

def client_p2p_main(block_buffer, utxos_buffer, mempool_buffer):
    global UTXOS
    UTXOS = utxos_buffer
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', my_port))# client uses this port
    peers = getPeers(sock)
    for peer in peers:
        (ip, s_port, d_port) = peer
        print('\n got peer')
        print(f'ip_address: {ip}\nsource port : {s_port}\ndestination port : {d_port}\n')
        print(f"Punching Hole for inbound from {ip}, {s_port}")
        sock.sendto(b'0', (ip, s_port))

        print("Punched Hole")
    #listen messages from my port after punching holes
    def listen():
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg != '0':
                    msg = json.loads(msg)
                    typ = msg['type']
                    print(f'\r{typ} message recieved from {addr}\n>', end = '')
                    if typ == 'BLOCK_UPDATE':
                        verify_block(msg['data'])
            except ConnectionResetError as ce:
                print(f'ERROR: {ce}')

    listener = threading.Thread(target= listen, daemon=True)
    listener.start()

    while True:
        # If any block is not relayed relay it
        while len(block_buffer) >= 1:
            msg = block_buffer.popitem()
            for peer in peers:
                send_block_msg(msg, (ip, s_port), sock)
        # while len(utxos_buffer) >= 1:
        #     msg = utxos_buffer.pop()
        #     for peer in peers:
        #         send_utxos_msg(msg, (ip, s_port), sock)
        # while len(mempool_buffer) >= 1:
        #     msg = mempool_buffer.pop()
        #     for peer in peers:
        #         send_txns_msg(msg, (ip, s_port), sock)