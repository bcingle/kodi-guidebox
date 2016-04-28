import urllib
import json
from datetime import datetime
from datetime import timedelta
import time


class Guidebox:
    """
    Interface with the Guidebox API
    https://api.guidebox.com/
    This class provides functions to build queries for accessing many of the features
    provided by the Guidebox API.
    """

    def __init__(self, apiKey, cache):
        """
        :param apiKey: The API key provided by Guidebox
        :param cache: The cached data, expires after 24 hours
        """
        self.__apiKey = apiKey
        self.__version = "v1.43"
        self.__region = "US"
        self.__baseUrl = "https://api-public.guidebox.com/" + self.__version + "/" + self.__region + "/" + self.__apiKey

        self.__channelTypes = {
            "all": "all",
            "tv": "television",
            "online": "online"
        }
        now = datetime.now()
        if not cache:
            cache = {}
        if "cache_time" in cache:
            # check the cache time to see if it is expired
            now = datetime.now()
            yesterday = now - timedelta(hours=24)
            cacheTime = cache["cache_time"]
            try:
                cacheTime = datetime.strptime(cacheTime, "%c")
            except TypeError:
                cacheTime = datetime(*(time.strptime(cacheTime, "%c")[0:6]))
            if cacheTime < yesterday:
                cache = {}
        
        if cache == {}:
            # setup the cache from scratch
            cache["cache_time"] = datetime.strftime(now, '%c')
            cache["shows_by_index"] = {}
            cache["shows_by_id"] = {}
            cache["channels_by_index"] = {}
            cache["channels_by_type"] = {
                "tv": {},
                "online": {},
                "all": {}
            }
            cache["channels_by_id"] = {}
            cache["episodes_by_index"] = {}
            cache["episodes_by_id"] = {}
            cache["sources_by_id"] = {}
            
        self.__cache = cache
        
        pass


    def http_get(self, url):
        print "Guidebox url: " + url
        response = urllib.urlopen(url)
        j = json.load(response)
        print "Response: " + json.dumps(j)
        return j

    def build_query(self, query, params=None):
        """
        Build a query for Guidebox API. Base URL for the API is extended with query and params.
        :param query: A list of URL elements, in the form ['search', 'channels', 'title', 'abc', ...]
        :param params: Params in the form {'key': ['value1', 'value2'], ...}
        :return: The query as a string
        """
        url = self.__baseUrl
        url = ["/".join(str(item) for item in [self.__baseUrl] + query)]
        first = True
        if params == None:
            params = {}
        for key, values in params:
            for value in values:
                if first:
                    url.append("?")
                    first = False
                else:
                    url.append("&")
                url.append(key)
                url.append("=")
                url.append(value)
        return "".join(url)

    def list_tv_channels(self, start=0, limit=50):
        """
        List all TV channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return self.list_channels_by_type(self.__channelTypes["tv"], start, limit)

    def list_online_channels(self, start=0, limit=50):
        """
        List all online channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return self.list_channels_by_type(self.__channelTypes["online"], start, limit)

    def list_all_channels(self, start=0, limit=50):
        """
        List all TV and Online channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return self.list_channels_by_type(self.__channelTypes["all"], start, limit)

    def list_channels_by_type(self, type, start=0, limit=50):
        """
        List all channels of a specific type
        :param type: Type to load, one of self.channelTypes
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        # first check to see if we have them all
#        complete = True
#        for index in range(start, limit):
#            if index not in self.__cache["channels_by_index"]:
#                complete = False
#                break
#        if complete:
#            results = {}
#            # TODO: Add caching capabilities
#            return 
        query = self.build_query(["channels", type, start, limit])
        return self.http_get(query)
    
    def fetch_channel_by_id(self, channelId):
        """
        Fetch a channel by ID
        :param channelId: The Guidebox channel ID
        """
        query = self.build_query(["channel", channelId])
        return self.http_get(query)

    def search_channel(self, query, start=0, limit=50, fuzzy=False):
        """
        Search for a channel by name
        :param query: Search term
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :param fuzzy: Whether to search for exact phrase
        :return:
        """
        query = self.build_query(["search", "channel", "title", query, start, limit])
        return self.http_get(query)

    def list_shows_for_channel(self, channelId, start=0, limit=50, sources="all", platform=None):
        query = self.build_query(["shows", channelId, start, limit, sources, platform])
        return self.http_get(query)

    def fetch_show_info(self, showId):
        """
        Fetch information for a show, such as overview, various artwork, and cast
        :param showId: Guidebox show ID
        """
        query = self.build_query(["show", showId])
        return self.http_get(query)

    def list_seasons_for_show(self, showId):
        query = self.build_query(["show", showId, "seasons"])
        return self.http_get(query)


    def list_episodes_for_show_season(self, showId, seasonNumber, start=0, limit=50, sources="all", platform=None):
        query = self.build_query(["show", showId, "episodes", seasonNumber, start, limit, sources, platform])
        return self.http_get(query)


    def fetch_episode_info(self, episodeId):
        query = self.build_query(["episode", episodeId])
        return self.http_get(query)
    

    @staticmethod
    def get_platform(osPlatform):
        if osPlatform in ("linux", "raspberry_pi", "win", "osx", "unknown"):
            return "web"
        if osPlatform in ("ios", "atv2"):
            return "ios"
        if osPlatform in ("android"):
            return "android"
        
    def get_show_images(self, showId):
        query = self.build_query(["show", showId, "images", "all"])
        return self.http_get(query)
    
    

    def get_episode_images(self, episodeId):
        query = self.build_query(["episode", episodeId, "images", "all"])
        return self.http_get(query)

    def get_cache(self):
        return self.__cache
    