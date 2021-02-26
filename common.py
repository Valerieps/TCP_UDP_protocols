
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
        self.headed_packages = None
        self.window_size = None
        self.window_full = None
        self.next_to_add = 0
        self.booked_all_packages = False
        self.finished = False
        self.current_window = set()
        self.available_item = None


    def fit(self, arquivo, payload_size, encode_format):
        self.get_total_packages(arquivo)
        self.payload_size = payload_size
        self.format = encode_format

        packages = self.break_in_chunks(arquivo)
        self.headed_packages = self.add_header(packages)

    def get_total_packages(self, arquivo):
        total_de_pacotes = int(arquivo.file_size) // self.payload_size
        if total_de_pacotes * self.payload_size < int(arquivo.file_size):
            total_de_pacotes += 1
        self.total_packages = total_de_pacotes

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
        """
        - o gerador de pacotes precisa de uma função que vê se rola add mais: add_new_package_to_send()
        - atributo finished_sending: quando tiver adicionado o ultimo pacote E o set esvaziar
        """

        self.window_size = window_size

        if self.window_size < self.total_packages:
            for pkg in range(self.window_size):
                self.current_window.add(pkg)
                self.next_to_add = len(self.window_size)
        else:
            for pkg in range(self.total_packages):
                self.current_window.add(pkg)
                self.booked_all_packages = True
        self.available_item = True
        self.window_full = True

    def get_package_to_deal(self):
        """Return a package to send without removing from window"""
        if self.available_item:
            item = self.current_window.pop()
            self.current_window.add(item)
            return item

    def confirm_receipt(self, sequence_number):
        self.current_window.remove(sequence_number)
        if len(self.current_window) == 0:
            self.available_item = False
            if self.booked_all_packages:
                self.finished = True

    def add_new_package_to_window(self):
        """Add a new package to window, if possible"""

        if self.booked_all_packages:
            return

        self.current_window.add(self.next_to_add)
        self.next_to_add += 1
        self.available_item = True
        if self.next_to_add == self.total_packages:
            self.booked_all_packages = True

