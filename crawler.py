from get_chrome_driver import GetChromeDriver
from selenium import webdriver
import socket
import time
import pandas as pd
import os
from supabase import create_client, Client 
from scripts import seleniumDriverWrapper as wrap
from scripts import officialEvent
from scripts import supabaseUtil

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

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

reader = supabaseUtil.eventIdUpdatedIndexReader()
updated_id_list = reader.read(supabase)

for i in range(6):
    offevent.download(wrapper, dataDir, updated_id_list, i)

wrapper.end()

