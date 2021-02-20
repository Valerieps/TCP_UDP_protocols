import socket
import argparse

parser = argparse.ArgumentParser(description='Servidor')
parser.add_argument('ip', type=str)
parser.add_argument('port', type=int)
# parser.add_argument('source_file', type=open)
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
    # envia HELLO (1) - Controle
    socket.send(b' 1')

    # Recebe CONNECTION  (2) - Controle
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)

    # Envia INFO FILE (3) - Controle
    msg_type = b' 3'

    file_name = b'arquivo.txt'
    file_name += b' ' * (15 - len(file_name))

    file_size = b'10'
    file_size += b' ' * (8 - len(file_size))

    info_file = msg_type + file_name +  file_size
    socket.send(info_file)

    # recebe OK (4) - Controle
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


def send_file():
    # Envia FILE (6) - Dados
    msg_type = b' 6'

    sequence_num = b'0'
    sequence_num += b' ' * (4 - len(sequence_num))
    payload_size = b'10'
    payload_size += b' ' * (2 - len(payload_size))
    file = b'0123456789'
    packed_file = msg_type + sequence_num + payload_size + file

    socket.send(packed_file)

    # Envia ACK(7) - Controle
    rcv = socket.recv(3)
    print(rcv)


def close_connection():
    send_data(b' 2', DISCONNECT_MSG)

if __name__ == "__main__":
    print("Greeting server")
    greet_server()

    print("Sending File")
    send_file()
    #
    # print("Disconnecting")
    # close_connection()



    # msg_length = len(message)
    # # o server  ler aenas essa qd de bytes
    # send_length = str(msg_length).encode(FORMAT)
    # send_length += b' ' * (HEADER - len(send_length))
    # send_length = bytes('5'.encode(FORMAT))
    # socket.send(send_length)