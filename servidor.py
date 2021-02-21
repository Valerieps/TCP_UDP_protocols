import socket
import threading
import argparse
from common import MSG_TYPE, File


parser = argparse.ArgumentParser(description='Servidor')
parser.add_argument('port', type=int)
args = parser.parse_args()

PORT = args.port
HEADER = 64
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "ascii"
PAYLOAD_SIZE = 1000

# todo é aqui que muda pra udp
server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)


def greet_client(connection):
    # Recebe HELLO (1) - Controle
    hello = connection.recv(2)
    if hello != MSG_TYPE["HELLO"]:
        print("Wrong handshake")
        connection.close()

    # Envia CONNECTION  (2) - Controle
    connection.send(MSG_TYPE["CONNECTION"])


def receive_info_file(connection):
    # Recebe INFO FILE (3) - Controle
    file = File()

    info_file_byte = connection.recv(26)
    msg_type = info_file_byte[:2]
    file_name = info_file_byte[2:17].decode(FORMAT).strip()
    file_size = info_file_byte[17:].decode(FORMAT).strip()

    file.file_name = str(file_name).strip()
    file.file_size = file_size

    # Envia OK (4) - Controle
    connection.send(MSG_TYPE["OK"])
    return file


def receive_file(connection, arquivo):
    file_size = int(arquivo.file_size)
    qnts_pacotes = file_size // PAYLOAD_SIZE
    if qnts_pacotes * PAYLOAD_SIZE < file_size:
        qnts_pacotes += 1

    pacotes = [None for i in range(qnts_pacotes)]

    for i in range(qnts_pacotes):
        # Recebe FILE (6) - Dados
        packed_file = connection.recv(PAYLOAD_SIZE + 10)
        msg_type = packed_file[:2]
        sequence_num = int(packed_file[2:6])
        payload_size = packed_file[6:8]
        arquivo.payload_size = payload_size
        payload = packed_file[8:]
        if payload:
            pacotes[sequence_num] = payload

        # Envia ACK(7) - Controle
        connection.send(MSG_TYPE["ACK"])

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


def handle_client(connection, address):
    print(f"New address: {address}")
    greet_client(connection)
    file = receive_info_file(connection)
    receive_file(connection, file)
    save_file(file)
    end_connection(connection)


def main():
    server.listen()
    print(f"Waiting connections in {SERVER}")

    while True:
        new_conn, new_addr = server.accept()  # a new client is trying to connect
        new_thread = threading.Thread(target=handle_client, args=(new_conn, new_addr))
        new_thread.start()
        print(f"Active Connections: {threading.activeCount() - 1}")  # less 1 because the star function is a thread


if __name__ == "__main__":
    main()
