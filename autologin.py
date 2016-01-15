import json
import datetime
from sys import argv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

times = {}
if len(argv) < 2:
    argv.append('config.json')
while True:
    with open(argv[1]) as fp:
        data = json.load(fp)
    if False:
        driver = webdriver.Firefox()
        driver.get("https://ezlmappdc1f.adp.com/ezLaborManagerNet/Login/Login.aspx")
        try:
            assert 'Client Login' in driver.title
            elem = driver.find_element_by_id('txtClientName')
            elem.send_keys(data['clientname'])
            elem.send_keys(Keys.ENTER)
        except AssertionError:
            pass
        assert 'Login' in driver.title
        elem = driver.find_element_by_id('txtUserID')
        elem.send_keys(data['username'])
        elem = driver.find_element_by_id('txtPassword')
        elem.send_keys(data['password'])
        elem.send_keys(Keys.ENTER)
        if argv[1] == 'in':
            elem = driver.find_element_by_class_name('btnClockIn_1')
            elem.click()
        elif argv[1] == 'out':
            elem = driver.find_element_by_class_name('btnClockOut_1')
            elem.click()
        else:
            print('No Command Sent')
        driver.close()
