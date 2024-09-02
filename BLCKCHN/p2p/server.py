import socket

known_port = 50002

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('192.168.137.1', 55555))
bind_ip, bind_port = sock.getsockname()

print(f"IP is {bind_ip}")

while True:
    clients = []
    
    while True:
        data, addr = sock.recvfrom(128)
        print(f"connection from {addr}")
        clients.append(addr)

        sock.sendto(b'ready', addr)

        if len(clients) == 2:
            if clients[0] == clients[1]:
                clients.pop()
            else:
                print("got two clients sending addresses to each other")
                break
    
    cl1 = clients.pop()
    cl2 = clients.pop()
    cl1_ip, cl1_port = cl1
    cl2_ip, cl2_port = cl2

    sock.sendto(f"{cl1_ip} {cl1_port} {known_port}".encode(), cl2)
    sock.sendto(f"{cl2_ip} {cl2_port} {known_port}".encode(), cl1)