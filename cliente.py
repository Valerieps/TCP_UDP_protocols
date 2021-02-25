import socket
import argparse
from common import MSG_TYPE, File

FORMAT = "ascii"
PAYLOAD_SIZE = 1000
WINDOW_SIZE = 10


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
    print("Greeting server")
    control_channel.send(MSG_TYPE["HELLO"])
    server_answer = control_channel.recv(7).decode(FORMAT)
    msg_type = server_answer[:2]
    data_channel_port = int(server_answer[2:])
    return data_channel_port


def open_data_channel(args, data_channel_port):
    udp_addr = (args.ip, data_channel_port)
    data_channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_channel.connect(udp_addr)
    return data_channel


def parse_file(filename):
    arquivo = File()
    bin_file = open(filename, "rb").read()

    arquivo.file_name = bytearray(filename, FORMAT)
    arquivo.file_size = str(len(bin_file)).encode(FORMAT)
    arquivo.get_total_packages(PAYLOAD_SIZE)

    pacotes = break_in_chunks(bin_file, arquivo, payload_size=1000)
    packed_files = add_header(pacotes)
    arquivo.packages = packed_files
    return arquivo


def send_file_info(control_channel, arquivo):
    # Envia INFO FILE (3) - Controle
    print("Sending file info")
    msg_type = MSG_TYPE["INFO_FILE"]
    file_name = arquivo.file_name
    file_name += b' ' * (15 - len(file_name))
    file_size = arquivo.file_size
    file_size += b' ' * (8 - len(file_size))
    info_file = msg_type + file_name + file_size
    control_channel.send(info_file)

    # Recebe OK (4) - Controle
    rcv = control_channel.recv(3).decode(FORMAT)
    print(rcv)


def break_in_chunks(bin_data, arquivo, payload_size=PAYLOAD_SIZE):
    qnts_pacotes = arquivo.total_packages
    pacotes = []
    start = None
    for idx in range(qnts_pacotes):
        start = idx * payload_size
        end = start + payload_size
        pacotes.append(bin_data[start:end])
    pacotes.append(bin_data[start:])
    return pacotes


def add_header(pacotes):
    pacotes_com_header = []
    msg_type = MSG_TYPE["FILE"]

    for idx, pacote in enumerate(pacotes):
        idx = str(idx).encode(FORMAT)
        sequence_num = bytes(idx)
        sequence_num += b' ' * (4 - len(sequence_num))
        payload_size = b'11'  # todo descobrir o que é isso
        payload_size += b' ' * (2 - len(payload_size))
        packed_file = msg_type + sequence_num + payload_size + pacote
        pacotes_com_header.append(packed_file)
    return pacotes_com_header


def send_file(data_channel, control_channel, arquivo):
    print("Sending file data")

    start = 0
    end = WINDOW_SIZE
    if end > arquivo.total_packages:
        end = arquivo.total_packages

    while end <= arquivo.total_packages:
        # Envia uma janela
        for package in range(start, end): # 0,1,2,3,4
            print("Enviando pacote", package)
            _ = data_channel.sendto(arquivo.packages[package], data_channel.getpeername())

            # Recebe ACK(7) - Controle
            rcv = control_channel.recv(7)
            sequence_num = int(rcv[2:].decode(FORMAT))
            print("Server recebeu pacote", sequence_num)

        # atualiza start e end
        start = end
        end += WINDOW_SIZE
        if end > arquivo.total_packages:
            end = arquivo.total_packages
        if start == end:
            break

def main():
    args = parse_args()
    filename = args.file

    control_channel = connect_to_control_channel(args)
    data_channel_port = greet_server(control_channel)
    data_channel = open_data_channel(args, data_channel_port)
    arquivo = parse_file(filename)
    send_file_info(control_channel, arquivo)
    send_file(data_channel, control_channel, arquivo)


if __name__ == "__main__":
    main()