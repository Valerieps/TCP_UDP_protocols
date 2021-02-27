FORMAT = "ascii"
PAYLOAD_SIZE = 1000
WINDOW_SIZE = 5
MSG_TYPE = {
    "HELLO": b'1 ',
    "CONNECTION": b'2 ',
    "INFO_FILE": b'3 ',
    "OK": b'4 ',
    "FIM": b'5 ',
    "FILE": b'6 ',
    "ACK": b'7 ',
    "RECEIVED EVERYTHING": b'8 ',
}


class File:
    def __init__(self):
        self.file_name = None
        self.file_size = 0
        self.binary_data = None


class SlidingWindow:
    def __init__(self):
        self.payload_size = None
        self.format = None
        self.total_packages = None
        self.all_packages = []
        self.window_size = None
        self.window_full = None
        self.next_to_add = 0
        self.booked_all_packages = False
        self.stop_sending = False
        self.current_window = set()
        self.to_confirm = set()

    def fit(self, file, payload_size, encode_format):
        self.payload_size = payload_size
        self.get_total_packages(file)
        self.format = encode_format

        packages = self.break_in_chunks(file)
        self.all_packages = self.add_header(packages)

    def get_total_packages(self, arquivo):
        total_de_pacotes = int(arquivo.file_size) // self.payload_size
        if total_de_pacotes * self.payload_size < int(arquivo.file_size):
            total_de_pacotes += 1
        self.total_packages = total_de_pacotes
        print(f"{total_de_pacotes=}")

    def break_in_chunks(self, arquivo):
        pacotes = []
        start = None
        for idx in range(self.total_packages):
            start = idx * self.payload_size
            end = start + self.payload_size
            pacotes.append(arquivo.binary_data[start:end])
        pacotes.append(arquivo.binary_data[start:])
        return pacotes

    def add_header(self, packages):
        pacotes_com_header = []
        msg_type = MSG_TYPE["FILE"]

        for idx, pacote in enumerate(packages):
            idx = str(idx).encode(self.format)
            sequence_num = bytes(idx)
            sequence_num += b' ' * (4 - len(sequence_num))
            payload_size = b'11'  # todo descobrir o que é isso
            payload_size += b' ' * (2 - len(payload_size))
            packed_file = msg_type + sequence_num + payload_size + pacote
            pacotes_com_header.append(packed_file)
        return pacotes_com_header

    def initialize_window(self, window_size):
        self.window_size = window_size

        if self.window_size < self.total_packages:
            for pkg in range(self.window_size):
                self.current_window.add(pkg)
                self.next_to_add = self.window_size
        else:
            for pkg in range(self.total_packages):
                self.current_window.add(pkg)
                self.booked_all_packages = True
        self.available_item = True
        self.window_full = True
        print(f"{self.current_window=}")

    def confirm_receipt(self, sequence_number):
        print("Confirmando pacote", sequence_number)
        self.current_window.remove(sequence_number)

        if not self.current_window and self.booked_all_packages:
                self.stop_sending = True
        print(f"{self.current_window=}")

    def add_new_package_to_window(self):
        print("Tentando adicionar pacote na janela")

        if self.booked_all_packages:
            print("Já agendou todos")
            if not self.all_packages:
                self.stop_sending = True
            return

        self.current_window.add(self.next_to_add)
        print("Consegui adicionar o pacote", self.next_to_add)
        self.next_to_add += 1
        if self.next_to_add == self.total_packages:
            self.booked_all_packages = True
            if not self.all_packages:
                self.stop_sending

        print(f"{self.current_window=}")

