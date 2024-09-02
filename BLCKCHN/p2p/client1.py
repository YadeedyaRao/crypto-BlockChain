import socket
import threading
import sys

randezvous = ('192.168.137.1', 55555)

print("conneting to randezvous server")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 7001))
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


print('\n got peer')
print(f'ip_address: {ip}\nsource port : {s_port}\ndestination port : {d_port}\n')

print("punching hole")

sock.bind(('0.0.0.0', s_port))
sock.sendto(b'0', (ip, d_port))

def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', s_port))

    while True:
        data = sock.recv(1024)
        print(f'\rpeer: {data.decode()}\n>', end = '')

listener = threading.Thread(target= listen, daemon=True)
listen.start()



sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', d_port))

while True:
    msg = input('> ')
    sock.sendto(msg, (ip, s_port))