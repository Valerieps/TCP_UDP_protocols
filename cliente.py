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

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)

    send_length += b' ' * (HEADER - len(send_length))

    socket.send(send_length)
    socket.send(message)
    rcv = socket.recv(HEADER).decode(FORMAT)
    print(rcv)


if __name__ == "__main__":


    send("Opa!!")
    send("O porra")
    send(DISCONNECT_MSG)