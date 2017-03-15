import requests
import json
import pickle


def main():
    bar = ['League of Legends', 'DOTA 2', 'Overwatch', 'For Honor', 'Battlefield 1', '']
    foo = GamesParser(bar)
    foo.gamelist()


class GamesParser:
    def __init__(self, games):
        self.games = games
        self.appid = 'DLKWBYCZNnBpDL4WOIRkCLFtDI7tO2RsOIGZ'
        self.appkey = '9exhOxYiMA4l0TH_utz5LAHH4Ii2ANbX'

    def gamelist(self):
        call = 'https://api.plays.tv/data/v1/games?appid={0}&appkey={1}'.format(self.appid, self.appkey)
        r = requests.get(call)
        if r.status_code != 404:
            if r.status_code == 200:
                self.parse_gamelist(r.text)
            elif r.status_code == 403:
                return 'forbidden'
            else:
                return 'error {}'.format(r.status_code)
        else:
            return 'down'

    def parse_gamelist(self, gamelist):
        game_info = {}
        game_data = json.loads(gamelist)
        exists = False
        for i in game_data['content']['games'].values():
            if i['title'] in self.games:
                name = i['title']
                id = i['id']
                videos = i['stats']['videos']
                exists = True
                if not(name in game_info.keys()):
                    game_info[name] = {'id': id, 'videos': videos}
                elif game_info[name]['videos'] < videos:
                    game_info[name] = {'id': id, 'videos': videos}
        if exists:
            pickle.dump(game_info, open('../../Data/games.pkl', 'wb+'))
        return


if __name__ == "__main__":
    main()