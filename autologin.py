import json
import time
import datetime
from sys import argv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

times = {}
last = ''
if len(argv) < 2:
    argv.append('config.json')
while True:
    with open(argv[1]) as fp:
        data = json.load(fp)
    now = datetime.datetime.now()
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
        elem = driver.find_element_by_id('txtUserID')
        elem.send_keys(data['username'])
        elem = driver.find_element_by_id('txtPassword')
        elem.send_keys(data['password'])
        elem.send_keys(Keys.ENTER)
        if data['times'][now.strftime('%H:%M')] == 'in':
            elem = driver.find_element_by_class_name('btnClockIn_1')
            elem.click()
        elif data['times'][now.strftime('%H:%M')] == 'out':
            elem = driver.find_element_by_class_name('btnClockOut_1')
            elem.click()
        else:
            print('No Command Sent')
        last = now.strftime('%H:%M')
        driver.close()
    time.sleep(30)
