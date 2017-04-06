from __future__ import unicode_literals
import youtube_dl
import requests
import json
import pickle
import os
import datetime
import numpy as np

class VideoStatsFilter():
    def __init__(self, game, videos_top_share_to_look, hashtags, startdate, resolution, request_type):
        self.hashtags = hashtags
        self.game = game
        self.type = request_type
        self.top = videos_top_share_to_look
        self.request_type = request_type
        gamedata = pickle.load(open('../../Data/games.pkl', 'wb+'))
        self.gameid = gamedata[game]['id']
        self.appid = 'DLKWBYCZNnBpDL4WOIRkCLFtDI7tO2RsOIGZ'
        self.appkey = '9exhOxYiMA4l0TH_utz5LAHH4Ii2ANbX'
        self.resolution = resolution
        self.start = startdate

    def jaccard_similarity(self, x, y):
        intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
        union_cardinality = len(set.union(*[set(x), set(y)]))
        return intersection_cardinality / float(union_cardinality)


    def cosine_similarity(self, x, y):
        return


    def tf_idf_interpreter(self):
        return

    def turn_metatags_to_hashtags(self, metatags):
        dic = pickle.load(open('../../Data/{}/metatags_hashtags.pkl'.format(self.game),'wb+'))
        hashtags = []
        for i in metatags:
            hashtag = self.parse_metatag(i)
            hashtags.append(hashtag)
            if not(i in dic.keys()):
                dic[i] = hashtag
        pickle.dump(dic, open('../../Data/{}/metatags_hashtags.pkl'.format(self.game),'wb+'))
        return hashtags

    def parse_metatag(self, metatag):
        parts = metatag["metatag"].split(":")
        return parts[-1]

    def rate_videos(self):
        stats = VideoStatsFetcher(self.game, self.top, self.appid, self.appkey).get_vid_stats()
        videos = self.parse_videos_data(stats)
        for i in videos:
            if self.request_type == 'trend':
                i['jaccard'] = self.jaccard_similarity(self.hashtags, i['hashtags'])
            #elif self.request_type == 'audience':
        return

    def parse_videos_data(self, stats):
        videos = []
        video = {}
        for i in stats['items']:
            #resolutions = i['resolutions'].split(",")
            if not(os.path.exists('../../Data/videos/{0}/{1}/%(title)s'.format(self.game, i['id']))) and (self.resolution in i['resolutions']):
                video['id'] = i['id']
                video['time'] = datetime.datetime.fromtimestamp(int(i['upload_time'])).strftime('%Y-%m-%d %H:%M:%S')
                video['hashtags'] = self.turn_metatags_to_hashtags(i['metatags'])
                videos.append(video)
        return videos


class VideoStatsFetcher:
    def __init__(self, game, top, appid, appkey):
        gamedata = pickle.load(open('../../Data/games.pkl', 'wb+'))
        self.gameid = gamedata[game]['id']
        self.maxvideos = int(gamedata[game]['videos'])
        self.videos = int(gamedata[game]['videos'] * top)
        self.appid = appid
        self.appkey = appkey

    def get_vid_stats(self):
        page = np.random.random_integers(int(self.maxvideos//self.videos))
        call = 'https://api.plays.tv/data/v1/games?appid={0}&appkey={1}' \
               '&gameId={2}&limit={3}&page={4}&sort=popular&sortdir=asc'.format(self.appid, self.appkey, self.gameid, self.videos, page)
        r = requests.get(call)
        return json.loads(r.text)


class VideoFetcher:
    def __init__(self, uri, game, videoid):
        self.uri = uri
        self.game = game
        self.id = videoid

    def fetch_video(self):
        ydl_opts = {
            'format': 'best',
            'preferredcodec': 'mp3',
            'outtmpl': '../../Data/videos/{0}/{1}/%(title)s'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        return
