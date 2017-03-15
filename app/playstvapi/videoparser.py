from __future__ import unicode_literals
import youtube_dl
import requests
import json
import pickle

class VideosStatsParser():
    def __init__(self, game, hashtags, startdate, maxlength, request_typw):
        self.hashtags = hashtags
        self.game = game

    def jaccard_similarity(self, y):
        intersection_cardinality = len(set.intersection(*[set(self.hashtags), set(y)]))
        union_cardinality = len(set.union(*[set(self.hashtags), set(y)]))
        return intersection_cardinality / float(union_cardinality)


    def cosine_similarity(self, y):
        return


    def tf_idf_interpreter(self):
        return


    def parse_metatags_to_hashtags(self, metatags):
        return


    def select_suiting_video(self, metatgs):
        stats = StatsFetcher(self.game, self.request_type)
        return


class StatsFetcher():
    def __init__(self, game, request_type):
        self.game = game
        self.request_type = request_type


    def get_vid_stats(self):
        return


class VideoFetcher():
    def __init__(self, uri, game, videoid):
        self.uri = uri
        self.game = game
        self.id = videoid
    def fetch_video(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            'outtmpl': '../../Data/videos/{0}/{1}/%(title)s.%(duration)s'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        return
