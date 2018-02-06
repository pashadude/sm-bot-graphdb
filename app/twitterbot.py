import tweepy
import settings
import time
import playstvapi.metrics as metrics
from py2neo import Graph, Node, Relationship, authenticate
#from py2neo import neo4j


class TwitterStatsFetcher:
    def __init__(self):
        auth = tweepy.OAuthHandler(settings.twitter_consumer_key, settings.twitter_consumer_secret)
        auth.set_access_token(settings.twitter_access_key, settings.twitter_access_secret)
        self.twitter = tweepy.API(auth)
        self.twitter_username = settings.twitter_account_name

    def getAccount(self, screen_name):
        return self.twitter.get_user(screen_name=screen_name)

    def getSelf(self):
        return self.twitter.me()

    def getFollowers(self, user_id):
        return tweepy.Cursor(self.twitter.followers, id=user_id)

    def getInfluencers(self, user_id):
        return tweepy.Cursor(self.twitter.friends, id=user_id)

    def getFeed(self, user_id):
        return tweepy.Cursor(self.twitter.user_timeline, id=user_id)

    def getHashtags(self, tweet):
        return tweet.entities.get('hashtags')

    def follow(self, user):
        return self.twitter.create_friendship(user)

    def unfollow(self, user):
        return self.twitter.destroy_friendship(user)

    def like(self, tweet):
        return self.twitter.create_favorite(tweet)

    def retweet(self, tweet):
        return self.twitter.retweet(tweet)


class TwitterNeo4jController:
    def __init__(self):
        authenticate(settings.NeoHost, settings.NeoLog, settings.NeoPass)
        self.graph = Graph("{0}/db/data/".format(settings.NeoHost))
        #self.graph.delete_all()

    def insert_user(self, user_id, user_properties):
        user = Node("User", id=user_id)
        self.graph.merge(user)
        try:
            user.properties['name'] = user_properties['name']
            user.properties['created_at'] = user_properties['created_at']
            user.properties['default_profile'] = user_properties['default_profile']
            user.properties['default_profile_image'] = user_properties['default_profile_image']
            user.properties['description'] = user_properties['description']
            user.properties['favourites_count'] = user_properties['favourites_count']
            user.properties['followers_count'] = user_properties['followers_count']
            user.properties['friends_count'] = user_properties['friends_count']
            user.properties['geo_enabled'] = user_properties['geo_enabled']
            user.properties['is_translator'] = user_properties['is_translator']
            user.properties['lang'] = user_properties['lang']
            user.properties['listed_count'] = user_properties['listed_count']
            user.properties['location'] = user_properties['location']
            user.properties['notifications'] = user_properties['notifications']
            user.properties['profile_background_image_url'] = user_properties['profile_background_image_url']
            #user.properties['profile_banner_url'] = user_properties['profile_banner_url']
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
        user = Node("User", id=user_id)
        self.graph.merge(user)
        tweet = Node("Tweet", id=tweet_id)
        self.graph.merge(tweet)
        tweeted = Relationship(user, "tweeted", tweet)
        self.graph.merge(tweeted)
        return

    def insert_following(self, user_id, follower_id):
        user = Node("User", id=user_id)
        self.graph.merge(user)
        follower = Node("User", id=follower_id)
        self.graph.merge(follower)
        following = Relationship(follower, "follows", user)
        self.graph.merge(following)
        return

    def insert_retweet(self, tweet_id, user_id):
        original_tweet = Node("Tweet", id=tweet_id)
        self.graph.merge(original_tweet)
        user = Node("User", id=user_id)
        self.graph.merge(user)
        retweeted = Relationship(user, "retweets", original_tweet)
        self.graph.merge(retweeted)
        return

    def insert_hashtag(self, tweet_id, hashtag_text):
        original_tweet = Node("Tweet", id=tweet_id)
        self.graph.merge(original_tweet)
        hashtag = Node("Hashtag", text=hashtag_text)
        self.graph.merge(hashtag)
        tagged = Relationship(original_tweet, "tagged", hashtag)
        self.graph.merge(tagged)
        return

    def insert_like(self, tweet_id, user_id):
        tweet = Node("Tweet", id=tweet_id)
        self.graph.merge(tweet)
        user = Node("User", id=user_id)
        self.graph.merge(user)
        liked = Relationship(user, "likes", tweet)
        self.graph.merge(liked)
        return


class TwitterBotController:
    def __init__(self):
        self.twitterSchema = TwitterNeo4jController()
        self.twitterInput = TwitterStatsFetcher()
        self.me = self.twitterInput.getSelf()
        self.inflgamers = settings.twitter_account_gamers


    def makeUserGraph(self, user):
        props = user._json
        return


    def makeMyGraph(self):
        props = self.me._json
        my_id = self.me.id
        self.twitterSchema.insert_user(my_id, props)
        my_followers = self.twitterInput.getFollowers(my_id)
        for user in my_followers.items():
            self.twitterSchema.insert_user(user._json['id'], user._json)
            self.twitterSchema.insert_following(my_id, user._json['id'])
            time.sleep(5)
        my_influencers = self.twitterInput.getInfluencers(my_id)
        for user in my_influencers.items():
            self.twitterSchema.insert_user(user._json['id'], user._json)
            self.twitterSchema.insert_following(user._json['id'], my_id)
            time.sleep(5)
        return

    def pushInfluencerFeed(self, user_name):
        user = self.twitterInput.getAccount(user_name)
        #print(user._json)
        tweet_feed = self.twitterInput.getFeed(user._json['id'])
        for status in tweet_feed.items(25):
            print(status._json['text'], status._json['entities']['hashtags'], status._json['entities']['user_mentions'])
        return

    def getTargets(self):
        return

    def likeNewComers(self):
        return

    def unfollowNonfollowers(self):
        followers = []
        influencers = []
        follower_threshold = 1000
        my_id = self.me.id
        my_influencers = self.twitterInput.getInfluencers(my_id)
        for user in my_influencers.items():
            time.sleep(5)
            if int(user._json['followers_count']) < 1000:
                influencers.append(user._json['screen_name'])
        my_followers = self.twitterInput.getFollowers(my_id)
        for user in my_followers.items():
            followers.append(user._json['screen_name'])
        for candidate in influencers:
            if not(candidate in followers):
                print("unfollowed", candidate)
                target = self.twitterInput.getAccount(candidate)
                self.twitterInput.unfollow(target.id)
        return

    def retweetGamerHashtags(self):
        return

    def getHashtagSpace(self):
        return



testee = TwitterBotController()
testee.pushInfluencerFeed("MinidukeLoL")

#testee.unfollowNonfollowers()
#testee.makeMyGraph()