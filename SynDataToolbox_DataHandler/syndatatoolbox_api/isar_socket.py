import time  # <--- CORREZIONE: Aggiunto l'import mancante
import numpy as np
import socket
import sys


def highestPowerof2(n):
    if n < 1:
        return 0
    res = 1
    for i in range(8 * sys.getsizeof(n)):
        curr = 1 << i
        if curr > n:
            break
        res = curr
    return res


class IsarSocket:

    def __init__(self, port, address):
        # open connection, given address and port
        self.__MAX_COMMAND_LEN = 1000
        server_address = (address, port)

        # Impostiamo il timeout per la connessione (se fallisce) a 5 secondi.
        TIMEOUT_CONNESIONE = 5.0
        # Impostiamo il timeout per l'attesa dei DATI a 10 secondi (per i comandi VSET complessi).
        TIMEOUT_DATI = 10.0

        check = False
        while not check:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(TIMEOUT_CONNESIONE)  # Imposta un timeout per il tentativo di connessione
                self.sock.connect(server_address)

                # 🛑 CORREZIONE FONDAMENTALE: Imposta un timeout LUNGO per i dati.
                self.sock.settimeout(TIMEOUT_DATI)
                check = True
            except ConnectionRefusedError:
                # Attesa breve prima di riprovare a connettersi
                time.sleep(0.5)
            except socket.timeout:
                # Gestione del timeout durante il tentativo di connessione
                time.sleep(0.5)
            except Exception:
                # Gestione di altri errori di socket
                time.sleep(0.5)

            if check:
                # Uscita pulita dal loop while
                break

    def send_command(self, command):
        command = command.ljust(self.__MAX_COMMAND_LEN)[:self.__MAX_COMMAND_LEN]
        self.sock.sendall(bytes(command, 'utf8'))

    def rec_bytes(self, n_responses):
        # n is number of different responses are included into one server segment
        received_list = []
        for _ in range(n_responses):
            data = bytearray()
            raw = self.sock.recv(4)
            n_bytes = np.frombuffer(raw, dtype=np.uint32)[0]
            rec_size = highestPowerof2(max(n_bytes, 4096))
            while len(data) < n_bytes:
                packet = self.sock.recv(min(rec_size, n_bytes - len(data)))
                data.extend(packet)
            received_list.append(data)
        return received_list

    def rec_sensors_observations(self, buffer_size_list):
        # n is number of different responses are included into one server segment
        received_list = []
        for buffer in buffer_size_list:
            data = bytearray()
            n_bytes = buffer
            rec_size = highestPowerof2(max(n_bytes, 4096))
            while len(data) < n_bytes:
                packet = self.sock.recv(min(rec_size, n_bytes - len(data)))
                data.extend(packet)
            received_list.append(data)
        return received_list

    def close(self):
        self.sock.close()

    def rec_byte(self):
        # this method doesn't require "handshakeing" about buffer-receiver dimension, because will be return only one byte!
        packet = self.sock.recv(1)
        return packet