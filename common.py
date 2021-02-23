
MSG_TYPE = {
    "HELLO": b'1 ',
    "CONNECTION": b'2 ',
    "INFO_FILE": b'3 ',
    "OK": b'4 ',
    "FIM": b'5 ',
    "FILE": b'6 ',
    "ACK": b'7 ',
}


class File:
    def __init__(self):
        self.file_name = None
        self.file_size = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.total_packages = 0
        self.packages = None


    def get_total_packages(self, PAYLOAD_SIZE):
        total_de_pacotes = int(self.file_size) // PAYLOAD_SIZE
        if total_de_pacotes * PAYLOAD_SIZE < int(self.file_size):
            total_de_pacotes += 1
        self.total_packages = total_de_pacotes