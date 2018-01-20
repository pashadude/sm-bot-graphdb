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
        return tweepy.Cursor(self.twitter.user_timeline, id=user)

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
        #self.graph.delete_all()

    def insert_user(self, user_id, user_properties):
        user = self.graph.merge_one("User", "id", user_id)
        try:
            user.properties['name'] = user_properties['name']
            user.properties['created_at'] = user_properties['created_at']
            user.properties['default_profile'] = user_properties['default_profile']
            user.properties['default_profile_image'] = user_properties['default_profile_image']
            user.properties['description'] = user_properties['description']
            user.properties['favorites_count'] = user_properties['favorites_count']
            user.properties['followers_count'] = user_properties['followers_count']
            user.properties['friends_count'] = user_properties['friends_count']
            user.properties['geo_enabled'] = user_properties['geo_enabled']
            user.properties['is_translator'] = user_properties['is_translator']
            user.properties['lang'] = user_properties['lang']
            user.properties['listed_count'] = user_properties['listed_count']
            user.properties['location'] = user_properties['location']
            user.properties['notifications'] = user_properties['notifications']
            user.properties['profile_background_image_url'] = user_properties['profile_background_image_url']
            user.properties['profile_banner_url'] = user_properties['profile_banner_url']
            user.properties['profile_image_url'] = user_properties['profile_image_url']
            user.properties['protected'] = user_properties['protected']
            user.properties['screen_name'] = user_properties['screen_name']
            user.properties['statuses_count'] = user_properties['statuses_count']
            user.properties['time_zone'] = user_properties['time_zone']
            user.properties['url'] = user_properties['url']
            user.properties['utc_offset'] = user_properties['utc_offset']
            user.properties['verified'] = user_properties['verified']
            user.push()
        except KeyError as e:
            print("KeyError in user property " + str(e))
        return user

    def insert_tweet(self, user_id, tweet_id):
        user = self.graph.merge_one("User", "id", user_id)
        tweet = self.graph.merge_one("Tweet", "id", tweet_id)
        tweeted = Relationship(user, "tweeted", tweet)
        self.graph.create_unique(tweeted)
        return

    def insert_following(self, user_id, follower_id):
        user = self.graph.merge_one("User", "id", user_id)
        follower = self.graph.merge_one("User", "id", follower_id)
        following = Relationship(follower, "follows", user)
        self.graph.create_unique(following)
        return

    def insert_retweet(self, tweet_id, user_id):
        original_tweet = self.graph.merge_one("Tweet", "id", tweet_id)
        user = self.graph.merge_one("User", "id", user_id)
        retweeted = Relationship(user, "retweets", original_tweet)
        self.graph.create_unique(retweeted)
        return

    def insert_hashtag(self, tweet_id, hashtag_text):
        original_tweet = self.graph.merge_one("Tweet", "id", tweet_id)
        hashtag = self.graph.merge_one("Hashtag", "text", hashtag_text)
        tagged = Relationship(original_tweet, "tagged", hashtag)
        self.graph.create_unique(tagged)
        return

    def insert_like(self, tweet_id, user_id):
        tweet = self.graph.merge_one("Tweet", "id", tweet_id)
        user = self.graph.merge_one("User", "id", user_id)
        liked = Relationship(user, "likes", tweet)
        self.graph.create_unique(liked)
        return


class TwitterBotController:
    def __init__(self):
        self.twitterSchema = TwitterNeo4jController()
        self.twitterInput = TwitterStatsFetcher()

    def makeUserGraph(self, user):
        return

    def getTargets(self):
        return

    def likeNewComers(self):
        return

    def unfollowNonfollowers(self):
        return

    def retweetGamerHashtags(self):
        return

    def followSimilarInfluenced(self):
        return

    def requestFollowers(self):
        return



