import socket
import argparse
from common import MSG_TYPE, File

FORMAT = "ascii"
PAYLOAD_SIZE = 1000


def parse_args():
    parser = argparse.ArgumentParser(description='Servidor')
    parser.add_argument('ip', type=str)
    parser.add_argument('port', type=int)
    parser.add_argument('file', type=str)
    return parser.parse_args()


def connect_to_control_channel(args):
    tcp_port = args.port
    server = args.ip
    tcp_addr = (server, tcp_port)

    # cria conexão TCP
    control_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_channel.connect(tcp_addr)
    return control_channel


def greet_server(control_channel):
    control_channel.send(MSG_TYPE["HELLO"])
    server_answer = control_channel.recv(7).decode(FORMAT)
    msg_type = server_answer[:2]
    data_channel_port = int(server_answer[2:])
    return data_channel_port

def test(control_channel):
    control_channel.send(MSG_TYPE["HELLO"])
    server_answer = control_channel.recv(7).decode(FORMAT)
    print(server_answer)


def open_data_channel(args, data_channel_port):
    udp_addr = (args.ip, data_channel_port)

    # cria conexão UDP
    data_channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_channel.connect(udp_addr)
    return data_channel


def parse_file(filename):
    arquivo = File()
    arquivo.bin_file = open(filename, "rb").read()
    arquivo.file_name = bytearray(filename, FORMAT)
    arquivo.file_size = str(len(arquivo.bin_file)).encode(FORMAT)
    return arquivo


def send_file_info(control_channel, arquivo):
    # Envia INFO FILE (3) - Controle
    msg_type = MSG_TYPE["INFO_FILE"]
    file_name = arquivo.file_name
    file_name += b' ' * (15 - len(file_name))
    file_size = arquivo.file_size
    file_size += b' ' * (8 - len(file_size))
    print(f"{file_size=}")

    info_file = msg_type + file_name + file_size
    print(f"{len(info_file)=}")

    control_channel.send(info_file)
    print("mandou")

    # Recebe OK (4) - Controle
    rcv = control_channel.recv(3).decode(FORMAT)

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


def send_file(data_channel, control_channel, arquivo):
    # Envia FILE (6) - Dados
    msg_type = MSG_TYPE["FILE"]

    for idx, package in break_in_chunks(arquivo.bin_file, payload_size=1000):
        # print(idx)
        idx = str(idx).encode(FORMAT)
        sequence_num = bytes(idx)
        sequence_num += b' ' * (4 - len(sequence_num))

        payload_size = b'11'  # todo descobrir o que é isso
        payload_size += b' ' * (2 - len(payload_size))

        packed_file = msg_type + sequence_num + payload_size + package
        data_channel.sendto(packed_file, data_channel.getpeername())

        # Recebe ACK(7) - Controle
        rcv = control_channel.recv(3)
        # print(rcv)


def main():
    args = parse_args()
    filename = args.file

    control_channel = connect_to_control_channel(args)
    data_channel_port = greet_server(control_channel)
    data_channel = open_data_channel(args, data_channel_port)
    arquivo = parse_file(filename)
    send_file_info(control_channel, arquivo)
    # send_file(data_channel, control_channel, arquivo)


if __name__ == "__main__":
    main()

