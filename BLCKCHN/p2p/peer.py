import socket
import threading
import json
import hashlib

class DHTNode:
    def __init__(self, port, bootstrap_ip=None, bootstrap_port=None):
        self.abort = False
        self.port = port
        self.bootstrap_ip = bootstrap_ip
        self.bootstrap_port = bootstrap_port
        self.node_ip = 'localhost'
        self.dht = {}  # Simple dictionary to store key-value pairs
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind((self.node_ip, self.port))
        if bootstrap_ip and bootstrap_port:
            self.join_network(bootstrap_ip, bootstrap_port)
        else:
            print("This is the bootstrap node.")

    def join_network(self, ip, port):
        message = {'type': 'JOIN', 'ip': self.node_ip, 'port': self.port}
        self.client_sock.connect((ip, port))# client connects to a server
        self.request_message(message)

    def serve_message(self, conn, message):
        conn.sendall(json.dumps(message).encode())# server sends message to a particular connection

    def request_message(self, message):
        self.client_sock.sendall(json.dumps(message).encode())# client sends request message to the bootstrap connection

    def handle_message(self, conn, addr):
        while True: 
            try:
                message = conn.recv(1024)
                if message :
                    message = json.loads(message.decode())
                    if message['type'] == 'JOIN':
                        print(f"Node joined: {message['ip']}:{message['port']}")
                    elif message['type'] == 'STORE':
                        self.dht[message['key']] = message['value']
                        print(f"Stored {message['key']}={message['value']}")
                    elif message['type'] == 'LOOKUP':
                        value = self.dht.get(message['key'], None)
                        response = {'type': 'LOOKUP_RESPONSE', 'key': message['key'], 'value': value}
                        self.serve_message(conn, response)
                    elif message['type'] == 'CAS':
                        print(f"{addr} says {message['data']}")
                else:
                    break
            except ConnectionResetError:
                print(f"connection with {addr} is lost!")
        conn.close()


    def recieve_message(self):
        self.server_sock.listen()# server listens for messages
        print(f"Node is listening on port {self.port}")
        while not self.abort:
            conn, addr = self.server_sock.accept()
            print(f"Connection from address {addr}")
            client_thread = threading.Thread(target= self.handle_message, args= (conn,addr))
            client_thread.start()
        print("stopped rm")

    def run(self):
        recv_thread = threading.Thread(target= self.recieve_message, args =())
        recv_thread.start()

    def send_casual_message(self, msg):
        message = {'type' : 'CAS', 'data' : msg}
        self.request_message(message)

    def store(self, key, value):
        message = {'type': 'STORE', 'key': key, 'value': value}
        self.send_message(self.node_ip, self.port, message)

    def lookup(self, key):
        message = {'type': 'LOOKUP', 'key': key}
        self.send_message(self.node_ip, self.port, message)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='DHT Node')
    parser.add_argument('--port', type=int, required=True, help='Port number for this node')
    parser.add_argument('--bootstrap_ip', type=str, help='Bootstrap node IP')
    parser.add_argument('--bootstrap_port', type=int, help='Bootstrap node port')
    parser.add_argument('--request', type = str, help='send request')
    args = parser.parse_args()

    node = DHTNode(args.port, args.bootstrap_ip, args.bootstrap_port)
    t = threading.Thread(target=node.run)
    t.start()

    while True:
        inp = input("send a message\n").split()
        if inp[0] == '<quit>':
            print("entered...")
            node.abort = True
            # t.join()
            # print("stopeed thread")
            # #cleanup the sockets
            # node.client_sock.close()
            # node.server_sock.close()
            # break
        elif inp[0] == '<msg>':
            msg = inp[1]
            if len(inp) == 2 : 
                node.send_casual_message(msg)
            else:
                for part in inp[2:]:
                    msg += ' '+ part
                node.send_casual_message(msg)
    
    # For testing: store and lookup values
    # import time
    # time.sleep(5)  # Give some time for the node to join network
    # node.store('key1', 'value1')
    # time.sleep(5)  # Give some time for the store to propagate
    # node.lookup('key1')