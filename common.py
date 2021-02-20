
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
        self.file_size = None
        self.payload_size = None
        self.bin_file = None