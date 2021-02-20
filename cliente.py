import socket
import argparse
from common import MSG_TYPE


parser = argparse.ArgumentParser(description='Servidor')
parser.add_argument('ip', type=str)
parser.add_argument('port', type=int)
parser.add_argument('file', type=str)
args = parser.parse_args()

PORT = args.port
SERVER = args.ip
HEADER = 64
FORMAT = "ascii"
DISCONNECT_MSG = "!close"
ADDR = (SERVER, PORT)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(ADDR)

def greet_server():
    socket.send(MSG_TYPE["HELLO"])
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)

def send_file_info(FILENAME):

    # Envia INFO FILE (3) - Controle
    msg_type = MSG_TYPE["INFO_FILE"]
    file_name = bytearray(FILENAME, FORMAT)
    file_name += b' ' * (15 - len(file_name))
    file_size = b'10'
    file_size += b' ' * (8 - len(file_size))
    info_file = msg_type + file_name + file_size
    socket.send(info_file)

    # recebe OK (4) - Controle
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


def send_file():
    # Envia FILE (6) - Dados
    msg_type = MSG_TYPE["FILE"]
    sequence_num = b'0'
    sequence_num += b' ' * (4 - len(sequence_num))
    payload_size = b'10'
    payload_size += b' ' * (2 - len(payload_size))
    file = b'Igor mais lindao'
    packed_file = msg_type + sequence_num + payload_size + file

    socket.send(packed_file)

    # Recebe ACK(7) - Controle
    rcv = socket.recv(3)
    print(rcv)

if __name__ == "__main__":
    FILENAME = args.file

    greet_server()
    send_file_info(FILENAME)
    send_file(FILENAME)
