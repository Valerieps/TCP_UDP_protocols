import socket
import argparse
from common import MSG_TYPE, File


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

def parse_file(FILENAME):
    arquivo = File()
    arquivo.bin_file = open(FILENAME, "rb").read()
    # print(arquivo.bin_file)
    arquivo.file_name = bytearray(FILENAME, FORMAT)
    arquivo.file_size = str(len(arquivo.bin_file)).encode(FORMAT)
    print(f"{arquivo.file_size=}")
    return arquivo

def send_file_info(arquivo):
    # Envia INFO FILE (3) - Controle
    msg_type = MSG_TYPE["INFO_FILE"]
    file_name = arquivo.file_name
    file_name += b' ' * (15 - len(file_name))
    file_size = arquivo.file_size
    file_size += b' ' * (8 - len(file_size))
    print(f"{file_size=}")

    info_file = msg_type + file_name + file_size
    socket.send(info_file)

    # recebe OK (4) - Controle
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


def send_file(arquivo):

    # Envia FILE (6) - Dados
    msg_type = MSG_TYPE["FILE"]

    sequence_num = b'0'
    sequence_num += b' ' * (4 - len(sequence_num))

    payload_size = b'10'
    payload_size += b' ' * (2 - len(payload_size))

    file = arquivo.bin_file
    packed_file = msg_type + sequence_num + payload_size + file

    socket.send(packed_file)

    # Recebe ACK(7) - Controle
    rcv = socket.recv(3)
    print(rcv)

def main(FILENAME):
    greet_server()
    arquivo = parse_file(FILENAME)
    send_file_info(arquivo)
    send_file(arquivo)


if __name__ == "__main__":
    FILENAME = args.file
    main(FILENAME)

