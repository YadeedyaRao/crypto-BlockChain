import socket
import threading
import sys
import json
randezvous = ('192.168.137.1', 55555)
my_port = 50003
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

if __name__ == '__main__':
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
            except ConnectionResetError as ce:
                print(f'ERROR: {ce}')

    listener = threading.Thread(target= listen, daemon=True)
    listener.start()

    while True:
        msg = input('> ')
        sock.sendto(msg.encode(), (ip, s_port))