from get_chrome_driver import GetChromeDriver
from selenium import webdriver
import socket
import time
import pandas as pd
from scripts import seleniumDriverWrapper as wrap
from scripts import officialEvent

get_driver = GetChromeDriver()
get_driver.install()

wrapper = wrap.seleniumDriverWrapper()
wrapper.begin(webdriver)
offevent = officialEvent.officialEventCsvBot()
bot2 = officialEvent.officialEventRankerCsvBot()

ip = socket.gethostbyname(socket.gethostname())
print(ip)

start = time.time()
dataDir = './data/cl'

for i in range(6):
    offevent.download(wrapper, dataDir, i)

wrapper.end()

