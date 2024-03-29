import socket
import glob
import pandas as pd
from pathlib import Path
import os
import json
import datetime
import os
from supabase import create_client, Client 
from scripts import jst
from scripts import clDeckAnalizer
from scripts import supabaseUtil

def isFileData(file:str):
    print(file+':'+str(os.path.getsize(file))+' Byte')
    if os.path.getsize(file) > 200:
        return True
    return False

ip = socket.gethostbyname(socket.gethostname())
print(ip)

currentDT = jst.now()
print(currentDT)

Path('./dist').mkdir(parents=True, exist_ok=True)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(url, key)
supabase.postgrest.auth(service_key)

reader = supabaseUtil.eventIdUpdatedIndexReader()
updated_id_list = reader.read(supabase)

data_list = []
files = glob.glob("./data/cl/*.csv")
for file in files:
    if isFileData(file) == True:
        filename = os.path.basename(file)
        filename_without_extension = os.path.splitext(filename)[0]
        if filename_without_extension in updated_id_list:
            df = pd.read_csv(file,
            dtype={'date': str,'datetime': str,'event_type': str,'event_name': str,'sponsorship': str,
            'address': str,'event_id': str,'event_url': str,'rank': int,'player_id': str,
            'player_name': str,'deck_id': str,'card_id': str,'card_name': str,'count': int})
            data_list.append(df)

df = pd.concat(data_list, axis=0, ignore_index=True, sort=True)
#print(getDeckCount(df))
#df.to_csv('./dist/cl_all.csv')

data_list = []
files = glob.glob("./data/card/*.csv")
for file in files:
    dfCard = pd.read_csv(file,
    dtype={'master_id': str,'expansion': str,'cn': str,'card_type': str, 'sub_type': str,
    'name': str, 'ability': str , 'move1': str, 'move2': str, 'regulation': str,
    'official_id': str})
    data_list.append(dfCard)
df2 = pd.concat(data_list, axis=0, ignore_index=True, sort=True)

# ここで最新のレギュレーションに切り替え
reguUpdate = clDeckAnalizer.CLDeckRegulationUpdater()
df2 = reguUpdate.get(df2)
#df2.to_csv('./dist/cl_card.csv')

dummy = clDeckAnalizer.CLDeckDummyCardProvider()
df = dummy.get(df, df2)
#print(df)
#df[df['card_type']== 'ポケモン'].to_csv('./dist/cl_card_all.csv')

baseDT = datetime.datetime(*currentDT.timetuple()[:3])
baseDT = baseDT + datetime.timedelta(days=1)
dateList = pd.date_range(
    baseDT - datetime.timedelta(days=7*4),
    baseDT - datetime.timedelta(days=7),
    freq='7D')
df['date'] = df['date']+' 00:00:00'
df['date'] = pd.to_datetime(df['date'])
writeData = {'items': []}
for index, date in enumerate(reversed(dateList)):
    begindate = date
    enddate = date + datetime.timedelta(days=7)
    print(enddate)
    dfA = df[(df['date'] >= begindate) & (df['date'] < enddate)]
    dfB = dfA[(dfA['rank'] == 1)]

    analizer = clDeckAnalizer.CLDeckAnalizer()
    provider = clDeckAnalizer.CLDeckListProvider()
    writeData['items'].append({
        'index': index,
        'deck_count': analizer.getDeckCount(dfA),
        'begindate': begindate.strftime('%Y-%m-%d %H:%M:%S'),
        'enddate' : enddate.strftime('%Y-%m-%d %H:%M:%S'),
        'card_list': analizer.getCardIdRow(dfA).to_dict(orient='records'),
        'deck_list': analizer.getDeckList(dfA),
        'deck_recipe': provider.get(dfA)
    })

with open('./dist/cl.json', 'w', encoding='utf_8_sig') as f:
    json.dump(writeData, f, ensure_ascii=False)
    #json.dump(writeData, f, , ensure_ascii=False, indent=4)
