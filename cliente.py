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
PAYLOAD_SIZE = 1000

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(ADDR)


def greet_server():
    socket.send(MSG_TYPE["HELLO"])
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


def parse_file(FILENAME):
    arquivo = File()
    arquivo.bin_file = open(FILENAME, "rb").read()
    arquivo.file_name = bytearray(FILENAME, FORMAT)
    arquivo.file_size = str(len(arquivo.bin_file)).encode(FORMAT)
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

    # Recebe OK (4) - Controle
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


def break_in_chunks(bin_data, payload_size=PAYLOAD_SIZE):
    qnts_pacotes = len(bin_data) // PAYLOAD_SIZE
    if qnts_pacotes * PAYLOAD_SIZE < len(bin_data):
        qnts_pacotes += 1

    start = None
    idx = None

    for idx in range(qnts_pacotes):
        start = idx * payload_size
        end = start + payload_size
        yield idx, bin_data[start:end]
    yield idx, bin_data[start:]


def send_file(arquivo):
    # Envia FILE (6) - Dados
    msg_type = MSG_TYPE["FILE"]

    for idx, package in break_in_chunks(arquivo.bin_file, payload_size=1000):
        print(idx)
        idx = str(idx).encode(FORMAT)
        sequence_num = bytes(idx)
        sequence_num += b' ' * (4 - len(sequence_num))

        payload_size = b'11'  # todo descobrir o que é isso
        payload_size += b' ' * (2 - len(payload_size))

        packed_file = msg_type + sequence_num + payload_size + package
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

