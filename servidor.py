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
    print("Greeting client")
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


def receive_info_file(control_channel):
    print("Receiving file info")

    # Recebe INFO FILE (3) - Controle
    file = File()

    info_file_byte = control_channel.recv(30)
    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file_size = info_file_byte[17:].decode(FORMAT).strip()

    file.file_name = str(file_name).strip()
    file.file_size = int(file_size)
    file.get_total_packages(PAYLOAD_SIZE)
    print(f"{file.total_packages=}")

    # Envia OK (4) - Controle
    control_channel.send(MSG_TYPE["OK"])
    return file


def receive_file(control_channel, data_channel, arquivo):
    print("Receiving file data")

    received_packages = [None for _ in range(arquivo.total_packages)]

    # Recebe FILE (6) - Dados
    print("Expecting to receive", arquivo.file_size, "bytes")
    print("Received", end = " ")
    while arquivo.bytes_received < arquivo.file_size:
        packed_file, client = data_channel.recvfrom(PAYLOAD_SIZE + 10)
        sequence_num = int(packed_file[2:6])
        payload = packed_file[8:]
        if payload:
            received_packages[sequence_num] = payload
            arquivo.bytes_received += len(payload)
            print(arquivo.bytes_received, end = ", ")

        # Envia ACK(7) - Controle
        sequence_num = packed_file[2:6]
        ack = MSG_TYPE["ACK"] + sequence_num
        control_channel.send(ack)

    arquivo.packages = received_packages


def save_file(arquivo):
    print("Saving file")
    filename = str(arquivo.file_name).split("/")[-1]
    filename = "output/" + filename

    print("salvando pacote num")
    with open(filename, "wb") as out:
        for i, pacote in enumerate(arquivo.packages):
            print(i, ",", end="")
            out.write(pacote)


def handle_client(control_channel, server, address):
    print(f"New address connected: {address}")

    data_channel = open_data_channel(0, server)
    greet_client(control_channel, data_channel)
    file = receive_info_file(control_channel)
    receive_file(control_channel, data_channel, file)
    save_file(file)
    control_channel.send(MSG_TYPE["FIM"])
    data_channel.close()
    control_channel.close()
    print("All Done!")


def main():
    args = parse_args()
    tcp_port = args.port
    server = socket.gethostbyname(socket.gethostname())
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
