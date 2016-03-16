import json
import time
import random
import logging
import datetime
import argparse
from os import linesep
from sys import stderr
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

if __name__ == '__main__':
    times = {}
    last = ''
    parser = argparse.ArgumentParser()
    parser.add_argument('config',
                        help='Config file (default: config.json)',
                        default='config.json',
                        nargs='?')
    args = parser.parse_args()
    data = {}
    try:
        with open(args.config, 'r') as fp:
            data = json.load(fp)
    except Exception as e:
        stderr.write('Error Reading Config: ' + str(e) + linesep)
        exit(1)
    logging.basicConfig(**data['logging'])
    OFFSET = random.randint(int(data['randomoffset']) * -1,
                            int(data['randomoffset']))  # Calculates Offset for login time
    while True:
        try:
            with open(args.config, 'r') as fp:
                data = json.load(fp)
        except Exception as e:
            logging.error('JSON: %s', str(e))
        now = datetime.datetime.now() + datetime.timedelta(minutes=OFFSET)  # Gets current date and applies offset
        if now.strftime('%Y-%m-%d') not in data['vacations'] \
                and now.strftime('%A') in data['workdays'] \
                and now.strftime('%H:%M') in data['times'] \
                and now.strftime('%H:%M') != last:
            driver = webdriver.Firefox()
            driver.get("https://ezlmappdc1f.adp.com/ezLaborManagerNet/Login/Login.aspx")  # Goes to Client Login page
            if ' - Client Login' in driver.title:
                logging.debug('Logging into client')
                elem = driver.find_element_by_id('txtClientName')
                elem.send_keys(data['clientname'])
                elem.send_keys(Keys.ENTER)
            if ' - Login' in driver.title:
                elem = driver.find_element_by_xpath('//*[@id="lblClientName"]')
                logging.debug('Client: %s', elem.text)
                logging.debug('Logging into user')
                elem = driver.find_element_by_id('txtUserID')
                elem.send_keys(data['username'])
                elem = driver.find_element_by_id('txtPassword')
                elem.send_keys(data['password'])
                elem.send_keys(Keys.ENTER)
                if 'Home' in driver.title:
                    elem = driver.find_element_by_xpath('//*[@id="lblName"]')
                    logging.debug('User: %s', elem.text)
                    if data['times'][now.strftime('%H:%M')] == 'in':
                        try:
                            elem = driver.find_element_by_class_name('btnClockIn_1')
                            elem.click()
                            logging.info('ClockIn: OK')
                        except Exception as e:
                            logging.error('ClockIn: %s', str(e))
                    elif data['times'][now.strftime('%H:%M')] == 'out':
                        try:
                            elem = driver.find_element_by_class_name('btnClockOut_1')
                            elem.click()
                            logging.info('ClockOut: OK')
                        except Exception as e:
                            logging.error('ClockOut: %s', str(e))
                    else:
                        logging.warning('No Command Set')
                    OFFSET = random.randint(int(data['randomoffset']) * -1,
                                            int(data['randomoffset']))
                    last = now.strftime('%H:%M')
                else:
                    logging.error('Login: %s', 'Could not login to user')
            else:
                logging.error('ClientLogin: %s', 'Could not login to client')
            driver.close()
        time.sleep(5)
