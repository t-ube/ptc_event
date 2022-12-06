import pandas as pd

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
        
        dup = df[['master_id', 'card_id', 'card_type', 'count']]
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
        dup = df[['event_id','player_id','deck_id','rank']]
        unDup = dup[dup.duplicated(keep='last') == False].sort_values(by=['rank'], ascending=[True])
        return {'count': len(unDup),
                'deck_id':unDup.to_dict(orient='records')}
    
    def getDeckIDList(self,df):
        if len(df) == 0:
            return []
        df = df[df['deck_id'].duplicated(keep='last') == False]
        return df['deck_id'].to_list()

    # ミュウ
    def getMyuVMAX(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ミュウVMAX') & (df['move1'] == 'クロスフュージョン')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # レジ
    def getReji(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'ロトムVSTAR') & (df['move1'] == 'スクラップパルス') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ギラティナ
    def getGirateinaVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ギラティナVSTAR') & (df['move1'] == 'ロストインパクト') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ヒスイヌメルゴン
    def getHisuinumerugonVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ヒスイヌメルゴンVSTAR') & (df['move1'] == 'アイアンローリング') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # パルキア（キュレムなし）
    def getParukiaVSTAR(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'オリジンディアルガVSTAR') & (df['move1'] == 'メタルブラスト')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス/ピカチュウ ARUSEUSU/Jixyurarudon
    def getAruPika(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'アルセウスVSTAR') & (df['move1'] == 'トリニティノヴァ')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # イベルタル IBERUTARU
    def getIberutaruControl(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'ガラルマタドガス') & (df['ability'] == 'かがくへんかガス')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ゾロアーク zoroaku
    def getZoroaku(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'ルギアVSTAR') & (df['ability'] == 'アッセンブルスター') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アルセウス/ジュラルドン ARUSEUSU/Jixyurarudon
    def getAruJixyura(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'ミュウツーV-UNION') & (df['ability'] == 'フォトンバリア')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ルナ/ソル RUNATON/SORUROKKU
    def getRunaSoru(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
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
        filterDf = df[(df['name'] == 'こくばバドレックスVMAX') & (df['ability'] == 'めいかいのとびら') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # はくばバドレックスVMAX
    def getHakuba(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'はくばバドレックスVMAX') & (df['move2'] == 'ダイランス') & (df['count'] >= 1)]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ロストゾーンBox
    def getLostZoneBox(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ウッウ') & (df['ability'] == 'ロストプロバイド')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'キュワワー') & (df['ability'] == 'はなえらび')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # ヒスイゾロアーク HISUIZOROAKUVSTAR
    def getHisuiZoroaku(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'ヒスイゾロアークVSTAR') & (df['move1'] == 'のろいをきざむ')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'ゲンガー') & (df['ability'] == 'ならくのうらもん')]
        newDf = self.getNewDfFromDeckID(df,filterDf)
        return (newDf)

    # アイアント AIANTO
    def getAianto(self,df):
        result = df['deck_id'].apply(lambda x: any(char in x for char in self.reject_deck_id))
        df = df[~result]
        filterDf = df[(df['name'] == 'アイアント') & (df['move2'] == 'くいあらす')]
        df = self.getNewDfFromDeckID(df,filterDf)
        if len(df) == 0: return df
        filterDf = df[(df['name'] == 'のろいのスコップ')]
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

    def getDeckType(self,df):

        self.ResetRejectList()

        myu = self.getMyuVMAX(df)
        self.addRejectList(myu)
        
        rugia = self.getRugiaVSTAR(df)
        self.addRejectList(rugia)
        
        giratina = self.getGirateinaVSTAR(df)
        self.addRejectList(giratina)
        
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
        
        lostzonebox = self.getLostZoneBox(df)
        self.addRejectList(lostzonebox)
        
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

        deiaruga = self.getDeiaruga(df)
        self.addRejectList(deiaruga)

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
            'hisui_numerugon_vstar': self.getDeckInfo(numerugon),
            'aru_jixyura': self.getDeckInfo(aruJixyura),
            'reji': self.getDeckInfo(reji),
            'parukia': self.getDeckInfo(parukia),
            'kixyremu': self.getDeckInfo(kixyremu),
            'parukia_kixyremu': self.getDeckInfo(parukiaKixyremu),
            'kokuba': self.getDeckInfo(kokuba),
            'hakuba': self.getDeckInfo(hakuba),
            'lostzone_box': self.getDeckInfo(lostzonebox),
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
