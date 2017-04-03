from __future__ import unicode_literals
import youtube_dl

class VideoFetcher():
    def __init__(self, uri, game, videoid):
        self.uri = uri
        self.game = game
        self.id = videoid
    def fetch_video(self):
        ydl_opts = {
            'format': 'best',
            'preferredcodec': 'mp3',
            #'dump_single_json': True,
            'outtmpl': '../../Data/videos/{0}/{1}/%(ext)s'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        return

a = VideoFetcher('http://plays.tv/video/586c23846d83444cba', 'League of Legends', '586c23846d83444cba')
a.fetch_video()