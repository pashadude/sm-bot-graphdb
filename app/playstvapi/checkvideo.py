from __future__ import unicode_literals
import youtube_dl

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
            'noplaylist': True,
            #'playlist_items': '0',
            #'writeinfojson': True,
            #'skip_download': True,
            #'dump_single_json': True,
            'outtmpl': '../../Data/videos/{0}/{1}/%(ext)s'.format(self.game, self.id),
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.uri])
        return

a = VideoFetcher('http://plays.tv/explore/videos?game_id=b179585c6b68a2791eea4a1ad3d7ef72', 'League of Legends', '57c068730a92ec4ea7')
a.fetch_video()