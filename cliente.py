import socket
import argparse
import threading
from common import MSG_TYPE, File, SlidingWindow
import time

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
    data_channel_port = int(server_answer[2:])
    return data_channel_port


def open_data_channel(args, data_channel_port):
    udp_addr = (args.ip, data_channel_port)
    data_channel = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data_channel.connect(udp_addr)
    return data_channel


def parse_file(filename):
    arquivo = File()
    arquivo.binary_data = open(filename, "rb").read()
    arquivo.file_name = bytearray(filename, FORMAT)
    arquivo.file_size = str(len(arquivo.binary_data)).encode(FORMAT)
    return arquivo


def send_file_info(control_channel, arquivo):
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


def make_sliding_window(arquivo):
    window = SlidingWindow()
    window.fit(arquivo, PAYLOAD_SIZE, FORMAT)
    window.initialize_window(WINDOW_SIZE)
    del arquivo
    return window


# ======== Sender functions ============
def sender_manager(data_channel, sliding_window, condition):
    print("Starting sender")

    # TODO retirar sleeps
    while not sliding_window.finished:
        s = threading.Thread(target=sender_task, args=(data_channel, sliding_window, condition))
        s.start()
        time.sleep(0.5)
        s.join()


def sender_task(data_channel, sliding_window, condition):
    with condition:
        if sliding_window.available_item:
            item = sliding_window.get_package_to_deal()
            package = sliding_window.headed_packages[item]
            _ = data_channel.sendto(package, data_channel.getpeername())
            print("Sending package", item)


# ======== Receiver functions ============
def confirmation_receiver_manager(control_channel, sliding_window, condition):
    print("Starting Confirmation Receiver")
    while not sliding_window.finished:
        c = threading.Thread(target=confirmation_receiver_task, args=(control_channel, sliding_window, condition))
        c.start()
        time.sleep(1.1)
        c.join()


def confirmation_receiver_task(control_channel, sliding_window, condition):
    rcv = control_channel.recv(7)
    msg_type = rcv[:2]
    sequence_number = int(rcv[2:].decode(FORMAT))

    with condition:
        if msg_type == MSG_TYPE["RECEIVED EVERYTHING"]:
            sliding_window.finished = True
            return

        if sliding_window.available_item:
            print("Server received package", sequence_number)
            sliding_window.confirm_receipt(sequence_number)
            sliding_window.add_new_package_to_window()


def send_file(sliding_window, data_channel, control_channel):
    condition = threading.Condition()
    sender = threading.Thread(target=sender_manager, args=(data_channel, sliding_window, condition))
    confirmation_receiver = threading.Thread(target=confirmation_receiver_manager,
                                    args=(control_channel, sliding_window, condition))
    sender.start()
    confirmation_receiver.start()

    sender.join()
    confirmation_receiver.join()


def main():
    args = parse_args()
    filename = args.file

    control_channel = connect_to_control_channel(args)
    data_channel_port = greet_server(control_channel)
    data_channel = open_data_channel(args, data_channel_port)
    arquivo = parse_file(filename)
    send_file_info(control_channel, arquivo)
    sliding_window = make_sliding_window(arquivo)
    send_file(sliding_window, data_channel, control_channel)
    print("All Done!")


if __name__ == "__main__":
    main()
