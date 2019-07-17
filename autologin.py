import argparse
import datetime
import json
import logging
import os
import random
import subprocess
import time
import hashlib
import zipfile
from sys import stderr

import requests
import requests.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

CLOCK_IN_BUTTON = '/html/body/div/app/ng-component/redbox-container/div[6]/div[2]/div[2]/div/div/dashboard-container/div/espresso-dashboard/espresso-tile[1]/div/div[2]/ng-include/div/div/div/div/time-punch-tile/div/div/div/div[2]/button[1]'
CLOCK_OUT_BUTTON = '/html/body/div/app/ng-component/redbox-container/div[6]/div[2]/div[2]/div/div/dashboard-container/div/espresso-dashboard/espresso-tile[1]/div/div[2]/ng-include/div/div/div/div/time-punch-tile/div/div/div/div[2]/button[2]'

log = logging.getLogger('adp')
stream = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream.setFormatter(formatter)
log.addHandler(stream)


def get_chrome_driver():
    version = '0.0'
    if os.path.exists('./chromedriver.exe'):
        p = subprocess.Popen(
            ['./chromedriver.exe', '--version'], stdout=subprocess.PIPE)
        p.wait()
        version = p.stdout.read().strip().decode('utf-8').split(' ')[1]
    log.debug('CHROME DRIVER VERSION: {}'.format(version))
    response = requests.get(
        'http://chromedriver.storage.googleapis.com/LATEST_RELEASE', timeout=5)
    latest = response.content.strip().decode('utf-8')
    log.debug('LATEST CHROME DRIVER VERSION: {}'.format(latest))
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
                log.info('Downloaded ChromeDriver v%s', latest)
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


# noinspection PyProtectedMember
def log_level(string):
    return logging._nameToLevel.get(string, logging.INFO)


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


if __name__ == '__main__':
    times = {}
    last = ''
    parser = argparse.ArgumentParser()
    parser.add_argument('config',
                        help='Config file (default: config.json)',
                        default='config.json',
                        nargs='?')
    # noinspection PyProtectedMember
    parser.add_argument('-l', '--log-level',
                        help='Log Level ({}) [INFO]'.format(
                            ', '.join(logging._nameToLevel)),
                        type=log_level,
                        default=logging.INFO)
    args = parser.parse_args()
    log.setLevel(args.log_level)
    data = {}
    config_hash = ''
    try:
        with open(args.config, 'r') as fp:
            data = json.load(fp)
    except Exception as e:
        print('Error Reading Config: {}'.format(e), file=stderr)
        exit(1)
    log.debug('Initial Load Successful')
    # Calculates Offset for login time
    OFFSET = random.randint(int(data['randomoffset']) * -1,
                            int(data['randomoffset']))
    log.debug('RANDOM OFFSET: %s', OFFSET)
    while True:
        try:
            new_hash = md5(args.config)
            if config_hash != new_hash:
                with open(args.config, 'r') as fp:
                    data = json.load(fp)
                config_hash = new_hash
                log.info("New Config!")
                log.debug('CONFIG HASH:   {}'.format(config_hash))
                log.debug('RANDOM OFFSET: {}'.format(data['randomoffset']))
                log.debug('BROWSER:       {}'.format(data['browser']))
                log.debug('WORKDAYS:      {}'.format(data['workdays']))
                log.debug('VACATIONS:     {}'.format(data['vacations']))
                log.debug('TIMES:         {}'.format(data['times']))
                log.debug('USERNAME:      {}'.format(data['username']))
                log.debug('PASSWORD:      {}'.format(data['password']))
        except Exception:
            log.exception('Reading JSON')
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
                    log.exception('Initialize Driver')
                    continue
                try:
                    # Goes to Client Login page
                    driver.get('https://my.adp.com/static/redbox/login.html')
                    if 'ADP' in driver.title:
                        log.debug('Logging into user')
                        elem = find_element_xpath(driver, '//*[@id="user"]')
                        elem.send_keys(data['username'])
                        elem = find_element_xpath(driver, '//*[@id="password"]')
                        elem.send_keys(data['password'])
                        elem.send_keys(Keys.ENTER)
                        if find_element_xpath(driver, CLOCK_IN_BUTTON, 30).is_displayed():
                            if data['times'][now.strftime('%H:%M')] == 'in':
                                try:
                                    elem = find_element_xpath(driver, CLOCK_IN_BUTTON)
                                    elem.click()
                                    log.info('CLOCK IN: OK')
                                    finished = True
                                except Exception:
                                    log.exception('CLOCK IN')
                            elif data['times'][now.strftime('%H:%M')] == 'out':
                                try:
                                    elem = find_element_xpath(driver, CLOCK_OUT_BUTTON)
                                    elem.click()
                                    log.info('CLOCK OUT: OK')
                                    finished = True
                                except Exception:
                                    log.exception('CLOCK OUT')
                            else:
                                log.warning('No Command Set')
                                finished = True
                            OFFSET = random.randint(
                                int(data['randomoffset']) * -1,
                                int(data['randomoffset'])
                            )
                            log.debug('RANDOM OFFSET: %s', OFFSET)
                            last = now.strftime('%H:%M')
                        else:
                            log.error('LOGIN: Could not login to user')
                    else:
                        log.error('CLIENT LOGIN: Could not login to client')
                except Exception:
                    log.exception('Auto Login Error')
                finally:
                    driver.close()
                time.sleep(2)
                attempts += 1
        time.sleep(5)
