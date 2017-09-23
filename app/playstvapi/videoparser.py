from __future__ import unicode_literals

import datetime
import os
import pickle
import mongoDBtools
from operator import itemgetter
import numpy as np
import playstvapi.metrics as metrics
import requests
import pandas as pd
import youtube_dl
from YaDiskClient.YaDiskClient import YaDisk
import settings


class VideoStatsFilter:
    appid = settings.PlaysTvAppId
    appkey = settings.PlaysTvKey

    def __init__(self, game, videos_top_share_to_look, hashtags, startdate, resolution, request_type):
        self.hashtags = hashtags
        self.game = game
        self.type = request_type
        self.top = videos_top_share_to_look
        self.request_type = request_type
        gamedata = pickle.load(open(settings.GamesDataPath, 'rb+'))
        pickle.dump(gamedata, open(settings.GamesDataPath, 'wb+'))
        self.gameid = gamedata[game]['id']
        self.resolution = resolution
        self.start = startdate
        self.videos = []

    def turn_metatags_to_hashtags(self, metatags):
        hashtags = []
        for i in metatags:
            hashtag = self.parse_metatag(i)
            hashtags.append(hashtag)
        return hashtags

    def parse_metatag(self, metatag):
        parts = metatag["metatag"].split(":")
        return parts[-1]

    def hashtag_list_to_str(self, hashtag_list):
        request = " ".join(str(x) for x in hashtag_list)
        return request

    def rate_videos(self):
        calc = metrics.SimilarityMeasures()
        if self.request_type == 'trend':
            for i in self.videos:
                if 'hashtags' in i:
                    i['jaccard'] = calc.jaccard_similarity(self.hashtags, i['hashtags'])
                else:
                    i['jaccard'] = 0.0
        elif self.request_type == 'account':
            corpus = []
            request = self.hashtag_list_to_str(self.hashtags)
            corpus.append('{0} {1}'.format(request, self.game))
            for i in self.videos:
                if 'hashtags' in i:
                    request = self.hashtag_list_to_str(i['hashtags'])
                    corpus.append('{0} {1}'.format(request, self.game))
                else:
                    corpus.append(self.game)
            tf_idf = calc.tf_idf_cosine(corpus, 'vector')
            k = 1
            for j in self.videos:
                j['cosine'] = tf_idf[k]
                k += 1
        return

    def publish_video(self, id):
        stop = False
        while stop != True:
            try:
                fetcher = VideoFetcher('http://plays.tv/video/{0}'.format(self.videos[id]['id']), self.game, self.videos[id]['id'], self.videos[id]['hashtags'])
                fetcher.fetch_video()
                uploader = VideoUploader(self.game, fetcher.videoFolderPath)
                stop = True
            except BaseException:
                print("fail")
                id += 1
        return


    def select_video(self):
        if self.request_type == 'trend':
            param = 'jaccard'
        elif self.request_type == 'account':
            param = 'cosine'
        self.videos = sorted(self.videos, key=itemgetter(param), reverse=True)
        if self.videos[0][param] == 0.0:
            id = np.random.random_integers(int(len(self.videos)))
        else:
            id = 0
        print(self.videos[id]['hashtags'], self.videos[id]['jaccard'])
        self.videos[id]['hashtags'].append('playstv')
        self.videos[id]['hashtags'].append(self.videos[id]['author'])
        return id

    def parse_videos_data(self):
        stats = VideoStatsFetcher(self.game, self.top)
        stats = stats.get_vid_stats()
        if not (isinstance(stats, str)):
            for i in stats:
                if not (isinstance(i, str)):
                    if i['resolutions'] != None:
                        if not (os.path.exists('{0}/{1}/{2}'.format(settings.VideosDirPath, self.game, i['id']))) and (self.resolution in i['resolutions']):
                            video = {}
                            video['id'] = i['id']
                            video['author'] = i['author']['id']
                            video['time'] = datetime.datetime.fromtimestamp(int(i['upload_time'])).strftime('%Y-%m-%d %H:%M:%S')
                            video['hashtags'] = []
                            if 'metatags' in i:
                                video['hashtags'] = self.turn_metatags_to_hashtags(i['metatags'])
                            if 'hashtags' in i:
                                for hash in i['hashtags']:
                                    video['hashtags'].append(hash['tag'])
                            if video['hashtags'] != []:
                                self.videos.append(video)
        return


class VideoStatsFetcher:
    def __init__(self, game, top):
        db = mongoDBtools.MongoDbTools('GameStats')
        gamedata = db.read_videodata_from_db({"name": game})
        self.gameid = gamedata['id'][0]
        self.maxvideos = int(gamedata['videos'][0])
        self.videos = top
        self.appid = settings.PlaysTvAppId
        self.appkey = settings.PlaysTvKey

    def get_vid_stats_page(self, page, limit):
        call = 'https://api.plays.tv/data/v1/videos/search?appid={0}&appkey={1}' \
               '&gameId={2}&limit={3}&page={4}'.format(self.appid, self.appkey, self.gameid, limit, page)
        try:
            r = requests.get(call).json()
            r = r['content']['items']
        except Exception as e:
            r = 'the error is %s' % e
        return r

    def get_vid_stats(self):
        if int(self.videos) > int(self.maxvideos):
            self.videos = self.maxvideos
        k = 1
        vids = 0
        data = []
        while vids < self.videos:
            vids += int(settings.PlaysTvLinesPerPage / settings.PlaysTvLinesPerVid)
            get_vids = self.get_vid_stats_page(k, settings.PlaysTvLinesPerPage)
            if get_vids == []:
                break
            if k == 1:
                data = get_vids
            else:
                data += get_vids
            k += 1
        return 


class VideoUploader:
    Ylogin = settings.Ylogin
    Ypassword = settings.Ypassword

    def __init__(self, game, videofolder):
        self.game = game
        self.videofolder = videofolder
        self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.pathtovids = settings.VideosDirPath

    def upload_yandex_disk(self):
        disk = YaDisk(self.Ylogin, self.Ypassword)
        disk.mkdir('Videos/{0}/{1}'.format(self.game, self.timestamp))
        disk.upload('{0}/{1}/{2}/video.mp4'.format(self.pathtovids, self.game, self.videofolder),
                    'Videos/{0}/{1}/video.mp4'.format(self.game, self.timestamp))
        disk.upload('{0}/{1}/{2}/hashtags.txt'.format(self.pathtovids, self.game, self.videofolder),
                    'Videos/{0}/{1}/hashtags.txt'.format(self.game, self.timestamp))
        disk.upload('{0}/{1}/{2}/link_to_original.txt'.format(self.pathtovids, self.game, self.videofolder),
                    'Videos/{0}/{1}/link_to_original.txt'.format(self.game, self.timestamp))
        return


class VideoFetcher:
    def __init__(self, uri, game, videoid, hashtags):
        self.uri = uri
        self.game = game
        self.id = videoid
        self.hashtags = hashtags

    def fetch_video(self):
        print(self.uri)
        ydl_opts = {
            'format': 'best',
            'preferredcodec': 'mp3',
            'outtmpl': '{0}/{1}/{2}/video.mp4'.format(settings.VideosDirPath, self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        self.videoFolderPath = '{0}/{1}/{2}/'.format(settings.VideosDirPath, self.game, self.id)
        myFilePath = os.path.join(self.videoFolderPath, 'hashtags.txt')
        linkFilePath = os.path.join(self.videoFolderPath, 'link_to_original.txt')

        utf_hashtags = []
        for i in self.hashtags:
            i = '#{0}'.format(i)
            utf_hashtags.append(i.encode('utf-8'))
        np.savetxt(myFilePath, ["%s" % utf_hashtags], fmt='%s')
        with open(linkFilePath, "w") as text_file:
            text_file.write(self.uri)
        return











