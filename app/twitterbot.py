import tweepy
import settings
import time
import playstvapi.metrics as metrics
import numpy as np
from py2neo import Graph, Node, Relationship, authenticate
#from py2neo import neo4j


class TwitterStatsFetcher:
    def __init__(self):
        auth = tweepy.OAuthHandler(settings.twitter_consumer_key, settings.twitter_consumer_secret)
        auth.set_access_token(settings.twitter_access_key, settings.twitter_access_secret)
        self.twitter = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)
        self.twitter_username = settings.twitter_account_name

    def getAccount(self, screen_name):
        try:
            result = self.twitter.get_user(screen_name=screen_name)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def getSelf(self):
        try:
            result = self.twitter.me()
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def getFollowers(self, user_id):
        try:
            result = tweepy.Cursor(self.twitter.followers, id=user_id)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def getFollowersPage(self, user_id, page):
        try:
            result = tweepy.Cursor(self.twitter.followers, id=user_id, count = 300).pages()
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def getInfluencers(self, user_id):
        try:
            result = tweepy.Cursor(self.twitter.friends, id=user_id)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def getFeed(self, user_id):
        try:
            result = tweepy.Cursor(self.twitter.user_timeline, id=user_id)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result


    def getHashtags(self, tweet):
        try:
            result = tweet.entities.get('hashtags')
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return result

    def follow(self, user):
        try:
            self.twitter.create_friendship(user)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return

    def unfollow(self, user):
        try:
            self.twitter.destroy_friendship(user)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return

    def like(self, tweet):
        try:
            self.twitter.create_favorite(tweet)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return

    def retweet(self, tweet):
        try:
            self.twitter.retweet(tweet)
        except tweepy.TweepError:
            print("lib error: ", tweepy.TweepError)
        return


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

    def get_users_followers(self, user_id):
        followers = self.graph.data(
            "MATCH (followers)-[:follows]->(user) WHERE user.id = {param} RETURN followers.id",
            param=user_id)
        return followers


    def get_past_retweets(self):
        retweets = self.graph.data("MATCH (you)-[:retweets]->(tweets) RETURN tweets.id")
        return retweets

    def get_influncers(self):
        influencers = self.graph.data("MATCH (you)-[:follows]->(influencers) WHERE you.id = {param} RETURN influencers.id", param = settings.twitter_account_name)
        return influencers


class TwitterBotController:
    def __init__(self):
        self.twitterSchema = TwitterNeo4jController()
        self.twitterInput = TwitterStatsFetcher()
        self.me = self.twitterInput.getSelf()
        self.inflgamers = settings.twitter_account_gamers
        self.corpus = []
        self.metrics = metrics.SimilarityMeasures()


    def makeUserGraph(self, user):
        props = user._json
        return


    def makeMyGraph(self):
        props = self.me._json
        my_id = self.me.id
        self.twitterSchema.insert_user(my_id, props)
        userdata = []
        #count = 0
        my_followers = self.twitterInput.getFollowers(my_id)
        for user in my_followers.items():
            self.twitterSchema.insert_user(user._json['id'], user._json)
            self.twitterSchema.insert_following(my_id, user._json['id'])
        #    time.sleep(5)
        my_influencers = self.twitterInput.getInfluencers(my_id)
        for user in my_influencers.items():
            userdata.append(user._json)
            #print(user._json['id'], count)
            #count+=1
            #if count%250==0:
            #    time.sleep(900)
        for user in userdata:
            self.twitterSchema.insert_user(user['id'], user)
            self.twitterSchema.insert_following(user['id'], my_id)
            self.makeInfluencerGraph(user['id'])
            #time.sleep(5)
        return

    def makeInfluencerGraph(self, influencer_id):
        followers = self.twitterInput.getFollowers(influencer_id)
        #count = 0
        userdata = []
        for user in followers.items():
            userdata.append(user._json)
            #count += 1
            #if count % 300 == 0:
                #time.sleep(900)
            #print(user._json['id'], count)
        for user in userdata:
            self.twitterSchema.insert_user(user['id'], user)
            self.twitterSchema.insert_following(influencer_id, user['id'])
        return

    def getPotentialFollowers(self):
        followers = self.twitterSchema.get_influncers()
        for id in followers:
            print(id)
            print(self.twitterSchema.get_users_followers(id))

        return

    def getInfluencersFeed(self):
        counter = 1
        for inf in self.inflgamers:
            #print(inf)
            user = self.twitterInput.getAccount(inf)
            tweet_feed = self.twitterInput.getFeed(user._json['id'])
            for status in tweet_feed.items(25):
                text = status._json['text']
                self.corpus.append(text)
            if counter == 27:
                time.sleep(900)
                counter = 1
            else:
                counter+=1
        return

    def retweetOfTheShift(self):
        self.getInfluencersFeed()
        data = self.twitterSchema.get_influncers()
        cosine = 0
        retweets = []
        for re in self.twitterSchema.get_past_retweets():
            retweets.append(re['tweets.id'])
        #print(retweets)
        for k in data:
            tweet_feed = self.twitterInput.getFeed(k['influencers.id'])
            for status in tweet_feed.items(1):
                text = status._json['text']
                tf_idf_space = [text] + self.corpus
                #tf_idf = metrics.SimilarityMeasures.tf_idf(tf_idf_space)
                score = self.metrics.tf_idf_cosine(tf_idf_space, 'vector')
                if cosine < np.mean(score) and status._json['id'] not in retweets:
                    cosine = np.mean(score)
                    tweet_id = status._json['id']
        self.twitterSchema.insert_retweet(tweet_id, self.me.id)
        self.twitterInput.retweet(tweet_id)
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

testee.getPotentialFollowers()
testee.retweetOfTheShift()
#testee.makeInfluencerGraph('Stoop_OW')
#testee.unfollowNonfollowers()
testee.makeMyGraph()
