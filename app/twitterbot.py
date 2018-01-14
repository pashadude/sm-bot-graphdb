import tweepy
import settings
from py2neo import Graph, Node, Relationship, authenticate
from py2neo import neo4j

class TwitterStatsFetcher:
    def __init__(self):
        auth = tweepy.OAuthHandler(settings.twitter_consumer_key, settings.twitter_consumer_secret)
        auth.set_access_token(settings.twitter_access_key, settings.twitter_access_secret)
        self.twitter = tweepy.API(auth)
        self.twitter_username = settings.twitter_account_name

    def getFollowers(self, user):
        return tweepy.Cursor(self.twitter.followers, id=user)

    def getInfluencers(self, user):
        return tweepy.Cursor(self.twitter.friends, id=user)

    def getTweets(self, user):
        return tweepy.Cursor(self.twitter.user_timeline ,id=user)

    def getHashtags(self, tweet):
        return tweet.entities.get('hashtags')

    def follow(self, user):
        return self.twitter.create_friendship(user)

    def unfollow(self, user):
        return self.twitter.destroy_friendship(user)

    def like(self, tweet):
        return self.twitter.create_favorite(tweet)

    def retweet(self, tweet):
        return self.twitter.retweer(tweet)

class TwitterNeo4jController:
    def __init__(self):
        authenticate(settings.NeoHost, settings.NeoLog, settings.NeoPass)
        self.graph = Graph("{0}/db/data/".format(settings.NeoHost))
        self.graph.delete_all()
        self.users = self.graph.get_or_create_index(neo4j.Node, 'users')
        self.tweets = self.graph.get_or_create_index(neo4j.Node, 'tweets')


class TwitterBotController:
    def __init__(self):





