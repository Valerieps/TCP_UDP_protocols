import socket
import threading
import argparse
from common import MSG_TYPE, File, SlidingWindow
from collections import OrderedDict

FORMAT = "ascii"
PAYLOAD_SIZE = 1000
WINDOW_SIZE = 10


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
    _ = control_channel.recv(2)

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

    # Envia OK (4) - Controle
    control_channel.send(MSG_TYPE["OK"])

    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file_size = info_file_byte[17:].decode(FORMAT).strip()
    file.file_name = str(file_name).strip()
    file.file_size = int(file_size)

    sliding_window = SlidingWindow()
    sliding_window.get_total_packages(file)
    sliding_window.initialize_window(WINDOW_SIZE)

    return file, sliding_window


def receive_file(control_channel, data_channel, sliding_window):
    print("Receiving file data")

    file_data = [None for _ in range(sliding_window.total_packages)]

    while not sliding_window.finished:
        packed_file, client = data_channel.recvfrom(PAYLOAD_SIZE + 10)
        sequence_num = int(packed_file[2:6].decode(FORMAT))

        if sequence_num in sliding_window.current_window:
            print("recebido pacote:", sequence_num, end=", ")

            sliding_window.confirm_receipt(sequence_num)
            sliding_window.add_new_package_to_window()

            # Save package
            payload = packed_file[8:]
            file_data[sequence_num] = payload

            # Envia ACK(7) - Controle
            sequence_num = packed_file[2:6]
            ack = MSG_TYPE["ACK"] + sequence_num
            control_channel.send(ack)

    return file_data


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
    arquivo, sliding_window = receive_info_file(control_channel)
    receive_file(control_channel, data_channel, sliding_window)
    save_file(arquivo)
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
