import socket
import glob
import pandas as pd
from pathlib import Path
import os
import json
import datetime
from supabase import create_client, Client 
from scripts import jst
from scripts import supabaseUtil

def getCardData():
    data_list = []
    files = glob.glob("./data/card/*.csv")
    for file in files:
        dfCard = pd.read_csv(file,
        dtype={'master_id': str,'expansion': str,'cn': str,'card_type': str, 'sub_type': str,
        'name': str, 'ability': str , 'move1': str, 'move2': str, 'regulation': str,
        'official_id': str})
        data_list.append(dfCard)
    df2 = pd.concat(data_list, axis=0, ignore_index=True, sort=True)
    df2 = df2.drop(['expansion','cn','card_type','sub_type','name','ability','move1','move2','regulation','copyright'],axis='columns')
    df2 = df2.rename({'official_id':'card_id'},axis=1)
    return df2

def getDeckData(file:str, cardDf):
    df = pd.read_csv(file,
    dtype={'date': str,'datetime': str,'event_type': str,'event_name': str,'sponsorship': str,
    'address': str,'event_id': str,'event_url': str,'rank': int,'player_id': str,
    'player_name': str,'deck_id': str,'card_id': str,'card_name': str,'count': int})
    df = df.drop(['event_type','event_name','sponsorship','address','event_url','rank','player_name','card_name'],axis='columns')
    df = df.dropna(how='any')
    newDf = pd.merge(df, cardDf, left_on='card_id', right_on='card_id', how='inner')
    return newDf

def isFileData(file:str):
    print(file+':'+str(os.path.getsize(file))+' Byte')
    if os.path.getsize(file) > 200:
        return False
    return True

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

ip = socket.gethostbyname(socket.gethostname())
print(ip)

currentDT = jst.now()
print(currentDT)

Path('./dist').mkdir(parents=True, exist_ok=True)

cardDf = getCardData()
print(cardDf)

reader = supabaseUtil.eventIDIndexReader()
editor = supabaseUtil.batchEditor()
writer = supabaseUtil.batchWriter()

updated_id_list = reader.read(supabase)

data_list = []
files = glob.glob("./data/cl/*.csv")
for file in files:
    if isFileData(file) == True:
        event_id = os.path.splitext(os.path.basename(file))[0]
        if event_id in updated_id_list:
            print('skip:'+event_id)
            continue
        print('write:'+event_id)
        records = []
        df = getDeckData(file,cardDf)
        for index, row in df.iterrows():
            records.append(row)
        batch_results = editor.getEventDeckItem(records)
        result = writer.write(supabase, "event_deck_item", batch_results)
