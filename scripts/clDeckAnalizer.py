import pandas as pd

class CLDeckRegulationUpdater:
    def get(self,df:pd.DataFrame):
        # 同名扱いのカードはこのフラグで吸収
        df['hakase'] = False
        df['boss'] = False

        df_modified = df.copy()
        df_modified = df_modified[df_modified['card_type'] == 'トレーナーズ']
        df_modified = df_modified[df_modified['regulation'] != '-']
        df_modified.loc[df_modified['name'].str.contains('博士の研究'),'hakase'] = True
        df_modified.loc[df_modified['name'].str.contains('ボスの指令'),'boss'] = True
        df_modified = df_modified.sort_values(by=['regulation'], ascending=[True])

        df_temp = df_modified[~df_modified.duplicated(keep='last', subset=['name'])]
        # この時点で df_temp には名前が同じカードはない

        # 同名カードのレギュレーションを最後のレギュレーションで上書き
        for index, row in df_temp.iterrows():
            df_modified.loc[df_modified['name'] == row['name'], 'regulation'] = row['regulation']

        # 博士の研究を含むカード
        df_temp = df_modified[df_modified['hakase'] == True]
        df_temp = df_temp[~df_temp.duplicated(keep='last', subset=['hakase'])]
        for index, row in df_temp.iterrows():
            df_modified.loc[(df_modified['hakase'] == True), 'regulation'] = row['regulation']

        # ボスの指令を含むカード
        df_temp = df_modified[df_modified['boss'] == True]
        df_temp = df_temp[~df_temp.duplicated(keep='last', subset=['boss'])]
        for index, row in df_temp.iterrows():
            df_modified.loc[(df_modified['boss'] == True), 'regulation'] = row['regulation']

        # 更新
        df.update(df_modified)
        df = df.drop(columns={'hakase','boss'})

        return df

class CLDeckDummyCardProvider:
    def get(self, cl_deck: pd.DataFrame, card_list: pd.DataFrame):
        cl_deck['card_id'] = cl_deck['card_id'].astype(str)
        card_list['official_id'] = card_list['official_id'].astype(str)

        print('最初の件数:'+str(len(cl_deck)))
        #print(cl_deck.columns.values)

        app_card_id = card_list['official_id'].to_list()
        result = cl_deck['card_id'].apply(lambda x: any(char in x for char in app_card_id))
        noneDf = cl_deck[~result]
        print('除外件数:'+str(len(noneDf)))
        #print(noneDf.columns.values)

        # 重複はなくす
        # ポケモンは完全にレギュ落ちするのでダミーを生成しない
        nameListDf = card_list[card_list['card_type'] != 'ポケモン']
        nameListDf = nameListDf[nameListDf.duplicated(['name'], keep='last') == False]
        dummyDf = pd.merge(noneDf, nameListDf, left_on='card_name', right_on='name')
        print('ダミー件数:'+str(len(dummyDf)))

        print('----------')
        test = []
        l1 = noneDf['card_id'].to_list()
        l2 = dummyDf['card_id'].to_list()
        for i1 in l1:
            if i1 not in l2:
                test.append(i1)
        print(test)
        print('----------')
        #print(dummyDf.columns.values)

        result = cl_deck['card_id'].apply(lambda x: any(char in x for char in app_card_id))
        findDf = cl_deck[result]
        print('該当件数:'+str(len(findDf)))
        #print(findDf.columns.values)

        unionDf = pd.merge(findDf, card_list, left_on='card_id', right_on='official_id')
        unDup = unionDf[unionDf.duplicated(subset=['card_id', 'card_name', 'count', 'deck_id', 'event_id', 'player_id'],keep='last') == False]
        print('結合後の該当件数:'+str(len(unDup)))
        #print(unDup.columns.values)

        df = unDup.append(dummyDf, ignore_index=True)
        print('最終件数:'+str(len(df)))
        #print(df.columns.values)
        return df

class CLDeckListProvider:

    # デッキIDリスト生成
    def _getDeckIDList(self,df):
        dup = df[['deck_id']]
        unDup = dup[dup.duplicated(keep='last') == False]
        return unDup['deck_id'].to_list()

    # 指定したデッキIDの採用カードと枚数の一覧を生成する
    def _getDeckRecipe(self,df,deck_id):
        df = df[df['deck_id'] == deck_id]

        df.loc[df['card_type'] == 'ポケモン', 'card_type'] = 'P'
        df.loc[(df['card_type'] == 'トレーナーズ') & (df['sub_type'] == 'グッズ'), 'card_type'] = 'G' #Goods
        df.loc[(df['card_type'] == 'トレーナーズ') & (df['sub_type'] == 'サポート'), 'card_type'] = 'S' #Suport
        df.loc[(df['card_type'] == 'トレーナーズ') & (df['sub_type'] == 'ポケモンのどうぐ'), 'card_type'] = 'T' #Tool
        df.loc[(df['card_type'] == 'トレーナーズ') & (df['sub_type'] == 'スタジアム'), 'card_type'] = 'D' # staDium
        df.loc[df['card_type'] == 'エネルギー', 'card_type'] = 'E'
        
        df = df.fillna({'regulation': ''})
        df = df.fillna({'official_id': ''})
        dup = df[['master_id', 'card_id', 'card_type', 'name', 'regulation', 'official_id', 'count']]
        unDup = dup[dup.duplicated(subset=['card_id', 'count'], keep='last') == False]
        return unDup.to_dict(orient='records')

    def get(self,df):
        temp = {}
        l = self._getDeckIDList(df)
        for id in l:
            temp[id] = {
                'items' : self._getDeckRecipe(df,id)
            }
        return temp

class CLDeckAnalizer:
    reject_deck_id = []

    # カード使用時のランキング
    def getCardRank(self,df):
        df['date'] = df['date']+' 00:00:00'
        dup = df[['date', 'card_id', 'deck_id','rank']]
        unDup = dup[dup.duplicated(keep='last') == False]
        dfMin = unDup.groupby(['date','card_id','deck_id'], as_index=False).min()
        print(dfMin.sort_values(by=['card_id','date','rank'], ascending=[False,False,True]))

    # デッキ数
    def getDeckCount(self,df):
        dup = df[['event_id', 'player_id', 'deck_id']]
        unDup = dup[dup.duplicated(keep='last') == False]
        unDup = unDup.drop(columns={'event_id'})
        unDup = unDup.drop(columns={'player_id'})
        resDf = unDup.groupby(['deck_id'], as_index=False).size()
        return len(resDf)

    # カード採用数
    def getCardIdRow(self,df):
        dup = df[['event_id', 'player_id', 'card_id', 'count']]
        unDup = dup[dup.duplicated(keep='last') == False]
        unDup = unDup.drop(columns={'event_id'})
        unDup = unDup.drop(columns={'player_id'})
        unDup['card_id_rows'] = 1
        resDf = unDup.groupby(['card_id'], as_index=False).sum().sort_values(by=['card_id_rows'], ascending=[False])
        return resDf

    def getNewDfFromDeckID(self,BaseDf,filterDf):
        target_chars = filterDf['deck_id'].to_list()
        result = BaseDf['deck_id'].apply(lambda x: any(char in x for char in target_chars))
        return BaseDf[result]

    def getNewDfFromDeckIDNotIn(self,BaseDf,filterDf):
        target_chars = filterDf['deck_id'].to_list()
        result = BaseDf['deck_id'].apply(lambda x: any(char in x for char in target_chars))
        return BaseDf[~result]

    def getDeckInfo(self,df):
        if len(df) == 0:
            return {'count': 0, 'deck_id': []}
        #df['date'] = df['date'].dt.strftime("%Y/%m/%d %H:%M:%S")
        df = df.fillna({'sponsorship': ''})
        dup = df[['datetime', 'event_id', 'event_name', 'sponsorship', 'player_id', 'player_name','deck_id','rank']]
        unDup = dup[dup.duplicated(keep='last') == False].sort_values(by=['rank'], ascending=[True])
        return {'count': len(unDup),
                'deck_info':unDup.to_dict(orient='records')}

    def addDeckType(self,df,deck_type):
        #df['date'] = df['date'].dt.strftime("%Y/%m/%d %H:%M:%S")
        df['deck_type'] = deck_type
        df = df.fillna({'sponsorship': ''})
        dup = df[['datetime', 'event_id', 'deck_type', 'event_name', 'sponsorship', 'player_id', 'player_name','deck_id','rank']]
        unDup = dup[dup.duplicated(keep='last') == False].sort_values(by=['rank'], ascending=[True])
        return unDup
    
    def getDeckIDList(self,df):
        if len(df) == 0:
            return []
        df = df[df['deck_id'].duplicated(keep='last') == False]
        return df['deck_id'].to_list()

    # ミュウ
    def getMyuVMAX(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ミュウVMAX') & (df['move1'] == 'クロスフュージョン')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # レジ
    def getReji(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジギガス') & (df['ability'] == 'こだいのえいち')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジアイス') & (df['move1'] == 'レジゲート')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)


    # ロトム ROTOMUVSTAR
    def getRotomu(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ロトムVSTAR') & (df['move1'] == 'スクラップパルス') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ギラティナ
    def getGirateinaVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ギラティナVSTAR') & (df['move1'] == 'ロストインパクト') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジドラゴVSTAR') & (df['move1'] == 'りゅうむそう')]
        newDf = self.getNewDfFromDeckIDNotIn(df,filterDf)
        return (newDf)

    # レジドラゴVSTAR
    def getRejidoragoVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジドラゴVSTAR') & (df['move1'] == 'りゅうむそう')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジドラゴV') & (df['move1'] == 'てんのさけび')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ヒスイヌメルゴン
    def getHisuinumerugonVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ヒスイヌメルゴンVSTAR') & (df['move1'] == 'アイアンローリング') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # パルキア（キュレムなし）
    def getParukiaVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'オリジンパルキアVSTAR') & (df['move1'] == 'あくうのうねり') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュレムVMAX') & (df['ability'] == 'はくぎんせかい')]
        newDf = self.getNewDfFromDeckIDNotIn(df,filterDf)
        return (newDf)

    # キュレム（パルキアなし）
    def getKixyremu(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュレムVMAX') & (df['ability'] == 'はくぎんせかい')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'オリジンパルキアVSTAR') & (df['move1'] == 'あくうのうねり')]
        newDf = self.getNewDfFromDeckIDNotIn(df,filterDf)
        return (newDf)

    # パルキアキュレム kixyuremu
    def getParukiaKixyremu(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'オリジンパルキアVSTAR') & (df['move1'] == 'あくうのうねり')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュレムVMAX') & (df['ability'] == 'はくぎんせかい') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ディアルガ ORIJINDEIARUGAVSTAR
    def getDeiaruga(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'オリジンディアルガVSTAR') & (df['move1'] == 'メタルブラスト')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス/ピカチュウ ARUSEUSU/Jixyurarudon
    def getAruPika(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'そらをとぶピカチュウVMAX') & (df['move1'] == 'ダイバルーン')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス/うらこうさく ARUSEUSU/
    def getAruUra(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ジメレオン') & (df['ability'] == 'うらこうさく')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス ARUSEUSU
    def getAruseusu(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # イベルタル IBERUTARU
    def getIberutaruControl(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df

        filterDf = df[(df['name'] == 'イベルタル') & (df['move1'] == 'はかいのさけび')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df

        id_List = []

        filterDf2 = df[(df['name'] == 'カビゴン') & (df['ability'] == 'とおせんぼ')]
        df2 = self.getNewDfFromDeckID(df,filterDf2)
        l = self.getDeckIDList(df2)
        if len(l): id_List.extend(l)

        filterDf2 = df[(df['name'] == 'モルペコ') & (df['move1'] == 'いちゃもん')]
        df2 = self.getNewDfFromDeckID(df,filterDf2)
        l = self.getDeckIDList(df2)
        if len(l): id_List.extend(l)

        filterDf2 = df[(df['name'] == 'アブリボン') & (df['move1'] == 'トリックステップ')]
        df2 = self.getNewDfFromDeckID(df,filterDf2)
        l = self.getDeckIDList(df2)
        if len(l): id_List.extend(l)

        filterDf2 = df[(df['name'] == 'ミルタンク') & (df['ability'] == 'ミラクルボディ')]
        df2 = self.getNewDfFromDeckID(df,filterDf2)
        l = self.getDeckIDList(df2)
        if len(l): id_List.extend(l)

        result = df['deck_id'].apply(lambda x: any(char in x for char in id_List))
        newDf = df[result]
        return (newDf)

    '''
    # フリーザー/うらこうさく FURIZA/
    def getFurizaUra(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'フリーザー') & (df['move2'] == 'ワイルドフリーズ')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ジメレオン') & (df['ability'] == 'うらこうさく')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)
    '''

    # うらこうさく
    def getUrakou(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'インテレオン') & (df['ability'] == 'うらこうさく')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ジメレオン') & (df['ability'] == 'うらこうさく')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # エレキガノン REJIEREKIVMAX/KUWAGANONV
    def getErekiganon(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'クワガノンV') & (df['move1'] == 'パラライズボルト')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'レジエレキVMAX') & (df['ability'] == 'トランジスタ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ダイナ/ブラッキー MUGENDAINAV/BURAKKIVMAX
    def getDainaBurakki(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ムゲンダイナVMAX') & (df['ability'] == 'ムゲンゾーン')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ブラッキーVMAX') & (df['ability'] == 'ダークシグナル')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ドガス/ダイナ GARARUMATADOGASU/MUGENDAINAV
    def getDogasuDaina(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ムゲンダイナVMAX') & (df['ability'] == 'ムゲンゾーン') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ガラルマタドガス') & (df['ability'] == 'かがくへんかガス')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ドガス/バット GARARUMATADOGASU/KUROBATTOVMAX
    def getDogasuBatto(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'クロバットVMAX') & (df['move1'] == 'ステルスポイズン') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ガラルマタドガス') & (df['ability'] == 'かがくへんかガス')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ドガス GARARUMATADOGASU
    def getDogasu(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ガラルマタドガス') & (df['ability'] == 'かがくへんかガス')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ゾロアーク zoroaku
    def getZoroaku(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ゾロアーク') & (df['ability'] == 'げんえいへんげ') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ゾロア')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ルギア
    def getRugiaVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ルギアVSTAR') & (df['ability'] == 'アッセンブルスター') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス/ジュラルドン ARUSEUSU/Jixyurarudon
    def getAruJixyura(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ジュラルドンVMAX') & (df['ability'] == 'まてんろう') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ハピナス/ミルタンク HAPINASU/MIRUTANKU
    def getHapiMiru(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ハピナスV') & (df['ability'] == 'しぜんかいふく') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ミルタンク') & (df['ability'] == 'ミラクルボディ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    '''
    # ミュウツー/アルセウス MYUUTSUVUNION/MIRUTANKU
    def getMyuutsuAru(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ミュウツーV-UNION') & (df['ability'] == 'フォトンバリア')]
        if len(df) == 0: return df
        df = self.getNewDfFromDeckID(df,filterDf)
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)
    '''

    # ミュウツー MYUUTSUVUNION
    def getMyuutsuVunion(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ミュウツーV-UNION') & (df['ability'] == 'フォトンバリア')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ルナ/ソル RUNATON/SORUROKKU
    def getRunaSoru(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ソルロック') & (df['ability'] == 'サンエナジー') & (df['count'] >= 1)]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ルナトーン') & (df['move1'] == 'サイクルドロー')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # こくばバドレックスVMAX
    def getKokuba(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'こくばバドレックスVMAX') & (df['ability'] == 'めいかいのとびら') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # はくばバドレックスVMAX
    def getHakuba(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'はくばバドレックスVMAX') & (df['move2'] == 'ダイランス') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ロストバレットBox
    def getLostZoneBox(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ウッウ') & (df['ability'] == 'ロストプロバイド')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュワワー') & (df['ability'] == 'はなえらび')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ロストジュラルドン Lost/Jixyurarudon
    def getLostJixyura(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ジュラルドンVMAX') & (df['ability'] == 'まてんろう')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュワワー') & (df['ability'] == 'はなえらび')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ヒスイゾロアーク HISUIZOROAKUVSTAR
    def getHisuiZoroaku(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ヒスイゾロアークVSTAR') & (df['move1'] == 'のろいをきざむ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ゲンガー') & (df['ability'] == 'ならくのうらもん')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アイアント AIANTO
    def getAianto(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'アイアント') & (df['move2'] == 'くいあらす')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'のろいのスコップ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ダークライ ブロロローム
    def getDarkraiBuroro(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ダークライVSTAR') & (df['ability'] == 'スターアビス')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ブロロローム') & (df['ability'] == 'ランブルエンジン')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ミライドンex
    def getMiraidon(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ミライドンex') & (df['ability'] == 'タンデムユニット')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # サーナイトex
    def getSirnight(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'サーナイトex') & (df['ability'] == 'サイコエンブレイス')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # パフュートンex
    def getPerfuton(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'パフュートンex') & (df['move1'] == 'きょうらんのかおり')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # その他
    def getOthers(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        newDf = df[~result]
        return (newDf)

    def ResetRejectList(self):
        self.reject_deck_id = []

    def addRejectList(self,df):
        print(len(self.reject_deck_id))
        l=self.getDeckIDList(df)
        if len(l): self.reject_deck_id.extend(l)

    def getDeckList(self,df):
        self.ResetRejectList()

        myu = self.addDeckType(self.getMyuVMAX(df),'myu_vmax')
        self.addRejectList(myu)
        
        rugia = self.addDeckType(self.getRugiaVSTAR(df),'rugia_vstar')
        self.addRejectList(rugia)
        
        giratina = self.addDeckType(self.getGirateinaVSTAR(df),'girateina_vstar')
        self.addRejectList(giratina)

        darkraiburoro = self.addDeckType(self.getDarkraiBuroro(df),'darkrai_buroro')
        self.addRejectList(darkraiburoro)

        miraidon = self.addDeckType(self.getMiraidon(df),'miraidon')
        self.addRejectList(miraidon)

        sirnight = self.addDeckType(self.getSirnight(df),'sirnight')
        self.addRejectList(sirnight) 

        rejidorago = self.addDeckType(self.getRejidoragoVSTAR(df),'rejidorago_vstar')
        self.addRejectList(rejidorago)
        
        numerugon = self.addDeckType(self.getHisuinumerugonVSTAR(df),'hisui_numerugon_vstar')
        self.addRejectList(numerugon)
        
        aruJixyura = self.addDeckType(self.getAruJixyura(df),'aru_jixyura')
        self.addRejectList(aruJixyura)

        reji = self.addDeckType(self.getReji(df),'reji')
        self.addRejectList(reji)

        kokuba = self.addDeckType(self.getKokuba(df),'kokuba')
        self.addRejectList(kokuba)
        
        hakuba = self.addDeckType(self.getHakuba(df),'hakuba')
        self.addRejectList(hakuba)
        
        parukia = self.addDeckType(self.getParukiaVSTAR(df),'parukia')
        self.addRejectList(parukia)
        
        kixyremu = self.addDeckType(self.getKixyremu(df),'kixyremu')
        self.addRejectList(kixyremu)
        
        parukiaKixyremu = self.addDeckType(self.getParukiaKixyremu(df),'parukia_kixyremu')
        self.addRejectList(parukiaKixyremu)

        deiaruga = self.addDeckType(self.getDeiaruga(df),'deiaruga')
        self.addRejectList(deiaruga)
        
        lostzonebox = self.addDeckType(self.getLostZoneBox(df),'lostzone_box')
        self.addRejectList(lostzonebox)

        lostjixyura = self.addDeckType(self.getLostJixyura(df),'lost_jixyura')
        self.addRejectList(lostjixyura)
        
        hapimiru = self.addDeckType(self.getHapiMiru(df),'hapi_miru')
        self.addRejectList(hapimiru)

        arupika = self.addDeckType(self.getAruPika(df),'aru_pika')
        self.addRejectList(arupika)
        
        runasoru = self.addDeckType(self.getRunaSoru(df),'runa_soru')
        self.addRejectList(runasoru)

        zoroaku = self.addDeckType(self.getZoroaku(df),'zoroaku')
        self.addRejectList(zoroaku)

        #dogasudaina = self.addDeckType(self.getDogasuDaina(df),'dogasu_daina')
        #self.addRejectList(dogasudaina)

        #dogasubatto = self.addDeckType(self.getDogasuBatto(df),'dogasu_batto')
        #self.addRejectList(dogasubatto)
        
        erekiganon = self.addDeckType(self.getErekiganon(df),'ereki_ganon')
        self.addRejectList(erekiganon)

        myuutsu= self.addDeckType(self.getMyuutsuVunion(df),'myuutsu')
        self.addRejectList(myuutsu)
        
        iberutal = self.addDeckType(self.getIberutaruControl(df),'iberutal')
        self.addRejectList(iberutal)

        rotomu = self.addDeckType(self.getRotomu(df),'rotomu')
        self.addRejectList(rotomu)
        
        aruura = self.addDeckType(self.getAruUra(df),'aru_ura')
        self.addRejectList(aruura)
        
        aruseusu = self.addDeckType(self.getAruseusu(df),'aruseusu')
        self.addRejectList(aruseusu)
        
        urakou = self.addDeckType(self.getUrakou(df),'urakou')
        self.addRejectList(urakou)

        hisuizoroaku = self.addDeckType(self.getHisuiZoroaku(df),'hisui_zoroaku')
        self.addRejectList(hisuizoroaku)
        
        dainaburakki = self.addDeckType(self.getDainaBurakki(df),'daina_burakki')
        self.addRejectList(dainaburakki)
        
        aianto = self.addDeckType(self.getAianto(df),'aianto')
        self.addRejectList(aianto)
        
        #dogasu = self.addDeckType(self.getDogasu(df),'dogasu')
        #self.addRejectList(dogasu)    
        
        others = self.addDeckType(self.getOthers(df),'others')
        self.addRejectList(others)

        decks = pd.concat([
            myu,
            rugia,
            giratina,
            darkraiburoro,
            miraidon,
            sirnight,
            rejidorago,
            numerugon,
            aruJixyura,
            reji,
            kokuba,
            hakuba,
            parukia,
            kixyremu,
            parukiaKixyremu,
            deiaruga,
            lostzonebox,
            lostjixyura,
            hapimiru,
            arupika,
            runasoru,
            zoroaku,
            erekiganon,
            myuutsu,
            iberutal,
            rotomu,
            aruura,
            aruseusu,
            urakou,
            hisuizoroaku,
            dainaburakki,
            aianto,
            #dogasudaina, '23.01.23 廃止
            #dogasubatto, '23.01.23 廃止
            #dogasu, '23.01.23 廃止
            others
        ])

        return decks.to_dict(orient='records')


    def getDeckType(self,df):

        self.ResetRejectList()

        myu = self.getMyuVMAX(df)
        self.addRejectList(myu)
        
        rugia = self.getRugiaVSTAR(df)
        self.addRejectList(rugia)
        
        giratina = self.getGirateinaVSTAR(df)
        self.addRejectList(giratina)

        rejidorago = self.getRejidoragoVSTAR(df)
        self.addRejectList(rejidorago)
        
        numerugon = self.getHisuinumerugonVSTAR(df)
        self.addRejectList(numerugon)
        
        aruJixyura = self.getAruJixyura(df)
        self.addRejectList(aruJixyura)

        reji = self.getReji(df)
        self.addRejectList(reji)

        kokuba = self.getKokuba(df)
        self.addRejectList(kokuba)
        
        hakuba = self.getHakuba(df)
        self.addRejectList(hakuba)
        
        parukia = self.getParukiaVSTAR(df)
        self.addRejectList(parukia)
        
        kixyremu = self.getKixyremu(df)
        self.addRejectList(kixyremu)
        
        parukiaKixyremu = self.getParukiaKixyremu(df)
        self.addRejectList(parukiaKixyremu)

        deiaruga = self.getDeiaruga(df)
        self.addRejectList(deiaruga)
        
        lostzonebox = self.getLostZoneBox(df)
        self.addRejectList(lostzonebox)

        lostjixyura = self.getLostJixyura(df)
        self.addRejectList(lostjixyura)
        
        hapimiru = self.getHapiMiru(df)
        self.addRejectList(hapimiru)

        arupika = self.getAruPika(df)
        self.addRejectList(arupika)
        
        runasoru = self.getRunaSoru(df)
        self.addRejectList(runasoru)

        zoroaku = self.getZoroaku(df)
        self.addRejectList(zoroaku)

        dogasudaina = self.getDogasuDaina(df)
        self.addRejectList(dogasudaina)

        dogasubatto = self.getDogasuBatto(df)
        self.addRejectList(dogasubatto)
        
        erekiganon = self.getErekiganon(df)
        self.addRejectList(erekiganon)

        myuutsu= self.getMyuutsuVunion(df)
        self.addRejectList(myuutsu)
        
        iberutal = self.getIberutaruControl(df)
        self.addRejectList(iberutal)

        rotomu = self.getRotomu(df)
        self.addRejectList(rotomu)
        
        aruura = self.getAruUra(df)
        self.addRejectList(aruura)
        
        aruseusu = self.getAruseusu(df)
        self.addRejectList(aruseusu)
        
        urakou = self.getUrakou(df)
        self.addRejectList(urakou)

        hisuizoroaku = self.getHisuiZoroaku(df)
        self.addRejectList(hisuizoroaku)
        
        dainaburakki = self.getDainaBurakki(df)
        self.addRejectList(dainaburakki)
        
        aianto = self.getAianto(df)
        self.addRejectList(aianto)
        
        dogasu = self.getDogasu(df)
        self.addRejectList(dogasu)
        
        others = self.getOthers(df)
        self.addRejectList(others)

        return {
            'myu_vmax': self.getDeckInfo(myu),
            'rugia_vstar': self.getDeckInfo(rugia),
            'girateina_vstar': self.getDeckInfo(giratina),
            'rejidorago_vstar': self.getDeckInfo(rejidorago),
            'hisui_numerugon_vstar': self.getDeckInfo(numerugon),
            'aru_jixyura': self.getDeckInfo(aruJixyura),
            'reji': self.getDeckInfo(reji),
            'parukia': self.getDeckInfo(parukia),
            'kixyremu': self.getDeckInfo(kixyremu),
            'parukia_kixyremu': self.getDeckInfo(parukiaKixyremu),
            'kokuba': self.getDeckInfo(kokuba),
            'hakuba': self.getDeckInfo(hakuba),
            'lostzone_box': self.getDeckInfo(lostzonebox),
            'lost_jixyura': self.getDeckInfo(lostjixyura),
            'hapi_miru': self.getDeckInfo(hapimiru),
            'aru_pika': self.getDeckInfo(arupika),
            'runa_soru': self.getDeckInfo(runasoru),
            'zoroaku': self.getDeckInfo(zoroaku),
            'dogasu_daina': self.getDeckInfo(dogasudaina),
            'dogasu_batto': self.getDeckInfo(dogasubatto),
            'daina_burakki': self.getDeckInfo(dainaburakki),
            'ereki_ganon': self.getDeckInfo(erekiganon),
            'myuutsu': self.getDeckInfo(myuutsu),
            'iberutal': self.getDeckInfo(iberutal),
            'deiaruga': self.getDeckInfo(deiaruga),
            'rotomu': self.getDeckInfo(rotomu),
            'aru_ura': self.getDeckInfo(aruura),
            'aruseusu': self.getDeckInfo(aruseusu),
            'urakou': self.getDeckInfo(urakou),
            'hisui_zoroaku': self.getDeckInfo(hisuizoroaku),
            'aianto': self.getDeckInfo(aianto),
            'dogasu': self.getDeckInfo(dogasu),
            'others': self.getDeckInfo(others),
        }
