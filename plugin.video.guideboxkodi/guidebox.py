import urllib
import json
from addontools import AddonHelper


class Guidebox:
    """
    Interface with the Guidebox API
    https://api.guidebox.com/
    This class provides functions to build queries for accessing many of the features
    provided by the Guidebox API.
    """

    __apiKey = "rKt8jl2G47wjhqAVXtQcAYirK8AnYtw6"
    __version = "v1.43"
    __region = "US"
    __baseUrl = "https://api-public.guidebox.com/" + __version + "/" + __region + "/" + __apiKey

    __channelTypes = {
        "all": "all",
        "tv": "television",
        "online": "online"
    }

    def __init__(self):
        pass

    @staticmethod
    def http_get(url):
        response = urllib.urlopen(url)
        j = json.load(response)
        return j

    @staticmethod
    def build_query(query, params=None):
        """
        Build a query for Guidebox API. Base URL for the API is extended with query and params.
        :param query: A list of URL elements, in the form ['search', 'channels', 'title', 'abc', ...]
        :param params: Params in the form {'key': ['value1', 'value2'], ...}
        :return: The query as a string
        """
        url = Guidebox.__baseUrl
        url = ["/".join(str(item) for item in [Guidebox.__baseUrl] + query)]
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

    @staticmethod
    def list_tv_channels(start=0, limit=50):
        """
        List all TV channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return Guidebox.list_channels_by_type(Guidebox.__channelTypes["tv"], start, limit)

    @staticmethod
    def list_online_channels(start=0, limit=50):
        """
        List all online channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return Guidebox.list_channels_by_type(Guidebox.__channelTypes["online"], start, limit)

    @staticmethod
    def list_all_channels(start=0, limit=50):
        """
        List all TV and Online channels
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        return Guidebox.list_channels_by_type(Guidebox.__channelTypes["all"], start, limit)

    @staticmethod
    def list_channels_by_type(type, start=0, limit=50):
        """
        List all channels of a specific type\
        :param type: Type to load, one of self.channelTypes
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :return: A list of channels as defined by the Guidebox API
        """
        query = Guidebox.build_query(["channels", type, start, limit])
        return Guidebox.http_get(query)

    @staticmethod
    def search_channel(query, start=0, limit=50, fuzzy=False):
        """
        Search for a channel by name
        :param query: Search term
        :param start: Optional start index for pagination
        :param limit: Optional result limit for pagination
        :param fuzzy: Whether to search for exact phrase
        :return:
        """
        query = Guidebox.build_query(["search", "channel", "title", query, start, limit])
        return Guidebox.http_get(query)

    @staticmethod
    def list_shows_for_channel(channelId, start=0, limit=50, sources="all", platform=None):
        if platform is None:
            platform = Guidebox.get_platform()
        query = Guidebox.build_query(["shows", channelId, start, limit, sources, platform])
        return Guidebox.http_get(query)


    @staticmethod
    def list_seasons_for_show(showId):
        query = Guidebox.build_query(["show", showId, "seasons"])
        return Guidebox.http_get(query)


    @staticmethod
    def list_episodes_for_show_season(showId, seasonNumber, start=0, limit=50, sources="all", platform=None):
        if platform is None:
            platform = Guidebox.get_platform()
        query = Guidebox.build_query(["show", showId, "episodes", seasonNumber, start, limit, sources, platform])
        return Guidebox.http_get(query)


    @staticmethod
    def list_episode_info(episodeId):
        query = Guidebox.build_query(["episode", episodeId])
        return Guidebox.http_get(query)


    @staticmethod
    def get_platform():
        if AddonHelper.is_platform('Android'):
            return 'android'
        elif AddonHelper.is_platform('IOS'):
            return 'ios'
        else:
            return 'web'