import socket
import threading
import argparse

parser = argparse.ArgumentParser(description='Servidor')
parser.add_argument('port', type=int)
args = parser.parse_args()

PORT = args.port
HEADER = 64
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "ascii"
DISCONNECT_MSG = "!close"

# new socket
# family, type
# TODO receber do teclado
# todo definir se a conexão é ipv4 ou ipv6
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# binds the server with this new connection
server.bind(ADDR)

def handle_client(connection, address):
    print(f"New connection: {address}")

    connected = True
    while connected:
        msg_length = connection.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = connection.recv(msg_length).decode(FORMAT)
            print(f"{address} said: {msg}")
            connection.send("ACK".encode(FORMAT))
            if msg == DISCONNECT_MSG:
                connected = False
    connection.close()


def start():


    server.listen()
    print(f"Waiting connections in {SERVER}")

    while True:
        new_addr, new_conn = server.accept()  # a new client is trying to connect
        new_thread = threading.Thread(target=handle_client, args=(new_addr, new_conn))
        new_thread.start()
        print(f"Active Connections: {threading.activeCount() - 1}")  # less 1 because the star function is a thread


if __name__ == "__main__":
    print("Server starting")
    start()
