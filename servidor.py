import socket
import threading
import argparse
from common import MSG_TYPE, File

FORMAT = "ascii"
PAYLOAD_SIZE = 1000


def parse_args():
    parser = argparse.ArgumentParser(description='Servidor')
    parser.add_argument('port', type=int)
    return parser.parse_args()


def open_control_channel(tcp_port, server):
    tcp_addr = (server, tcp_port)

    control_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_channel.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    control_channel.bind(tcp_addr)
    return control_channel


def open_data_channel(udp_port, server):
    udp_addr = (server, udp_port)

    data_channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_channel.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_channel.bind(udp_addr)
    return data_channel


def greet_client(control_channel, data_channel):

    # Recebe HELLO (1) - Controle
    hello = control_channel.recv(2)
    if hello != MSG_TYPE["HELLO"]:
        print("Wrong handshake")
        control_channel.close()

    # Envia CONNECTION  (2) - Controle
    msg_type = MSG_TYPE["CONNECTION"]
    udp_port = data_channel.getsockname()[1]
    udp_port = str(udp_port).encode(FORMAT)

    # TODO udp port tem 5 bytes e não 4
    udp_port += b' ' * (5 - len(udp_port))
    message = msg_type + udp_port
    control_channel.send(message)
    return data_channel

def test(control_channel, data_channel):

    # Recebe HELLO (1) - Controle
    info_file_byte = control_channel.recv(30)
    control_channel.send(b'AAA')

def receive_info_file(control_channel):

    # Recebe INFO FILE (3) - Controle
    file = File()

    info_file_byte = control_channel.recv(30)
    msg_type = info_file_byte[:2]
    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file_size = info_file_byte[17:].decode(FORMAT).strip()

    file.file_name = str(file_name).strip()
    file.file_size = file_size

    # Envia OK (4) - Controle
    control_channel.send(MSG_TYPE["OK"])
    return file


def receive_file(control_channel, data_channel, arquivo):
    file_size = int(arquivo.file_size)
    qnts_pacotes = file_size // PAYLOAD_SIZE
    if qnts_pacotes * PAYLOAD_SIZE < file_size:
        qnts_pacotes += 1

    pacotes = [None for i in range(qnts_pacotes)]

    for i in range(qnts_pacotes):
        # Recebe FILE (6) - Dados
        packed_file, client = data_channel.recvfrom(PAYLOAD_SIZE + 10)

        msg_type = packed_file[:2]
        sequence_num = int(packed_file[2:6])
        payload_size = packed_file[6:8]
        arquivo.payload_size = payload_size
        payload = packed_file[8:]
        if payload:
            pacotes[sequence_num] = payload

        # Envia ACK(7) - Controle
        control_channel.send(MSG_TYPE["ACK"])

    arquivo.bin_file = pacotes


def save_file(arquivo):
    filename = str(arquivo.file_name).split("/")[-1]
    filename = "output/" + filename

    with open(filename, "wb") as out:
        for i, pacote in enumerate(arquivo.bin_file):
            print("salvando pacote num", i)
            out.write(pacote)


def end_connection(connection):
    # Envia FIM(5) - Controle
    connection.send(MSG_TYPE["FIM"])
    connection.shutdown(1)
    connection.close()


def handle_client(control_channel, server, address):
    print(f"New address connected: {address}")

    udp_port = 3030  # TODO como designar isso de forma automatica?
    data_channel = open_data_channel(udp_port, server)
    greet_client(control_channel, data_channel)
    file = receive_info_file(control_channel)
    receive_file(control_channel, data_channel, file)
    save_file(file)
    end_connection(control_channel)


def main():
    args = parse_args()
    server = socket.gethostbyname(socket.gethostname())

    tcp_port = args.port
    control_channel = open_control_channel(tcp_port, server)
    control_channel.listen()

    print(f"Waiting connections")

    while True:
        new_tcp_conn, new_client_addr = control_channel.accept()
        new_thread = threading.Thread(target=handle_client, args=(new_tcp_conn, server, new_client_addr))
        new_thread.start()
        print(f"Active Connections: {threading.activeCount() - 1}")

if __name__ == "__main__":
    main()
