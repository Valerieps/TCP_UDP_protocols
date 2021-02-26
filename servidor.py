import socket
from threading import Thread, Condition, activeCount
import argparse
from common import MSG_TYPE, FORMAT, PAYLOAD_SIZE, WINDOW_SIZE
from common import File, SlidingWindow
import time

def parse_args():
    parser = argparse.ArgumentParser(description='Servidor')
    parser.add_argument('port', type=int)
    return parser.parse_args()


def open_control_channel(tcp_port, server):
    tcp_addr = (server, tcp_port)

    # Se IPV4
    try:
        control_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_channel.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        control_channel.bind(tcp_addr)
    except:
        control_channel = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
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

    # msg_type = info_file_byte[:2]
    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file.file_name = str(file_name).strip()

    file_size = info_file_byte[17:].decode(FORMAT).strip()
    file.file_size = int(file_size)

    sliding_window = SlidingWindow()
    sliding_window.payload_size = PAYLOAD_SIZE
    sliding_window.get_total_packages(file)
    sliding_window.all_packages = [None for _ in range(sliding_window.total_packages)]
    sliding_window.initialize_window(WINDOW_SIZE)

    control_channel.send(MSG_TYPE["OK"])
    return file, sliding_window


# ============= PACKAGE RECEIVER FUNCTIONS =================
def package_receiver_manager(sliding_window, data_channel, condition):
    print("Starting Package Receiver")
    while not sliding_window.finished:
        c = Thread(target=package_receiver_task, args=(sliding_window, data_channel, condition))
        c.start()
        c.join()
    print("Received all expected packages")

def package_receiver_task(sliding_window, data_channel, condition):
    try:
        package, client = data_channel.recvfrom(PAYLOAD_SIZE + 10)
    except:
        return

    # msg_type = package[:2]
    sequence_number = package[2:6]
    # payload_size = package[6:8]
    payload = package[8:]

    sequence_number = int(sequence_number.decode(FORMAT))

    with condition:
        if sequence_number in sliding_window.current_window:
            print("Received package", sequence_number)
            sliding_window.all_packages[sequence_number] = payload
            sliding_window.confirm_receipt(sequence_number)
            sliding_window.to_confirm.add(sequence_number)
            sliding_window.add_new_package_to_window()


# ============= CONFIRMATION SENDER FUNCTIONS =================
def confirmation_sender_manager(sliding_window, control_channel, condition):
    print("Starting Confirmation Sender")

    while not sliding_window.finished:
        s = Thread(target=confirmation_sender_task, args=(sliding_window, control_channel, condition))
        s.start()
        s.join()

    # msg = MSG_TYPE["RECEIVED EVERYTHING"]
    # control_channel.send(msg)


def confirmation_sender_task(sliding_window, control_channel, condition):
    with condition:
        if sliding_window.to_confirm:
            sequence_number = sliding_window.to_confirm.pop()
            print("Sending confirmation", sequence_number)

            sequence_number = str(sequence_number).encode(FORMAT)
            sequence_number += b' ' * (2 - len(sequence_number))
            message = MSG_TYPE["ACK"] + sequence_number
            try:
                _ = control_channel.send(message)
            except:
                pass


def receive_file(control_channel, data_channel, sliding_window):
    print("Receiving file data")

    condition = Condition()
    package_receiver = Thread(target=package_receiver_manager, args=(sliding_window, data_channel, condition))
    confirmation_sender = Thread(target=confirmation_sender_manager, args=(sliding_window, control_channel, condition))
    package_receiver.start()
    confirmation_sender.start()

    package_receiver.join()
    confirmation_sender.join()


def save_file(arquivo, sliding_window):
    print("Saving file")
    filename = str(arquivo.file_name).split("/")[-1]
    filename = "output/" + filename

    print("salvando pacote num")
    with open(filename, "wb") as out:
        for i, pacote in enumerate(sliding_window.all_packages):
            print(i, ",", end="")
            out.write(pacote)


def handle_client(control_channel, server, address):
    print(f"New address connected: {address}")

    data_channel = open_data_channel(0, server)
    data_channel.settimeout(.5)

    greet_client(control_channel, data_channel)
    arquivo, sliding_window = receive_info_file(control_channel)
    receive_file(control_channel, data_channel, sliding_window)
    save_file(arquivo, sliding_window)

    for _ in range(10):
        try:
            control_channel.send(MSG_TYPE["FIM"])
        except:
            continue
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
        new_thread = Thread(target=handle_client, args=(new_tcp_conn, server, new_client_addr))
        new_thread.start()
        print(f"Active Connections: {activeCount() - 1}")


if __name__ == "__main__":
    main()
