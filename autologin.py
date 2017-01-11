import argparse
import datetime
import json
import logging
import os
import random
import subprocess
import time
import zipfile
from os import linesep
from sys import stderr

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        url = '/'.join([
            'http://chromedriver.storage.googleapis.com',
            latest,
            'chromedriver_win32.zip'
        ])
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


def find_element_xpath(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def find_element_name(driver, name, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.NAME, name))
    )


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
        # Gets current date and applies offset
        now = datetime.datetime.now() + datetime.timedelta(minutes=OFFSET)
        if now.strftime('%Y-%m-%d') not in data['vacations'] \
                and now.strftime('%A') in data['workdays'] \
                and now.strftime('%H:%M') in data['times'] \
                and now.strftime('%H:%M') != last:
            if data['browser'] == 'CHROME':
                get_chrome_driver()
                driver = webdriver.Chrome('./chromedriver')
            else:
                driver = webdriver.Firefox()
            # Goes to Client Login page
            driver.get("https://workforcenow.adp.com/public/index.htm")
            if 'ADP' in driver.title:
                logging.debug('Logging into user')
                elem = find_element_name(driver, 'USER')
                elem.send_keys(data['username'])
                elem = find_element_name(driver, 'PASSWORD')
                elem.send_keys(data['password'])
                elem.send_keys(Keys.ENTER)
                if driver.find_element_by_id('Myself_navItem_label').is_displayed():
                    elem = find_element_xpath(
                        driver,
                        '//*[@id="mastheadGlobalOptions_label"]'
                    )
                    logging.debug('User: %s', elem.text)
                    driver.get(
                        "https://workforcenow.adp.com/portal/theme#/Myself_ttd_MyselfTabTimecardsAttendanceSchCategoryMyTimeEntry/MyselfTabTimecardsAttendanceSchCategoryMyTimeEntry"
                    )
                    find_element_name(driver, 'eZlmIFrame_iframe')
                    driver.switch_to.frame('eZlmIFrame_iframe')
                    if data['times'][now.strftime('%H:%M')] == 'in':
                        try:
                            elem = find_element_xpath(
                                driver,
                                '//*[@id="revit_form_ComboButton_0_button"]/span[1]'
                            )
                            elem.click()
                            logging.info('ClockIn: OK')
                        except Exception as e:
                            logging.error('ClockIn: %s', str(e))
                    elif data['times'][now.strftime('%H:%M')] == 'out':
                        try:
                            elem = find_element_xpath(
                                driver,
                                '//*[@id="revit_form_ComboButton_1_button"]/span[1]'
                            )
                            elem.click()
                            logging.info('ClockOut: OK')
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
