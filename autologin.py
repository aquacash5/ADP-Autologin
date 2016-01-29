import os
import sys
import json
import time
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

times = {}
last = ''
if len(sys.argv) < 2:
    sys.argv.append('config.json')
with open(sys.argv[1]) as fp:
    data = json.load(fp)
OFFSET = random.randint(int(data['randomoffset']) * -1, int(data['randomoffset']))
while True:
    with open(sys.argv[1]) as fp:
        data = json.load(fp)
    now = datetime.datetime.now() + datetime.timedelta(minutes=OFFSET)
    if now.strftime('%Y-%m-%d') not in data['vacations'] \
            and now.strftime('%A') in data['workdays'] \
            and now.strftime('%H:%M') in data['times'] \
            and now.strftime('%H:%M') != last:
        driver = webdriver.Firefox()
        driver.get("https://ezlmappdc1f.adp.com/ezLaborManagerNet/Login/Login.aspx")
        if 'Client Login' in driver.title:
            elem = driver.find_element_by_id('txtClientName')
            elem.send_keys(data['clientname'])
            elem.send_keys(Keys.ENTER)
        if 'Login' in driver.title:
            elem = driver.find_element_by_id('txtUserID')
            elem.send_keys(data['username'])
            elem = driver.find_element_by_id('txtPassword')
            elem.send_keys(data['password'])
            elem.send_keys(Keys.ENTER)
            if 'Home' in driver.title:
                if data['times'][now.strftime('%H:%M')] == 'in':
                    try:
                        elem = driver.find_element_by_class_name('btnClockIn_1')
                        elem.click()
                        sys.stdout.write('{0}\tClockIn\tSuccess\tOK'.format(now) + os.linesep)
                    except Exception as e:
                        sys.stderr.write('{0}\tClockIn\tError\t{1}'.format(now, str(e)))
                elif data['times'][now.strftime('%H:%M')] == 'out':
                    try:
                        elem = driver.find_element_by_class_name('btnClockOut_1')
                        elem.click()
                        sys.stdout.write('{0}\tClockOut\tSuccess\tOK'.format(now) + os.linesep)
                    except Exception as e:
                        sys.stderr.write('{0}\tClockOut\tError\t{1}'.format(now, str(e)) + os.linesep)
                else:
                    print('No Command Sent')
                OFFSET = random.randint(int(data['randomoffset']) * -1, int(data['randomoffset']))
                last = now.strftime('%H:%M')
            else:
                sys.stderr.write('{0}\tLogin\tError\tCould not login to ezLaborManager')
        else:
            sys.stderr.write('{0}\tClientLogin\tError\tCould not login to ezLaborManager'.format(now))
        driver.close()
    time.sleep(30)
