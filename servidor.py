import socket
import threading
import argparse
from common import MSG_TYPE

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

class File:
    def __init__(self):
        self.file_name = None
        self.file_size = None
        self.payload_size = None
        self.bin_file = None

def greet_client(connection):
    # Recebe HELLO (1) - Controle
    hello = connection.recv(2)
    if hello != MSG_TYPE["HELLO"]:
        print("Wrong handshake")
        connection.close()

    # Envia CONNECTION  (2) - Controle
    connection.send(MSG_TYPE["CONNECTION"])




def receive_info_file(connection):

    # Recebe INFO FILE (3) - Controle
    file = File()

    info_file_byte = connection.recv(26)
    msg_type = info_file_byte[:2]
    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file_size = info_file_byte[17:].decode(FORMAT).strip()


    file.file_name = str(file_name).strip()
    file.file_size = file_size

    print(info_file_byte)
    print(msg_type)
    print(f"{file.file_name=}")
    print(file_size)

    # Envia OK (4) - Controle
    connection.send(MSG_TYPE["OK"])
    return file


def receive_file(connection, file):
    # Recebe FILE (6) - Dados
    packed_file = connection.recv(1010)
    msg_type = packed_file[:2]
    sequence_num = packed_file[2:6]
    payload_size = packed_file[6:8]
    file_chunk = packed_file[8:]

    file.payload_size = payload_size
    file.bin_file = file_chunk

    print(f"{msg_type=}")
    print(f"{sequence_num=}")
    print(f"{payload_size=}")
    print(f"{file_chunk=}")

    # Envia ACK(7) - Controle
    connection.send(MSG_TYPE["ACK"])

def save_file(file):
    # abrir o arquivo da extensão correta
    filename = "output/" + file.file_name
    with open(filename, "wb") as out:
        out.write(file.bin_file)

def end_connection(connection):
    # Envia FIM(5) - Controle
    connection.send(MSG_TYPE["FIM"])
    connection.shutdown(1)
    connection.close()


def handle_client(connection, address):
    print(f"New address: {address}")
    greet_client(connection)
    file = receive_info_file(connection)
    receive_file(connection, file)
    save_file(file)
    end_connection(connection)


def main():
    server.listen()
    print(f"Waiting connections in {SERVER}")

    while True:
        new_conn, new_addr = server.accept()  # a new client is trying to connect
        new_thread = threading.Thread(target=handle_client, args=(new_conn, new_addr))
        new_thread.start()
        print(f"Active Connections: {threading.activeCount() - 1}")  # less 1 because the star function is a thread


if __name__ == "__main__":
    main()
