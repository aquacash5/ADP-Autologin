import argparse
import datetime
import json
import logging
import os
import random
import subprocess
import time
import zipfile
from sys import stderr

import requests
import requests.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def get_chrome_driver():
    version = '0.0'
    if os.path.exists('./chromedriver.exe'):
        p = subprocess.Popen(
            ['./chromedriver.exe', '--version'], stdout=subprocess.PIPE)
        p.wait()
        version = p.stdout.read().strip().decode('utf-8').split(' ')[1]
    logging.debug('CHROME DRIVER VERSION: {}'.format(version))
    response = requests.get(
        'http://chromedriver.storage.googleapis.com/LATEST_RELEASE', timeout=5)
    latest = response.content.strip().decode('utf-8')
    logging.debug('LATEST CHROME DRIVER VERSION: {}'.format(latest))
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
        try:
            response = requests.get(url, timeout=5)
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
        except requests.exceptions.Timeout:
            pass


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
        print('Error Reading Config: {}'.format(e), file=stderr)
        exit(1)
    logging.basicConfig(**data['logging'])
    logging.info('Config Read Successfully')
    # Calculates Offset for login time
    OFFSET = random.randint(int(data['randomoffset']) * -1,
                            int(data['randomoffset']))
    logging.info('RANDOM OFFSET: %s', OFFSET)
    while True:
        try:
            with open(args.config, 'r') as fp:
                data = json.load(fp)
        except Exception:
            logging.exception('Reading JSON')
        # Gets current date and applies offset
        now = datetime.datetime.now() + datetime.timedelta(minutes=OFFSET)
        if now.strftime('%Y-%m-%d') not in data['vacations'] \
                and now.strftime('%A') in data['workdays'] \
                and now.strftime('%H:%M') in data['times'] \
                and now.strftime('%H:%M') != last:
            finished = False
            attempts = 0
            while not finished and attempts < 10:
                try:
                    if data['browser'] == 'CHROME':
                        try:
                            get_chrome_driver()
                        except Exception:
                            pass
                        driver = webdriver.Chrome('./chromedriver')
                    else:
                        driver = webdriver.Firefox()
                except Exception:
                    logging.exception('Initialize Driver')
                    continue
                try:
                    # Goes to Client Login page
                    driver.get('https://workforcenow.adp.com/public/index.htm')
                    if 'ADP' in driver.title:
                        logging.debug('Logging into user')
                        elem = find_element_name(driver, 'USER')
                        elem.send_keys(data['username'])
                        elem = find_element_name(driver, 'PASSWORD')
                        elem.send_keys(data['password'])
                        elem.send_keys(Keys.ENTER)
                        if driver.find_element_by_id(
                                'Myself_navItem_label').is_displayed():
                            elem = find_element_xpath(
                                driver,
                                '//*[@id="mastheadGlobalOptions_label"]'
                            )
                            logging.debug('USER: %s', elem.text)
                            driver.get(
                                'https://workforcenow.adp.com/portal/theme#'
                                '/Myself_ttd_MyselfTabTimecardsAttendanceSch'
                                'CategoryMyTimeEntry/MyselfTabTimecards'
                                'AttendanceSchCategoryMyTimeEntry'
                            )
                            find_element_name(driver, 'eZlmIFrame_iframe')
                            driver.switch_to.frame('eZlmIFrame_iframe')
                            if data['times'][now.strftime('%H:%M')] == 'in':
                                try:
                                    elem = find_element_xpath(
                                        driver,
                                        '//*[@id="revit_form_'
                                        'ComboButton_0_button"]/span[1]'
                                    )
                                    elem.click()
                                    logging.info('CLOCK IN: OK')
                                    finished = True
                                except Exception:
                                    logging.exception('CLOCK IN')
                            elif data['times'][now.strftime('%H:%M')] == 'out':
                                try:
                                    elem = find_element_xpath(
                                        driver,
                                        '//*[@id="revit_form_'
                                        'ComboButton_1_button"]/span[1]'
                                    )
                                    elem.click()
                                    logging.info('CLOCK OUT: OK')
                                    finished = True
                                except Exception:
                                    logging.exception('CLOCK OUT')
                            else:
                                logging.warning('No Command Set')
                                finished = True
                            OFFSET = random.randint(
                                int(data['randomoffset']) * -1,
                                int(data['randomoffset'])
                            )
                            logging.info('RANDOM OFFSET: %s', OFFSET)
                            last = now.strftime('%H:%M')
                        else:
                            logging.error('LOGIN: Could not login to user')
                    else:
                        logging.error(
                            'CLIENT LOGIN: Could not login to client')
                except Exception:
                    logging.exception('Auto Login Error')
                finally:
                    driver.close()
                time.sleep(2)
                attempts += 1
        time.sleep(.1)
