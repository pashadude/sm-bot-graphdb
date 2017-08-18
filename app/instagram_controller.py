import gspread
from oauth2client.service_account import ServiceAccountCredentials
import playstvapi.videoparser as vp


scope = ['https://spreadsheets.google.com/feeds']
credentials = ServiceAccountCredentials.from_json_keyfile_name('API Project-429c8ddbdd22.json', scope)
gc = gspread.authorize(credentials)
sht = gc.open('vids_data').sheet1
games = sht.col_values(2)
hashtags = sht.col_values(3)
indicator = sht.col_values(7)

for i in range(1, len(games)):
    if(indicator[i] == ''):
        break
    elif(indicator[i] == 'no'):
        if(hashtags[i] != 'FALSE'):
            hash_list = hashtags[i].split()
        else:
            hash_list = ['']
        game = games[i]
        #print(game)
        #print(hash_list)
        a = vp.VideoStatsFilter(game, 100000, hash_list, '2016-01-07 00:00:00', '720', 'account')
        a.parse_videos_data()
        a.rate_videos()
        a.select_video()
        break
        #sht.update_cell(i+1, 7, 'yes')