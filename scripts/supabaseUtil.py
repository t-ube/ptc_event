import os
import httpx
import numpy as np
import postgrest
import datetime
import pandas as pd
from supabase import create_client, Client 

# 一括処理用
class batchEditor:
    # event_deck_item 用の情報を生成する
    def getEventDeckItem(self,records):
        items = []
        if len(records) <= 0:
            return items
        for item in records:
            batch_item = {
                "master_id": item['master_id'],
                "date": item['date'],
                "event_id": item['event_id'],
                "deck_id": item['deck_id'],
                "player_id": item['player_id'],
                "datetime": item['datetime']+'+09',
                "count": item['count']
            }
            items.append(batch_item)
        return items

# 一括書き込み用
class batchWriter:
    def write(self, supabase:Client, table_name:str, batch_item):
        if len(batch_item) <= 0:
            return True
        try:
            supabase.table(table_name).upsert(batch_item).execute()
            return True
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except httpx.WriteTimeout as e:
            print("httpx.WriteTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
            print('Begin error data')
            print(batch_item)
            print('End error data')
        return False

# event_id_index の読み取り用
class eventIDIndexReader:
    def read(self, supabase:Client):
        try:
            data = supabase.table("event_id_index").select("event_id_list").execute()
            if len(data.data) == 0:
                return []
            if data.data[0]['event_id_list'] == None:
                return []
            return data.data[0]['event_id_list'].split(',')
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []

# event_deck_item の削除用
class eventDeckItemCleaner:
    def limit(self,base_date):
        td = datetime.timedelta(days=8)
        limit_date = base_date - td
        return limit_date.strftime('%Y-%m-%d 00:00:00')

    def delete(self, supabase:Client, id_list, base_date):
        try:
            data = supabase.table("event_deck_item").delete().in_("master_id",id_list).lt("datetime",self.limit(base_date)).execute()
            return data.data
        except httpx.ReadTimeout as e:
            print("httpx.ReadTimeout")
            print(e.args)
        except postgrest.exceptions.APIError as e:
            print("postgrest.exceptions.APIError")
            print(e.args)
        return []
