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
import math
import collections


class VideoStatsFilter():

    appid = 'DLKWBYCZNnBpDL4WOIRkCLFtDI7tO2RsOIGZ'
    appkey = '9exhOxYiMA4l0TH_utz5LAHH4Ii2ANbX'
    videos = []

    def __init__(self, game, videos_top_share_to_look, hashtags, postdate, startdate, resolution, request_type):
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
        self.post = postdate

    def jaccard_similarity(self, x, y):
        intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
        union_cardinality = len(set.union(*[set(x), set(y)]))
        return intersection_cardinality / float(union_cardinality)

    def cosine_similarity(self, vector1, vector2):
        dot_product = sum(p * q for p, q in zip(vector1, vector2))
        magnitude = math.sqrt(sum([val ** 2 for val in vector1])) * math.sqrt(sum([val ** 2 for val in vector2]))
        if not magnitude:
            return 0
        return dot_product / magnitude

    def tf_idf_cosine(self):
        tf = np.matrix([],[])
        idf = np.matrix([],[])
        tf_idf = np.matrix([],[])
        original_tf_idf = []
        for i in self.hashtags:
            original_tf_idf[i] = math.log10(len(self.videos)/sum([1.0 for k in self.videos if i in k['hashtags']]))
        for j in self.videos:
            if 'hashtags' in j:
                for i in self.hashtags:
                    if i in j['hashtags']:
                        tf[j][i] = 1
                    else:
                        tf[j][i] = 0
                    idf[j][i] = math.log10(len(self.videos)/sum([1.0 for k in self.videos if i in k['hashtags']]))
                    tf_idf[j][i] = float(tf[j][i])*float(idf[j][i])
            else:
                j['cosine'] = 0.0
        for j in self.videos:
            if not('cosine' in j):
                j['cosine'] = self.cosine_similarity(original_tf_idf, tf_idf[j])
        return

    def turn_metatags_to_hashtags(self, metatags):
        if os.path.exists('../../Data/{}/metatags_hashtags.pkl'.format(self.game)):
            dic = pickle.load(open('../../Data/{}/metatags_hashtags.pkl'.format(self.game), 'rb+'))
        else:
            dic = {'':''}
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
        if self.request_type == 'trend':
            for i in self.videos:
                if 'hashtags' in i:
                    i['jaccard'] = self.jaccard_similarity(self.hashtags, i['hashtags'])
                else:
                    i['jaccard'] = 0.0
        elif self.request_type == 'account':
           self.tf_idf_cosine()
        return


    def select_video(self):
        if self.request_type == 'trend':
            param = 'jaccard'
        elif self.request_type == 'account':
            param = 'cosine'
        self.videos = sorted(self.videos, key=itemgetter(param), reverse=True)
        if self.videos[0][param] == 0.0:
            id = np.random.random_integers(int(len(self.videos)))
            self.videos[id]['hashtags'] = [self.game, 'videogames']
        else:
            id = 0
        VideoFetcher('http://plays.tv/video/{0}'.format(self.videos[id]['id']), self.game, self.videos[id]['id'], self.videos[id]['hashtags']).fetch_video()
        vids = pickle.load(open('../../Data/videos_parsed.pkl'.format(self.game), 'rb+'))
        vids.append(self.videos[id])
        pickle.dump(vids, open('../../Data/videos_parsed.pkl'.format(self.game), 'wb+'))
        return

    def parse_videos_data(self):
        stats = VideoStatsFetcher(self.game, self.top, self.appid, self.appkey)
        stats = stats.get_vid_stats()
        if not (os.path.exists('../../Data/videos/{0}/{1}')):
            vids = []
        else:
            vids =  pickle.load(open('../../Data/videos_parsed.pkl'.format(self.game), 'rb+'))

        for i in stats['content']['items']:
            #resolutions = i['resolutions'].split(",")

            if not(i[id] in vids.keys) and (self.resolution in i['resolutions']):
                video = {}
                video['id'] = i['id']
                video['time'] = datetime.datetime.fromtimestamp(int(i['upload_time'])).strftime('%Y-%m-%d %H:%M:%S')
                if 'metatags' in i:
                    video['hashtags'] = self.turn_metatags_to_hashtags(i['metatags'])
                    #print(video['hashtags'])
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
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.hashtags = hashtags

    def fetch_video(self):
        ydl_opts = {
            'format': 'best',
            'preferredcodec': 'mp3',
            'outtmpl': '../../Data/videos/{0}/{1}/video.mp4'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        myFilePath = os.path.join('../../Data/videos/{0}/{1}/'.format(self.game, self.id), 'hashtags.txt')
        utf_hashtags = []
        for i in self.hashtags:
            i = '#{0}'.format(i)
            utf_hashtags.append(i.encode('utf-8'))
        np.savetxt(myFilePath, ["%s" % utf_hashtags], fmt='%s')
        disk = YaDisk(self.Ylogin, self.Ypassword)
        disk.mkdir('Videos/{0}/{1}'.format(self.game, self.timestamp))
        disk.upload('../../Data/videos/{0}/{1}/video.mp4'.format(self.game, self.id), 'Videos/{0}/{1}/video.mp4'.format(self.game, self.timestamp))
        disk.upload('../../Data/videos/{0}/{1}/hashtags.txt'.format(self.game, self.id), 'Videos/{0}/{1}/hashtags.txt'.format(self.game, self.timestamp))
        return

a = VideoStatsFilter('League of Legends', 25000, ['lux','zed','soraka','graves','pentakill'], '2015-01-07 00:00:00', '720', 'trend')
#'For Honor', 10000, ['knight', 'duel', 'flawless', 'kill']
#'Overwatch', 10000, ['soldier76', 'ace', 'kill']
#'DOTA 2', 7000, ['drow ranger', 'phantomassassin', 'karthus', 'bristleback']
#'Battlefield 1', 10000, ['kill', 'germany']
#'FIFA 17', 5000, ['goal', 'barcelona']

a.parse_videos_data()
a.rate_videos()
a.select_video()
