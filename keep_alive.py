#!/usr/bin/python
"""
This process should be run as a CRON job to make sure the
intended script stays running without interruptions.

Each time it is run, it checks if the intended process is currently
running. If it is not, then it restarts it and send an email notifying 
about this.
"""

import subprocess
import smtplib

def check_if_running(script):
    p = subprocess.Popen(['pgrep', '-fl', script], stdout=subprocess.PIPE)
    output, err = p.communicate()
    if len(output) > 0:
        return True
    else:
        return False

def restart_script(script):
    p = subprocess.Popen(['python',  script], stdout=subprocess.PIPE)
        
def send_mail():
    gmail_user = '<SENDER>@gmail.com'
    gmail_pwd = '<PASSWORD>'
    FROM = '<SENDER>@gmail.com'
    TO = ['<RECIPIENT>@gmail.com'] #must be a list
    TEXT = 'Script stopped. Script restarted'
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587) 
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, TEXT)
        server.close()
        print 'Successfully sent the mail'
    except:
        print 'Failed to send mail'

script = '/path/to/script/to/be/monitored/script.py'
running = check_if_running(script)
if not running:
    restart_script(script)
    send_mail()
