import requests as r
import pandas as pd
import datetime as dt

class ChessAPI():
    def __init__(self,username):
        self.user = username
        
        self.base_url = 'https://api.chess.com/pub/player'

        self.opps = {}

    def all_archives(self):
        return self.__pull(f"https://api.chess.com/pub/player/{self.user}/games/archives")

    def game_archive(self,archive_url):
        '''
        this calls the game_archive url
        '''
        return self.__pull(archive_url)
         
    def __pull(self,url):
        '''
        requests library to pull the json 
        '''
        return r.get(url).json()
    
    def _get_result(self,results,color):
        '''
        returns the result of the match and the detail behind it
        '''
        res_string = results[color]['result']
        if res_string in ['checkmated','resigned','timeout','lose']:
            return 'loss' , res_string
        elif res_string in ['agreed','repetition']:
            return 'draw',res_string
        elif res_string == 'stalemate':
            return res_string,res_string
        elif res_string == 'win':
            return res_string,results['white' if color =='black' else 'black']['result']
        else:
            return res_string,None
        
    def _extract_data(self,api_obj):
        '''
        sets the values for the df
        
        looks in the api json response to determine the following columns
        
        color, opp (name), your result, your detailed result, current rating,
        opp current rating, the date the game concluded
        '''
        if api_obj['white']['username'] == self.user:
            color = 'white'
            result,result_detail = self._get_result(api_obj,'white')
            rating = api_obj['white']['rating']
            opp = api_obj['black']['username']
            opp_rating = api_obj['black']['rating']

        else:
            color = 'black'
            result, result_detail = self._get_result(api_obj,'black')
            rating = api_obj['black']['rating']
            opp = api_obj['white']['username']
            opp_rating = api_obj['white']['rating']
                
        return {'color': color,
                'opp': opp,
                'result': result,
                'result detail': result_detail,
                'current rating':rating,
                'opp current rating': opp_rating,
                'game-mode': api_obj['time_class'] + '-' + api_obj['time_control'],
                'rated':api_obj['rated'],
                'url':api_obj['url'],
                'date':dt.datetime.fromtimestamp(api_obj['end_time']).date()}
        
    def archive_grab(self):
        '''
        pulls all the data found in all archive pages
        '''
        self.data = []
        for page in self.all_archives()['archives']:
            self.data += self.game_archive(page)['games']
        
        self.df = pd.DataFrame()
        for x in self.data:
            self.df = self.df.append(pd.DataFrame.from_records([self._extract_data(x)]))
            
        self.df['date'] = pd.to_datetime(self.df['date'])
        
    def opp(self,opp_name):
        '''
        returns grouped data (date,result,result detail) between you and 
        a specific player
        '''
        opp_df = self.df.loc[self.df['opp'] == opp_name].copy()
        
        def group(df,cols):
            df = df.groupby(cols).count()[df.columns[0]]
            df.name = 'results'
            df = pd.DataFrame(df)
            df['pct'] = df/df.sum()
            return df 
        
        month = group(opp_df,
                      [pd.Index(opp_df['date']).year,
                       pd.Index(opp_df['date']).month,
                       'result','result detail'])

        month_simple = month.groupby(
                        [month.index.get_level_values(0),
                        month.index.get_level_values(1),
                        month.index.get_level_values(2)]
                        ).sum()['results']

        detail = month.groupby([month.index.get_level_values(2),
                                month.index.get_level_values(3)]
                               ).sum()
        
        results = detail.groupby(detail.index.get_level_values(0)
                                 ).sum()

        self.opps[opp_name] = {'raw':opp_df,
                               'detail':detail,
                               'results':results,
                               'month':month,
                               'month-s':month_simple
                               }

        return opp_df, detail, results, month, month_simple
