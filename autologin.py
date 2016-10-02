import os
import json
import time
import random
import logging
import zipfile
import datetime
import requests
import argparse
import subprocess
from os import linesep
from sys import stderr
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def get_chrome_driver():
    version = '0.0'
    if os.path.exists('./chromedriver.exe'):
        p = subprocess.Popen(['./chromedriver.exe', '--version'], stdout=subprocess.PIPE)
        p.wait()
        version = p.stdout.read().strip().decode("utf-8").split(' ')[1]
    response = requests.get('http://chromedriver.storage.googleapis.com/LATEST_RELEASE')
    latest = response.content.strip().decode("utf-8")
    if version < latest:
        try:
            os.remove('./chromedriver.exe')
        except Exception:
            pass
        url = '/'.join(['http://chromedriver.storage.googleapis.com', latest, 'chromedriver_win32.zip'])
        response = requests.get(url)
        try:
            with open('chromedriver.zip', 'wb') as zipper:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        zipper.write(chunk)
            with zipfile.ZipFile('chromedriver.zip') as zipper:
                zipper.extractall('.')
            logging.info('Downloaded ChromeDriver v%s', latest)
        finally:
            os.remove('chromedriver.zip')


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
    logging.info('Config Read Successfully')
    OFFSET = random.randint(int(data['randomoffset']) * -1,
                            int(data['randomoffset']))  # Calculates Offset for login time
    logging.info('Random Offset: %s', OFFSET)
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
            if data['browser'] == 'CHROME':
                get_chrome_driver()
                driver = webdriver.Chrome('./chromedriver')
            else:
                driver = webdriver.Firefox()
            driver.get("https://workforcenow.adp.com/public/index.htm")  # Goes to Client Login page
            # if 'ADP' in driver.title:
            # logging.debug('Logging into client')
            # elem = driver.find_element_by_id('txtClientName')
            # elem.send_keys(data['clientname'])
            # elem.send_keys(Keys.ENTER)
            if 'ADP' in driver.title:
                # elem = driver.find_element_by_xpath('//*[@id="lblClientName"]')
                # logging.debug('Client: %s', elem.text)
                logging.debug('Logging into user')
                elem = driver.find_element_by_name('USER')
                elem.send_keys(data['username'])
                elem = driver.find_element_by_name('PASSWORD')
                elem.send_keys(data['password'])
                elem.send_keys(Keys.ENTER)
                if driver.find_element_by_id('Myself_navItem_label').is_displayed():
                    elem = driver.find_element_by_xpath('//*[@id="mastheadGlobalOptions_label"]')
                    logging.debug('User: %s', elem.text)
                    # Going through drop-down menu selenium doesn't like clicking hidden elements
                    elem = driver.find_element_by_xpath('//*[@id="Myself_navItem"]')
                    elem.click()
                    elem = driver.find_element_by_xpath('//*[@id="revit_layout_TabContainer_1_tablist_dijit_layout_ContentPane_4"]/span[2]/span')
                    elem.click()
                    elem = driver.find_element_by_xpath('//*[@id="Myself_ttd_MyselfTabTimecardsAttendanceSchCategoryMyTimeEntry"]')
                    elem.click()
                    if data['times'][now.strftime('%H:%M')] == 'in':
                        try:
                            for _ in range(10):
                                elem = driver.find_element_by_xpath('//*[@id="revit_form_Button_1"]/input')
                                if elem:
                                    # elem.click()
                                    logging.info('ClockIn: OK')
                                    break
                                else:
                                    time.sleep(.5)
                        except Exception as e:
                            logging.error('ClockIn: %s', str(e))
                    elif data['times'][now.strftime('%H:%M')] == 'out':
                        try:
                            for _ in range(10):
                                elem = driver.find_element_by_xpath('//*[@id="revit_form_Button_0"]/input')
                                if elem:
                                    # elem.click()
                                    logging.info('ClockOut: OK')
                                    break
                                else:
                                    time.sleep(.5)
                        except Exception as e:
                            logging.error('ClockOut: %s', str(e))
                    else:
                        logging.warning('No Command Set')
                    OFFSET = random.randint(int(data['randomoffset']) * -1,
                                            int(data['randomoffset']))
                    logging.info('Random Offset: %s', OFFSET)
                    last = now.strftime('%H:%M')
                else:
                    logging.error('Login: %s', 'Could not login to user')
            else:
                logging.error('ClientLogin: %s', 'Could not login to client')
            driver.close()
        time.sleep(.01)
