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

    # socket.send(b'0123456789')

    # recebe OK (4) - Controle


def send_data(type, msg):
    message = msg.encode(FORMAT)

    print("sending type")
    socket.send(type)
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)

    print("sending message")
    socket.send(message)
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)

def close_connection():
    send_data(b' 2', DISCONNECT_MSG)

if __name__ == "__main__":
    print("Greeting server")
    greet_server()

    # print("Sending message")
    # send_data(b' 1', 'Oi')
    #
    # print("Disconnecting")
    # close_connection()



    # msg_length = len(message)
    # # o server  ler aenas essa qd de bytes
    # send_length = str(msg_length).encode(FORMAT)
    # send_length += b' ' * (HEADER - len(send_length))
    # send_length = bytes('5'.encode(FORMAT))
    # socket.send(send_length)