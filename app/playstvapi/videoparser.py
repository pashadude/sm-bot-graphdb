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
    def __init__(self, game, hashtags, request_type):
        self.hashtags = hashtags
        self.game = game
        self.request_type = request_type
        self.reply = "no similar video yet"
        self.db_game = mongoDBtools.MongoDbTools(self.game)

    def hashtag_list_to_str(self, hashtag_list):
        request = " ".join(str(x) for x in hashtag_list)
        return request

    def rate_videos(self):
        start = True
        for word in self.hashtags:
            if start == True:
                data = self.db_game.read_text_index_videodata_from_db("hashtags", '"' + (str(word)) + '"')
                if not isinstance(data, str) and not data.empty:
                    start = False
            elif start == False:
                datax = self.db_game.read_text_index_videodata_from_db("hashtags", '"' + (str(word)) + '"')
                if not isinstance(datax, str) and not datax.empty:
                    data = data.append(datax, ignore_index=True)
        #print(data)
        if not isinstance(data, str) and not data.empty:
            data = data[pd.notnull(data['id'])]
            data = data.drop_duplicates("id", "first")
            data = data.reset_index()
            self.data = data
            #print(data)
            calc = metrics.SimilarityMeasures()
            k = len(data)
            vid = 0
            num = 0
            num_id = ''
            tf_idf = -1
            if self.request_type == 'trend':
                while vid < k:
                    jac = calc.jaccard_similarity(data['hashtags'][vid], self.hashtags)
                    if num <= jac:
                        num = jac
                        num_id = data['id'][vid]
                    vid += 1
                #print(num_id)
                self.reply = num_id
                self.publish_video()

            elif self.request_type == 'account':
                corpus = []
                request = self.hashtag_list_to_str(self.hashtags)
                corpus.append('{0} {1}'.format(request, self.game))
                while vid < k:
                    request = self.hashtag_list_to_str(data['hashtags'][vid])
                    corpus.append('{0} {1}'.format(request, self.game))
                tf_idf = calc.tf_idf_cosine(corpus, 'vector')
                # need to fix
                self.reply = max(tf_idf)

    def publish_video(self):

        try:
            fetcher = VideoFetcher('http://plays.tv/video/{0}'.format(self.data.loc[self.reply, 'id']), self.game, self.data.loc[self.reply,'id'], self.data.loc[self.reply,'hashtags'])
            fetcher.fetch_video()
            uploader = VideoUploader(self.game, fetcher.videoFolderPath)
            uploader.upload_yandex_disk()
        except BaseException:
            print("fail")
        return




class VideoStatsFetcher:
    def __init__(self, game, top, resolution='1080'):
        db = mongoDBtools.MongoDbTools('GameStats')
        self.resolution = resolution
        self.db_game = mongoDBtools.MongoDbTools(game)
        gamedata = db.read_videodata_from_db({"name": game})
        self.gameid = gamedata['id'][0]
        self.maxvideos = int(gamedata['videos'][0])
        self.videos = top
        self.appid = settings.PlaysTvAppId
        self.appkey = settings.PlaysTvKey

    def turn_metatags_to_hashtags(self, metatags):
        hashtags = []
        for i in metatags:
            hashtag = self.parse_metatag(i)
            hashtags.append(hashtag)
        return hashtags

    def parse_metatag(self, metatag):
        parts = metatag["metatag"].split(":")
        return parts[-1]

    def get_vid_stats_page(self, page, limit):
        call = 'https://api.plays.tv/data/v1/videos/search?appid={0}&appkey={1}' \
               '&gameId={2}&limit={3}&page={4}'.format(self.appid, self.appkey, self.gameid, limit, page)
        try:
            r = requests.get(call).json()
            r = r['content']['items']
        except Exception as e:
            r = 'the error is %s' % e
        return r

    def save_vid_stats(self):
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
            self.store_game_videos(get_vids)
        return

    def store_game_videos(self, data):
        for i in data:
            if not (isinstance(i, str)):
                if i['resolutions'] != None:
                    #print(self.resolution in i['resolutions'])
                    if len(self.db_game.read_videodata_from_db({"id": i['id']})) == 0 and (self.resolution in i['resolutions']):
                        video = {}
                        video['id'] = i['id']
                        video['author'] = i['author']['id']
                        video['time'] = datetime.datetime.fromtimestamp(int(i['upload_time'])).strftime(
                            '%Y-%m-%d %H:%M:%S')
                        video['hashtags'] = []
                        video['title'] = i['description']
                        #print(rating)
                        #break
                        if 'metatags' in i:
                            video['hashtags'] = self.turn_metatags_to_hashtags(i['metatags'])
                        if 'hashtags' in i:
                            for hash in i['hashtags']:
                                video['hashtags'].append(hash['tag'])
                        video['hashtags'].append(i['author']['id'])
                        video['hashtags'].append(video['title'])
                        #print(video)
                        self.db_game.write_videodata_to_db(video)
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











