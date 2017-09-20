import pymongo
import pandas as pd
import settings

class MongoDbTools:

    def __init__(self, game):
        self.game = game

    def connect_to_video_db(self, host, port, username, password, db):
        try:
            if username and password:
                mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db)
                conn = pymongo.MongoClient(mongo_uri)
            else:
                conn = pymongo.MongoClient(host, port)
            return conn[db]
        except pymongo.errors.ConnectionFailure as e:
            return "Server connection failed: %s" % e


    def read_videodata_from_db(self, query, no_id=False):
        collection = self.game
        db = self.connect_to_video_db(settings.MongoHost, settings.MongoPort, settings.MongoUserName,
                                      settings.MongoPassword, settings.MongoDb)
        try:
            cursor = db[collection].find(query)
            df = pd.DataFrame(list(cursor))
        except:
            return "No data found"
        if no_id:
            del df['_id']
        return df


    def update_videodata_from_db(self, video_id, updated):
        collection = self.game
        db = self.connect_to_video_db(settings.MongoHost, settings.MongoPort, settings.MongoUserName,
                                      settings.MongoPassword, settings.MongoDb)
        try:
            db.collection.update_one({'_id': video_id}, updated)
        except:
            return "error"
        return


    def write_videodata_to_db(self, json):
        collection = self.game
        db = self.connect_to_video_db(settings.MongoHost, settings.MongoPort, settings.MongoUserName,
                                      settings.MongoPassword, settings.MongoDb)
        try:
            db.collection.insert_one(json['content']['video'])
        except:
            return "error"
        return