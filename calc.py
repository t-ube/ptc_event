import socket
import glob
import pandas as pd
from pathlib import Path
import os
import json
import datetime
from scripts import jst

# 1ヶ月のカード採用数
def getCardIdRow(df):
    '''
    dupID = df[['card_id']]
    dupID['card_id_rows'] = 1
    print(dupID.groupby(['card_id'], as_index=False).sum().sort_values(by=['card_id_rows'], ascending=[False]))
    '''
    dup = df[['event_id', 'player_id', 'card_id', 'count']]
    unDup = dup[dup.duplicated(keep='last') == False]
    unDup = unDup.drop(columns={'event_id'})
    unDup = unDup.drop(columns={'player_id'})
    unDup['card_id_rows'] = 1
    resDf = unDup.groupby(['card_id'], as_index=False).sum().sort_values(by=['card_id_rows'], ascending=[False])
    return resDf

# カード使用時のランキング
def getCardRank(df):
    df['date'] = df['date']+' 00:00:00'
    dup = df[['date', 'card_id', 'deck_id','rank']]
    unDup = dup[dup.duplicated(keep='last') == False]
    dfMin = unDup.groupby(['date','card_id','deck_id'], as_index=False).min()
    print(dfMin.sort_values(by=['card_id','date','rank'], ascending=[False,False,True]))

# デッキ数
def getDeckCount(df):
    dup = df[['event_id', 'player_id', 'deck_id']]
    unDup = dup[dup.duplicated(keep='last') == False]
    unDup = unDup.drop(columns={'event_id'})
    unDup = unDup.drop(columns={'player_id'})
    resDf = unDup.groupby(['deck_id'], as_index=False).size()
    return len(resDf)

ip = socket.gethostbyname(socket.gethostname())
print(ip)

currentDT = jst.now()
print(currentDT)

Path('./dist').mkdir(parents=True, exist_ok=True)

data_list = []
files = glob.glob("./data/cl/*.csv")
for file in files:
    df = pd.read_csv(file)
    data_list.append(df)

df = pd.concat(data_list, axis=0, sort=True)

print(getDeckCount(df))

#print(df)

# 重複するものを削除しない

# 採用率/全体
#getCardIdRow(df)

# ランク
#getCardRank(df)

baseDT = datetime.datetime(*currentDT.timetuple()[:3])
baseDT = baseDT + datetime.timedelta(days=1)
dateList = pd.date_range(
    baseDT - datetime.timedelta(days=7*7),
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

    writeData['items'].append({
        'index': index,
        'deck_count': getDeckCount(dfA),
        'begindate': begindate.strftime('%Y-%m-%d %H:%M:%S'),
        'enddate' : enddate.strftime('%Y-%m-%d %H:%M:%S'),
        'data': getCardIdRow(dfA).to_dict(orient='records')
    })

with open('./dist/cl.json', 'w') as f:
    json.dump(writeData, f, indent=4)

'''
# 採用枚数/デッキ
df['date'] = df['date']+' 00:00:00'
dup = df[['date', 'event_id', 'player_id', 'card_id', 'count']]
unDup = dup[dup.duplicated(keep='last') == False]
unDup = unDup.drop(columns={'event_id','player_id'})
unDup['card_id_rows'] = 1
dfSum = unDup.groupby(['date','card_id'], as_index=False).sum()
#print(dfSum.sort_values(by=['date','card_id'], ascending=[False,False]))
'''

'''
dup = df[['event_id', 'player_id', 'card_id']]
unDup = dup[dup.duplicated(keep='last') == False]
unDup = unDup.drop(columns={'event_id'})
unDup = unDup.drop(columns={'player_id'})
unDup['count'] = 1
print(unDup.groupby(['card_id']).sum().sort_values(by=['count'], ascending=[False]))

'''

