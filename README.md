# TwitterTools

**Source code for this project is in file ```twittertools.py```** 

Twitter REST API tools  
Author: Greg Behm  
Copyright 2017  
 
Simplified interface for invoking commonly-used Twitter REST API endpoint  
requests. Methods are invoked on an authenticated TwitterTools instance.  
A few module function also are available for convenience, such as  
twittertools.save_tweets().  

*Caution!*
*This software is for personal use and demonstration only.*  
*Any Twitter content collected with this software should be used*  
*in accordance with Twitter's Terms of Service: https://twitter.com/en/tos*
 
*Read the Twitter Terms of Service, Twitter Developer Agreement,*  
*and Twitter Developer Policy before collecting Twitter content*  
*with this or any derivative software.*


## Example use

```python
import pathlib
import pprint
import random
import twittertools
```

#### Get an authenticated TwitterTools object
```python
filename = pathlib.Path.home().joinpath('.twitter', 'credentials.json')
twt = twittertools.TwitterTools(filename)
```

#### Get Rate Limits
```python
print('All rate limits')
limits = twt.get_rate_limits()
pprint.pprint(limits)
print('"Statuses" rate limits')
limits = twt.get_rate_limits('statuses')
pprint.pprint(limits)
print('"Search tweets" rate limit')
limits = twt.get_rate_limits('search', '/search/tweets')
pprint.pprint(limits)
```

#### Get and save user profiles
```python
print('User profiles:')
screen_names = ['katyperry', 'BarackObama', 'pourmecoffee', 'Fahrenthold']
profiles = twt.get_user_profiles(screen_names=screen_names)
for profile in profiles:
    pprint.pprint(profile)
twittertools.save_profiles(profiles, 'profiles.csv')
```

#### Post a tweet
```python
tweet = 'Twitter API Post Status test'
print(f'Post this tweet: {tweet}')
response = twt.post_status_update('Twitter API Post Status test')
if response:
    tweet = dict(response.items())
    pprint.pprint(tweet)
```

#### Get timeline requests
```python
tweets = twt.get_home_timeline()
print(f"Got {len(tweets)} tweets from authenticated user's home timeline")
tweets = twt.get_user_timeline()
print(f"Got {len(tweets)} tweets from authenticated user's status timeline")
twittertools.save_to_json(tweets, 'timeline.json')
print(f'Dumped {len(tweets)} tweets to JSON file')
tweets = twt.get_user_favorites()
print(f"Got {len(tweets)} tweets from authenticated user's favorites")

other_user = 'katyperry'
tweets = twt.get_user_timeline(other_user)
print(f"Got {len(tweets)} tweets from {other_user}'s status timeline")
tweets = twt.get_user_favorites(other_user)
print(f"Got {len(tweets)} tweets from {other_user}'s favorites")
```

#### Get tweets by id
```python
ids = [889189252264853504, 881880194113556480]
print(f'Get tweets {ids} by id')
tweets = twt.get_tweets_by_id(ids)
for tweet in tweets:
    pprint.pprint(tweet)
```

#### Get trends
```python
# Get all trend locations
all_trend_places = twt.get_trend_locations()
print(f'Total places with trends available: {len(all_trend_places)}')

# Paris, France by coordinates
lat, lon = 48.858093, 2.294694
print(f'Places closest to ({lat}, {lon}):')
trend_places = twt.get_trend_locations((lat, lon))
for place in trend_places:
    print(f"   {place['name']} woeid {place['woeid']}")

# U.S. WOEID
trends = twt.get_trends(woeid=23424977)
print(f'U.S. Trends:')
for trend in trends:
    pprint.pprint(trend)
print(f'Total U.S. Trends: {len(trends)}')
```

#### Get Follower and Following IDs
```python
screen_name = 'RockyMtnInst'
connection_ids = twt.get_connection_ids(screen_name=screen_name, which='followers')
print(f'{screen_name} has {len(connection_ids)} Followers')
connection_ids = twt.get_connection_ids(screen_name=screen_name, which='friends')
print(f'{screen_name} Follows {len(connection_ids)} users')
```

#### Use REST API Tweet Search
```python
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
```

#### Save search results to CSV file
```python
twittertools.save_tweets(tweets, 'tweets.csv')
```
