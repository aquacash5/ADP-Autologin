import json
import datetime
from sys import argv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

if len(argv) < 2:
    argv.append('config.json')
with open(argv[1]) as fp:
    data = json.load(fp)
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
assert 'Home' in driver.title
driver.find_element_by_link_text('My Benefits').click()
elems = driver.find_elements_by_xpath('//*[@id="tableCurrentHolidays"]/tbody/tr/td[1]')
for elem in elems:
    print(datetime.datetime.strptime(elem.text, '%A, %B %d, %Y').date())
