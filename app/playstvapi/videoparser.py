from __future__ import unicode_literals
from YaDiskClient.YaDiskClient import YaDisk
from operator import itemgetter
import youtube_dl
import requests
import json
import pickle
import os
import datetime
import numpy as np


class VideoStatsFilter():

    appid = 'DLKWBYCZNnBpDL4WOIRkCLFtDI7tO2RsOIGZ'
    appkey = '9exhOxYiMA4l0TH_utz5LAHH4Ii2ANbX'
    videos = []

    def __init__(self, game, videos_top_share_to_look, hashtags, startdate, resolution, request_type):
        self.hashtags = hashtags
        self.game = game
        self.type = request_type
        self.top = videos_top_share_to_look
        self.request_type = request_type
        gamedata = pickle.load(open('../../Data/games.pkl', 'rb+'))
        pickle.dump(gamedata, open('../../Data/games.pkl', 'wb+'))
        self.gameid = gamedata[game]['id']
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
        dic = pickle.load(open('../../Data/{}/metatags_hashtags.pkl'.format(self.game), 'rb+'))
        hashtags = []
        for i in metatags:
            hashtag = self.parse_metatag(i)
            hashtags.append(hashtag)
            if not(i['metatag'] in dic.keys()):
                dic[i['metatag']] = hashtag
        pickle.dump(dic, open('../../Data/{}/metatags_hashtags.pkl'.format(self.game), 'wb+'))
        return hashtags

    def parse_metatag(self, metatag):
        parts = metatag["metatag"].split(":")
        return parts[-1]

    def rate_videos(self):
        for i in self.videos:
            if 'hashtags' in i:
                i['jaccard'] = self.jaccard_similarity(self.hashtags, i['hashtags'])
            else:
                i['jaccard'] = 0.0
        return

    def select_video(self):
        self.videos = sorted(self.videos, key=itemgetter('jaccard'), reverse=True)
        #print(self.videos)
        VideoFetcher('http://plays.tv/video/{0}'.format(self.videos[0]['id']), self.game, self.videos[0]['id'], self.videos[0]['hashtags']).fetch_video()
        return

    def parse_videos_data(self):
        stats = VideoStatsFetcher(self.game, self.top, self.appid, self.appkey)
        stats = stats.get_vid_stats()
        for i in stats['content']['items']:
            #resolutions = i['resolutions'].split(",")
            if not(os.path.exists('../../Data/videos/{0}/{1}'.format(self.game, i['id']))) and (self.resolution in i['resolutions']):
                video = {}
                video['id'] = i['id']
                video['time'] = datetime.datetime.fromtimestamp(int(i['upload_time'])).strftime('%Y-%m-%d %H:%M:%S')
                if 'metatags' in i:
                    video['hashtags'] = self.turn_metatags_to_hashtags(i['metatags'])
                self.videos.append(video)
        return


class VideoStatsFetcher:
    def __init__(self, game, top, appid, appkey):
        gamedata = pickle.load(open('../../Data/games.pkl', 'rb+'))
        pickle.dump(gamedata, open('../../Data/games.pkl', 'wb+'))
        self.gameid = gamedata[game]['id']
        self.maxvideos = int(gamedata[game]['videos'])
        self.videos = top
        self.appid = appid
        self.appkey = appkey

    def get_vid_stats(self):
        if int(self.videos) > int(self.maxvideos):
            self.videos = self.maxvideos
        call = 'https://api.plays.tv/data/v1/videos/search?appid={0}&appkey={1}' \
               '&gameId={2}&limit={3}&sort=trending'.format(self.appid, self.appkey, self.gameid, self.videos)
        r = requests.get(call)
        return json.loads(r.text)


class VideoFetcher:
    Ylogin = 'pavel.dudko2016@yandex.com'
    Ypassword = 'Zt2w47kH'

    def __init__(self, uri, game, videoid, hashtags):
        self.uri = uri
        self.game = game
        self.id = videoid
        self.hashtags = hashtags

    def fetch_video(self):
        ydl_opts = {
            'format': 'best',
            'preferredcodec': 'mp3',
            'outtmpl': '../../Data/videos/{0}/{1}/{1}.mp4'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        myFilePath = os.path.join('../../Data/videos/{0}/{1}/'.format(self.game, self.id), '{0}_hashtags.txt'.format(self.id))
        utf_hashtags = []
        for i in self.hashtags:
            i = '#{0}'.format(i)
            utf_hashtags.append(i.encode('utf-8'))
        np.savetxt(myFilePath, ["%s" % utf_hashtags], fmt='%s')
        disk = YaDisk(self.Ylogin, self.Ypassword)
        disk.mkdir('Videos/{0}/{1}'.format(self.game, self.id))
        disk.upload('../../Data/videos/{0}/{1}/{1}.mp4'.format(self.game, self.id), 'Videos/{0}/{1}/{1}.mp4'.format(self.game, self.id))
        disk.upload('../../Data/videos/{0}/{1}/{1}_hashtags.txt'.format(self.game, self.id), 'Videos/{0}/{1}/{1}_hashtags.txt'.format(self.game, self.id))
        return

a = VideoStatsFilter('League of Legends', 10000, ['ranked', 'sona', 'pentakill', 'ezreal'], '2015-01-07 00:00:00', '720', 'trend')
a.parse_videos_data()
a.rate_videos()
a.select_video()