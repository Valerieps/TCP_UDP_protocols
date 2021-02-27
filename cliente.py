import socket
import argparse
import threading
import time
from common import MSG_TYPE, FORMAT, PAYLOAD_SIZE, WINDOW_SIZE
from common import File, SlidingWindow


def parse_args():
    parser = argparse.ArgumentParser(description='Servidor')
    parser.add_argument('ip', type=str)
    parser.add_argument('port', type=int)
    parser.add_argument('file', type=str)
    return parser.parse_args()


def filename_valid(filename):
    filename = filename.split("/")[-1]
    if len(filename) > 15:
        return False
    if len(filename.split(".")) != 2:
        return False
    if len(filename.split(".")[-1]) < 3:
        return False
    try:
        filename.encode(FORMAT)
        return True
    except:
        return False


def connect_to_control_channel(args):
    tcp_port = args.port
    server = args.ip
    tcp_addr = (server, tcp_port)

    try:
        control_channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_channel.connect(tcp_addr)
    except:
        control_channel = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        control_channel.connect(tcp_addr)
    return control_channel


def greet_server(control_channel):
    print("1. Greeting server")
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

    filename = filename.split("/")[-1]
    arquivo.file_name = bytearray(filename, FORMAT)
    arquivo.file_size = str(len(arquivo.binary_data)).encode(FORMAT)
    return arquivo


def make_sliding_window(arquivo):
    window = SlidingWindow()
    window.fit(arquivo, PAYLOAD_SIZE, FORMAT)
    window.initialize_window(WINDOW_SIZE)
    print("Fisrt window:", window.current_window)
    del arquivo
    return window


def send_file_info(control_channel, arquivo):
    print("2. Sending file info")
    msg_type = MSG_TYPE["INFO_FILE"]
    file_name = arquivo.file_name
    file_name += b' ' * (15 - len(file_name))
    file_size = arquivo.file_size
    file_size += b' ' * (8 - len(file_size))
    info_file = msg_type + file_name + file_size
    control_channel.send(info_file)

    # Recebe OK (4) - Controle
    _ = control_channel.recv(3).decode(FORMAT)


def send_file(sliding_window, data_channel, control_channel):
    print("3. Sending file data")
    condition = threading.Condition()
    control_channel.settimeout(0.5)

    sender = threading.Thread(target=sender_manager, args=(data_channel, sliding_window, condition))
    sender.start()

    print("Star listening to server responses")
    while True:
        if sliding_window.stop_sending:
            break
        try:
            msg = control_channel.recv(10)
            msg_type = msg[:2]
            with condition:
                if msg_type == MSG_TYPE["ACK"]:
                    sequence_number = msg[2:].decode(FORMAT).strip()
                    sequence_number = int(sequence_number)
                    sliding_window.confirm_receipt(sequence_number)
                    sliding_window.add_new_package_to_window()
                    condition.notify()
                elif msg_type == MSG_TYPE["RECEIVED EVERYTHING"]:
                    sliding_window.stop_sending = True
                    break
        except:
            continue

    sender.join()
    print("Finished sending file")


def sender_manager(data_channel, sliding_window, condition):
    print("3.2 Starting Sender")
    print("Falta enviar:", sliding_window.current_window)
    while not sliding_window.stop_sending:
        with condition:
            current_window = list(sliding_window.current_window)
        for to_send in current_window:
            print("Enviando pacote", to_send)
            with condition:
                s = threading.Thread(target=data_channel.sendto, args=(sliding_window.all_packages[to_send],
                                                                         data_channel.getpeername()))
            s.start()
            time.sleep(.1)
        # condition.wait()
    print("CLOSING Sender")


def main():
    args = parse_args()
    filename = args.file

    if not filename_valid(filename):
        print("Nome não permitido.")
        return

    control_channel = connect_to_control_channel(args)
    data_channel_port = greet_server(control_channel)
    data_channel = open_data_channel(args, data_channel_port)
    data_channel.settimeout(.5)
    arquivo = parse_file(filename)
    send_file_info(control_channel, arquivo)
    sliding_window = make_sliding_window(arquivo)
    send_file(sliding_window, data_channel, control_channel)

    for _ in range(10):
        try:
            fim = control_channel.recv(2)
            if fim == MSG_TYPE["FIM"]:
                print(fim)
                break
        except:
            continue
    print("All Done!")


if __name__ == "__main__":
    main()
