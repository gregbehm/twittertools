"""
twittertools.py

Twitter API data acquisition tools
Author: Greg Behm
Copyright 2017

Caution!
   This software is for personal use and demonstration only.
   Any Twitter content collected with this software should be
   used in accordance with Twitter's Terms of Service:
   
   https://twitter.com/en/tos
   
   Read the Twitter Terms of Service, Twitter Developer Agreement,
   and Twitter Developer Policy before collecting Twitter content
   with this or any derivative software.
   
Some software presented here was derived from or inspired by 
sample code in the book Mining the Social Web, 2nd Edition,
copyright 2014 by Matthew A. Russell, O'Reilly, ISBN 978-1449367619.
The book's author and publisher give permission to reuse sample code
under the Simplified BSD License. More information is found at:
https://github.com/ptwobrussell/Mining-the-Social-Web-2nd-Edition

"""

import collections
import datetime
import json
import pandas
import re
import time
# https://pypi.python.org/pypi/twitter
import twitter


def get_api(credentials_file):
    """
    Create an authenticated twitter.Twitter() API object.

    :param credentials_file: Twitter application credentials JSON file name.
    :return: twitter.Twitter() API object
    """

    def load_json_credentials(credentials_file):
        """
        Load the Twitter app credentials file from the given
        JSON credentials_file (example shown below) and return
        the authentication credentials as a namedtuple containing
        the four necessary data items:
            {
                "consumer_key": "<consumer_key>",
                "consumer_secret": "<consumer_secret>",
                "access_token": "<access_token>",
                "access_token_secret": "<access_token_secret>"
            }

        :param credentials_file: Twitter application credentials JSON file name.
        :return: A namedtuple containing the necessary authentication data.
        """

        with open(credentials_file) as fd:
            data = json.load(fd)
            codes = ['consumer_key', 'consumer_secret',
                     'access_token', 'access_token_secret']
            Credentials = collections.namedtuple('Credentials', codes)
            return Credentials(data['consumer_key'], data['consumer_secret'],
                               data['access_token'], data['access_token_secret']
                               )

    # def load_json_credentials

    cr = load_json_credentials(credentials_file)
    consumer_key, consumer_secret = cr.consumer_key, cr.consumer_secret
    access_token, access_token_secret = cr.access_token, cr.access_token_secret
    auth = twitter.oauth.OAuth(access_token, access_token_secret,
                               consumer_key, consumer_secret)
    return twitter.Twitter(auth=auth)


def save_tweets(tweets, path_or_buf):
    """
    Save a list of tweets to a CSV file, saving select
    fields as defined in function unpack_tweet().
    
    :param tweets: List of tweet objects
    :param path_or_buf: String, file path or file handle
    :return: None
    """

    df = pandas.DataFrame(unpack_tweet(tweet) for tweet in tweets)
    df.to_csv(path_or_buf, index=False, encoding='utf-8-sig')


def save_profiles(profiles, path_or_buf):
    """
    Save a list of user objects to a CSV file, saving select
    fields as defined in function unpack_profile().
    
    :param profiles: List of user objects
    :param path_or_buf: String, file path or file handle
    :return: None
    """

    df = pandas.DataFrame(unpack_profile(profile) for profile in profiles)
    df.to_csv(path_or_buf, index=False)


def get_datum(item, *args):
    """
    Search for single-value object element by dictionary key words.
    The caller must specify the necessary key words in correct hierarchical
    order. For example, to get a tweet's user screen_name, e.g.
    {"user": {..., "screen_name": "katyperry", ...}},
    call get_datum(tweet, 'user', 'screen_name')
    
    :param item: Twitter dictionary object, e.g. Tweet or User
    :param args: Item-search dictionary keys
    :return: Requested datum, or None if not found.
    """

    for arg in args:
        item = item[arg]
        if not item:
            return None

    return item


def get_list_dict_data(item, *args):
    """
    Search for a list of dictionary objects by dictionary key words.
    The caller must specify the necessary key words in correct hierarchical
    order. The last key word specifies the dictionary element within each
    list item. For example, to get a tweet's hashtags, e.g.
    {"entities": {"hashtags": [{"text": "blockchain",...}},
    call get_list_dict_data(tweet, 'entities', 'hashtags', 'text')
    
    :param item: Twitter dictionary object, e.g. Tweet or User
    :param args: Item-search dictionary keys
    :return: Concatenated string of each list element for requested type.
    """

    def next_item(item, key):
        """
        Get a dictionary or list object, depending on whether
        the input item is a dictionary or list.
        
        :param item: Twitter object dictionary or list
        :param key: Target element key word
        :return: If item is a dictionary, return the value for input key.
                 If item is a list with dictionary elements containing
                 the input key, return the list.
        """

        # Try item as a dictionary
        try:
            # return the dictionary item's value
            return item[key]
        except:
            # Try item as a list of dictionaries
            try:
                if item[0].get(key):
                    # return the dictionary
                    return item
            except:
                # Nothing relevant found
                return None

    # def next_item

    for arg in args:
        item = next_item(item, arg)
        if not item:
            return None

    # Concatenate all list elements in a space-separated string
    key = args[-1]
    return ' '.join(elem[key] for elem in item)


def unpack_tweet(tweet):
    """
    Extract select fields from the given tweet object.
    
    :param tweet: Twitter Tweet object
    :return: Ordered dictionary of select tweet field values
    """

    fields = [('Screen name', get_datum(tweet, 'user', 'screen_name')),
              ('Created', format_datetime(get_datum(tweet, 'created_at'))),
              ('Text', clean_whitespace(get_datum(tweet, 'text'))),
              ('Retweet count', get_datum(tweet, 'retweet_count')),
              ('Hashtags', get_list_dict_data(tweet, 'entities', 'hashtags', 'text')),
              ('Mentions', get_list_dict_data(tweet, 'entities', 'user_mentions', 'screen_name')),
              ('URLs', get_list_dict_data(tweet, 'entities', 'urls', 'url')),
              ('Expanded URLs', get_list_dict_data(tweet, 'entities', 'urls', 'expanded_url')),
              ('Media URLs', get_list_dict_data(tweet, 'entities', 'media', 'url')),
              ('Media types', get_list_dict_data(tweet, 'entities', 'media', 'type')),
              ('Tweet ID', get_datum(tweet, 'id_str')),
              ('Symbols', get_list_dict_data(tweet, 'entities', 'symbols', 'text'))
              ]
    return collections.OrderedDict(fields)


def unpack_profile(profile):
    """
     Extract select fields from the given user object.
    
    :param profile: Twitter User object
    :return: Ordered dictionary of select user field values
    """

    fields = [('Name', get_datum(profile, 'name')),
              ('Screen name', get_datum(profile, 'screen_name')),
              ('ID', get_datum(profile, 'id_str')),
              ('Description', clean_whitespace(get_datum(profile, 'description'))),
              ('Location', get_datum(profile, 'location')),
              ('Tweets', get_datum(profile, 'statuses_count')),
              ('Following', get_datum(profile, 'friends_count')),
              ('Followers', get_datum(profile, 'followers_count')),
              ('Favorites', get_datum(profile, 'favourites_count')),
              ('Language', get_datum(profile, 'lang')),
              ('Listed', get_datum(profile, 'listed_count')),
              ('Created', format_datetime(get_datum(profile, 'created_at'))),
              ('Time zone', get_datum(profile, 'time_zone')),
              ('Protected', get_datum(profile, 'protected')),
              ('Verified', get_datum(profile, 'verified')),
              ('Geo enabled', get_datum(profile, 'geo_enabled'))
              ]
    return collections.OrderedDict(fields)


def format_datetime(date_str):
    """
    Convert Twitter's date time format ("Thu Jul 20 19:34:20 +0000 2017")
    to ISO 8601 International Standard Date and Time format.
    
    :param date_str: 
    :return: 
    """

    try:
        dt = datetime.datetime.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y')
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    except:
        return None


def clean_whitespace(text):
    """
    Remove extraneous whitespace characters (includes e.g. newlines)
    
    :param text: Input text
    :return: Cleaned text with unwanted whitespace characters replaced
             with single spaces.
    """

    return re.sub('\s+', ' ', text)


class TwitterTools:
    """
    twittertools Twitter API class
    """

    def __init__(self, credentials_file):
        self.credentials = credentials_file
        self.api = get_api(self.credentials)
        if self.api:
            self.api_endpoint_method = {
                '/application/rate_limit_status': self.api.application.rate_limit_status,
                '/favorites/list': self.api.favorites.list,
                '/followers/ids': self.api.followers.ids,
                '/friends/ids': self.api.friends.ids,
                '/search/tweets': self.api.search.tweets,
                '/statuses/home_timeline': self.api.statuses.home_timeline,
                '/statuses/user_timeline': self.api.statuses.user_timeline,
                '/statuses/lookup': self.api.statuses.lookup,
                '/statuses/update': self.api.statuses.update,
                '/trends/available': self.api.trends.available,
                '/trends/closest': self.api.trends.closest,
                '/trends/place': self.api.trends.place,
                '/users/lookup': self.api.users.lookup
            }

    def __repr__(self):
        return f'{self.__class__.__name__}({self.credentials!r})'

    def endpoint_request(self, endpoint, *args, **kwargs):
        """
        Send Twitter API requests (e.g. GET, POST), handle request errors,
        and return requested Twitter content.

        :param endpoint: Endpoint request string, e.g. '/search/tweets'
        :param args: Optional, user-supplied positional arguments
        :param kwargs: Optional, user-supplied keyword arguments
        :return: Twitter content, defined by endpoint request.
        """

        def handle_http_error(error, endpoint, wait, retry=True):
            """
            Handle common twitter.api.TwitterHTTPError(s)

            :param error: twitter.api.TwitterHTTPError error object
            :param endpoint: Endpoint request string, e.g. '/search/tweets'
            :param wait: Wait period, in seconds
            :param retry: Retry on error; default True
            :return: Updated wait time
            """

            # See https://dev.twitter.com/docs/error-codes-responses

            errors = {401: '(Unauthorized)',
                      403: '(Forbidden)',
                      404: '(Not Found)',
                      429: '(Rate Limit Exceeded)',
                      500: '(Internal Server Error)',
                      502: '(Bad Gateway)',
                      503: '(Service Unavailable)',
                      504: '(Gateway Timeout)'
                      }

            ecode = error.e.code
            now = f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}'
            descr = errors.get(ecode, "(Unknown)")
            print(f'{now}: Error {ecode} {descr} on "{endpoint}"', flush=True)

            if ecode in (401, 403, 404):
                # Caller must handle these errors. Return 0 wait time.
                return 0

            if ecode == 429:
                if retry:
                    print('Retrying in 15 minutes...', end=' ', flush=True)
                    time.sleep(60 * 15)
                    print('awake and trying again.')
                    # Return wait time to default 1 second.
                    return 1
                else:
                    # No retries
                    return 0

            if ecode in (500, 502, 503, 504):
                if retry:
                    print(f'Retrying in {wait} seconds...', end=' ', flush=True)
                    time.sleep(wait)
                    print('awake and trying again.')
                    wait *= 1.5
                    if wait < 60 * 30:
                        return wait
                print('Too many retries. Quitting.')

            raise error

        # def handle_http_error

        api_endpoint = self.api_endpoint_method[endpoint]

        wait = 1
        while wait:
            try:
                return api_endpoint(*args, **kwargs)
            except twitter.api.TwitterHTTPError as e:
                wait = handle_http_error(e, endpoint, wait)

    def get_user_tweets(self, endpoint, screen_name=None, user_id=None,
                        max_tweets=None, **kwargs):
        """
        Request a user's tweets (statuses) according to the endpoint

        :param endpoint: Endpoint request string, e.g. '/statuses/user_timeline'
        :param screen_name: User's screen name, a.k.a. handle, e.g. 'katyperry'
        :param user_id: User's numeric ID
        :param max_tweets: Maximum tweets requested
        :param kwargs: Optional, user-supplied keyword arguments
        :return: A list of Tweet objects
        """

        # No screen_name or user_id implies default to authenticated user
        if screen_name:
            kwargs['screen_name'] = screen_name
        elif user_id:
            kwargs['user_id'] = user_id

        count = 200
        tweets = []
        while True:
            # Limit each GET to a maximum 200 tweets
            kwargs['count'] = min(count, max_tweets - len(tweets)) if max_tweets else count

            # To correctly traverse the user's timeline, set the
            # max_id parameter after the first tweets are available.
            # See https://dev.twitter.com/rest/public/timelines.
            if tweets:
                kwargs['max_id'] = min(tweet['id'] for tweet in results) - 1

            results = self.endpoint_request(endpoint, **kwargs)
            if not results:
                break
            tweets.extend(results)
            if max_tweets and len(tweets) >= max_tweets:
                break

        return tweets

    def get_cursored_items(self, endpoint, key, count=5000, max_items=None, **kwargs):
        """
        Helper request function for cursored objects.
        
        :param endpoint: Endpoint request string, e.g. '/followers/ids'
        :param key: Cursored items key, e.g. 'ids'
        :param count: Maximum items per request
        :param max_items: Maximum total items requested
        :param kwargs: Optional, user-supplied keyword arguments
        :return: A list of requested objects
        """

        kwargs['count'] = count
        items = []
        cursor = -1
        while cursor:
            kwargs['cursor'] = cursor
            results = self.endpoint_request(endpoint, **kwargs)
            if not results:
                break
            items.extend(results[key])
            if max_items and len(items) >= max_items:
                break
            cursor = results['next_cursor']

        return items

    def get_items_by_lookup(self, endpoint, item_keyword, items, **kwargs):
        """
        Get user-requested objects of type item_keyword, named in the items list.
        
        :param endpoint: Endpoint request string, e.g. '/users/lookup'
        :param item_keyword: Endpoint request keyword
               Note: Endpoint 'id' requests must call the twitter.Twitter()
               API methods with kwargs['_id'] to produce correct results.
        :param items: User-supplied list of requested items, e.g. screen names
        :param kwargs: Optional, user-supplied keyword arguments
        :return: A list of user-requested objects. Note: The Twitter API
                 doesn't guarantee that objects are returned in the order
                 requested. The caller is responsible for confirming the
                 order and completeness of the returned list, if necessary.
        """

        # Request up to 100 items per call
        items_max = 100
        results = []
        while items:
            items_str = ','.join(str(item) for item in items[:items_max])
            kwargs[item_keyword] = items_str
            response = self.endpoint_request(endpoint, **kwargs)
            if not response:
                break
            results.extend(response)
            items = items[items_max:]

        return results

    def get_rate_limits(self, key_0=None, key_1=None):
        """
        Query the authorized user's current rate limit data.

        See Rate Limits chart at https://dev.twitter.com/rest/public/rate-limits

        :param key_0: Optional, single category request, e.g. 'statuses'
        :param key_1: Optional, subcategory category request, e.g. '/statuses/user_timeline'
        :return: Requested limits dictionary
        """

        limits = self.endpoint_request('/application/rate_limit_status')
        if limits:
            limits = limits['resources']
            if key_0 in limits:
                limits = limits[key_0]
                return limits[key_1] if key_1 else limits
            else:
                return limits

        return None

    def get_home_timeline(self, max_tweets=None):
        """
        Get a list of the most recent tweets and retweets posted
        by the authenticating user and the user's friends (following).        
        
        :param max_tweets: Optional maximum tweets requested
        :return: List of tweets
        """

        return self.get_user_tweets('/statuses/home_timeline', max_tweets)

    def get_user_timeline(self, screen_name=None, user_id=None, max_tweets=None):
        """
        Get a list of the most recent tweets posted by the user specified
        by screen_name or user_id. If both screen_name and user_id are given,
        screen_name is used. If neither screen_name nor user_id is given,
        results are collected for the authenticated user.        
        
        :param screen_name: User's screen name, a.k.a. handle, e.g. 'katyperry'
        :param user_id: User's numeric ID
        :param max_tweets: Maximum desired tweets
        :return: List of tweets
        """

        return self.get_user_tweets('/statuses/user_timeline', screen_name, user_id, max_tweets)

    def get_user_favorites(self, screen_name=None, user_id=None, max_tweets=None):
        """
        Get a list of the most recent tweets favorited by the authenticating
        user, or the user specified by screen_name or user_id. If both screen_name
        and user_id are given, screen_name is used. If neither screen_name nor user_id
        is given, results are collected for the authenticated user.
        
        :param screen_name: User's screen name, a.k.a. handle, e.g. 'katyperry'
        :param user_id: User's numeric ID
        :param max_tweets: Maximum desired tweets
        :return: List of tweets
        """

        return self.get_user_tweets('/favorites/list', screen_name, user_id, max_tweets)

    def get_user_profiles(self, screen_names=None, user_ids=None):
        """
        Get a list of user objects as specified by values given by the screen_names
        or user_ids list parameter. If both lists, screen_names and user_ids,
        are given, screen_names is used.
        
        :param screen_names: List of user screen names, a.k.a. handles
        :param user_ids: List of user numeric IDs
        :return: List of user objects
        """

        items = screen_names or user_ids
        item_keyword = 'screen_name' if screen_names else 'user_id'
        return self.get_items_by_lookup('/users/lookup', item_keyword, items)

    def get_tweets_by_id(self, ids):
        """
        Get a list of tweets, specified by a given list of
        numeric Tweet IDs in parameter ids.
        
        :param ids: List of unique numeric tweet IDs
        :return: List of requested tweets
        """

        return self.get_items_by_lookup('/statuses/lookup', '_id', ids)

    def get_connection_ids(self, which='friends', screen_name=None, user_id=None,
                           max_ids=None, **kwargs):
        """
        For the user specified by screen_name or user_id, get a list of user IDs
        for every user the specified user is following (which="friends"), or
        for every user following the specified user (which=followers"). If both
        screen_name and user_id are given, screen_name is used.  
        :param which: Connection type, Friends or Followers
        :param screen_name: User's screen name, a.k.a. handle, e.g. 'katyperry'
        :param user_id: User's numeric ID
        :param max_ids: Maximum IDs to request
        :param kwargs: Optional, user-supplied keyword arguments
        :return: List of user IDs
        """

        endpoint = {'friends': '/friends/ids',
                    'followers': '/followers/ids'}.get(which)
        # No screen_name or user_id implies default to authenticated user
        if screen_name:
            kwargs['screen_name'] = screen_name
        elif user_id:
            kwargs['user_id'] = user_id
        return self.get_cursored_items(endpoint, 'ids', max_items=max_ids, **kwargs)

    def get_trend_locations(self, lat_lon=None):
        """
        Get a list of locations for which Twitter has trending topic information.
        Each location response encodes the WOEID and other human-readable information,
        such as a canonical name and country.
        
        If param lat_lon is given, returns a list of locations for which
        Twitter has trending topics closest to the specified location.        
        
        A WOEID is a Yahoo! Where On Earth ID (http://developer.yahoo.com/geo/geoplanet).
        
        :param lat_lon: Earth latitude and longitude coordinates,
                        passed as a tuple or list of decimal values
                        ranging from +90.0 to -90.0 for latitude,
                        and from +180.0 to -180.0 for longitude.
        :return: List of Twitter location objects
        """

        if lat_lon:
            lat, lon = lat_lon
            kwargs = {'lat': lat, 'long': lon}
            return self.endpoint_request('/trends/closest', **kwargs)
        else:
            return self.endpoint_request('/trends/available')

    def get_trends(self, woeid=1):
        """
        Get a list of the top 50 trending topics for a specific WOEID,
        if trending information is available for that WOEID. Responses
        are trend objects that encode the trending topic, from which
        the "query" parameter can be used to search for the topic on
        Twitter Search.
        
        :param woeid: Yahoo! Where On Earth location ID
                      (http://developer.yahoo.com/geo/geoplanet)
                      Default: WOEID=1 for worldwide
        :return: List of trending topics for the specified WOEID.
        """

        kwargs = {'_id': woeid}
        return self.endpoint_request('/trends/place', **kwargs)[0]['trends']

    def post_status_update(self, status, media_ids=None, **kwargs):
        """
        Post a Tweet!
        
        :param status: Required text
        :param media_ids: Optional media id list. Twitter-supplied ids from media upload.
                          See https://dev.twitter.com/rest/reference/post/media/upload
        :param kwargs: Optional, user-supplied keyword arguments
        :return: Status (tweet) object, or error on failure
        """

        kwargs['status'] = status
        if media_ids:
            kwargs['media_ids'] = media_ids
        return self.endpoint_request('/statuses/update', **kwargs)

    def search_tweets(self, query, max_requests=5):
        """
        Get a list of relevant Tweets matching a specified query.
        
        # See https://dev.twitter.com/rest/public/search and
        # https://dev.twitter.com/rest/reference/get/search/tweets
        
        Quoting from https://dev.twitter.com/rest/public/search:
        
        "The Twitter Search API is part of Twitter’s REST API.
        It allows queries against the indices of recent or
        popular Tweets and behaves similarly to, but not exactly
        like the Search feature available in Twitter mobile or web
        clients, such as Twitter.com search. The Twitter Search API
        searches against a sampling of recent Tweets published in
        the past 7 days.
             
        Before getting involved, it’s important to know that the
        Search API is focused on relevance and not completeness.
        This means that some Tweets and users may be missing from
        search results. If you want to match for completeness you
        should consider using a Streaming API instead."

        :param query: Twitter search term
        :param max_requests: Maximum query requests. Each request
                             returns up to 100 results, and the
                             authenticated user is limited to
                             180 requests per 15 minutes.                             
        :return: List of tweets
        """

        # Prepare first request
        kwargs = {'q': query, 'count': 100}
        tweets = []
        for search in range(max_requests):
            if tweets:
                try:
                    next_results = results['search_metadata']['next_results']
                    # Create a dict from next_results, which has this format:
                    # ?max_id=313519052523986943&q=NCAA&include_entities=1
                    kwargs = dict(item.split('=') for item in next_results[1:].split("&"))
                # No further results when 'next_results' is missing
                except KeyError:
                    break

            results = self.endpoint_request('/search/tweets', **kwargs)
            if not results['statuses']:
                break
            tweets.extend(results['statuses'])

        return tweets


# imports for demonstration
import pathlib
import pprint
import random


def main():
    """
    Demonstration code.
    """

    # Get an authenticated TwitterTools object
    filename = pathlib.Path.home().joinpath('.twitter', 'credentials.json')
    twt = TwitterTools(filename)

    # Get Rate Limits data
    print('All rate limits')
    limits = twt.get_rate_limits()
    pprint.pprint(limits)
    print('"Statuses" rate limits')
    limits = twt.get_rate_limits('statuses')
    pprint.pprint(limits)
    print('"Search tweets" rate limit')
    limits = twt.get_rate_limits('search', '/search/tweets')
    pprint.pprint(limits)
    print()

    # Get and save some user profiles
    print('User profiles:')
    screen_names = ['katyperry', 'BarackObama', 'pourmecoffee', 'realDonaldTrump']
    profiles = twt.get_user_profiles(screen_names=screen_names)
    for profile in profiles:
        print(profile)
    save_profiles(profiles, 'profiles.csv')
    print()

    # Post a tweet
    tweet = 'Twitter API Post Status test'
    print(f'Post this tweet: {tweet}')
    response = twt.post_status_update('Twitter API Post Status test')
    tweet = dict(response.items())
    pprint.pprint(tweet)
    print()

    # Get timeline requests
    tweets = twt.get_home_timeline()
    print(f"Got {len(tweets)} tweets from authenticated user's home timeline")
    tweets = twt.get_user_timeline()
    print(f"Got {len(tweets)} tweets from authenticated user's status timeline")
    with open('timeline.json', 'w') as fp:
        json.dump(tweets, fp)
        print(f'Dumped {len(tweets)} tweets to JSON file')
    tweets = twt.get_user_favorites()
    print(f"Got {len(tweets)} tweets from authenticated user's favorites")

    other_user = 'katyperry'
    tweets = twt.get_user_timeline(other_user)
    print(f"Got {len(tweets)} tweets from {other_user}'s status timeline")
    tweets = twt.get_user_favorites(other_user)
    print(f"Got {len(tweets)} tweets from {other_user}'s favorites")
    print()

    # Get tweets by id
    ids = [889189252264853504, 881880194113556480]
    print(f'Get tweets {ids} by id')
    tweets = twt.get_tweets_by_id(ids)
    for tweet in tweets:
        pprint.pprint(tweet)
    print()

    # Get trends
    all_trend_places = twt.get_trend_locations()
    print(f'Total places with trends available: {len(all_trend_places)}')
    #
    lat, lon = 48.858093, 2.294694
    print(f'Places closest to ({lat}, {lon}):')
    trend_places = twt.get_trend_locations((lat, lon))
    for place in trend_places:
        print(f"   {place['name']} woeid {place['woeid']}")
    print()

    trends = twt.get_trends(woeid=23424977)
    print(f'U.S. Trends:')
    for trend in trends:
        print(trend)
    print(f'Total U.S. Trends: {len(trends)}')
    print()

    # Get Follower and Following IDs
    screen_name = 'RockyMtnInst'
    connection_ids = twt.get_connection_ids(screen_name=screen_name, which='followers')
    print(f'{screen_name} has {len(connection_ids)} Followers')
    connection_ids = twt.get_connection_ids(screen_name=screen_name, which='friends')
    print(f'{screen_name} Follows {len(connection_ids)} users')
    print()

    # Use REST API Tweet Search
    print('Test the Twitter REST API Tweet Search, with randomly chosen trending topics')
    trend_queries = set()
    woeids = [place['woeid'] for place in all_trend_places]
    for woeid in random.sample(woeids, 10):
        trends = twt.get_trends(woeid=woeid)
        for trend in trends:
            trend_queries.add(trend['query'])

    print(f'Trend queries random sample size: {len(trend_queries)}')
    tweets = []
    for query in random.sample(trend_queries, 200):
        result = twt.search_tweets(query, max_requests=1)
        tweets.extend(result)
    print(f'Total tweets from trend searches: {len(tweets)}')

    save_tweets(tweets, 'tweets.csv')


if __name__ == '__main__':
    main()
