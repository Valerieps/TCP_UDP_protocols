import socket
import threading
import argparse
import sys

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


def greet_client(connection):
    # Recebe HELLO (1) - Controle
    hello = connection.recv(2)
    if hello != b' 1':
        print("Wrong handshake")
        connection.close()

    # Envia CONNECTION  (2) - Controle
    connection.send(b' 2')

    # Recebe INFO FILE (3) - Controle
    info_file_byte = connection.recv(26)
    msg_type = info_file_byte[:2]
    file_name = info_file_byte[2:17]
    file_size = info_file_byte[17:]

    print(info_file_byte)
    print(msg_type)
    print(file_name)
    print(file_size)

    # Envia OK (4) - Controle
    connection.send(b' 4')


def receive_file(connection):

    # Recebe FILE (6) - Dados
    packed_file = connection.recv(1010)
    msg_type = packed_file[:2]
    sequence_num = packed_file[2:6]
    payload_size = packed_file[6:8]
    file_chunk = packed_file[8:]

    print(f"{msg_type=}")
    print(f"{sequence_num=}")
    print(f"{payload_size=}")
    print(f"{file_chunk=}")

    # Envia ACK(7) - Controle
    connection.send(b' 7')

def end_connection(connection):
    connection.shutdown(1)
    connection.close()


def handle_client(connection, address):
    print(f"New address: {address}")
    greet_client(connection)
    receive_file(connection)
    end_connection(connection)


def start():
    server.listen()
    print(f"Waiting connections in {SERVER}")
    while True:
        new_conn, new_addr = server.accept()  # a new client is trying to connect
        new_thread = threading.Thread(target=handle_client, args=(new_conn, new_addr))
        new_thread.start()
        print(f"Active Connections: {threading.activeCount() - 1}")  # less 1 because the star function is a thread


if __name__ == "__main__":
    print("Server starting")
    start()
