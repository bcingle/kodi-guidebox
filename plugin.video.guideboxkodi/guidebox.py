import urllib
import json
from datetime import datetime
from datetime import timedelta
import time
from multiprocessing.pool import ThreadPool
import sys


class Guidebox:
    """
    Interface with the Guidebox API
    https://api.guidebox.com/
    This class provides functions to build queries for accessing many of the features
    provided by the Guidebox API.
    """

    def __init__(self, apiKey, cache, apiVersion = "v1.43", region="US", platform="web", poolSize=50):
        """
        :param apiKey: The API key provided by Guidebox
        :param cache: The cached data, expires after 24 hours. If set to None, an empty cache is used internally.
        It is preferred to pass at least an empty cache object so the external caller has access to the cache
        as it's updated at all times.  Otherwise, you have to call the get_cache() method to get and store
        the cache.
        """
        self.__apiKey = apiKey
        self.__version = apiVersion
        self.__region = region
        self.__baseUrl = "https://api-public.guidebox.com/" + self.__version + "/" + self.__region + "/" + self.__apiKey

        self.__channelTypes = {
            "all": "all",
            "tv": "television",
            "online": "online"
        }
        self.__platform = platform
        self.__pool = ThreadPool(processes=poolSize)
        now = datetime.now()
        if cache is None:
            cache = {}
            
        self.__cache = cache
        
        if "cache_time" not in cache:
            # cache time has not been set
            self.__reset_cache()
        else:
            # cache time previously set
            # check the cache time to see if it is expired
            now = datetime.now()
            yesterday = now - timedelta(hours=24)
            cacheTime = cache["cache_time"]
            try:
                cacheTime = datetime.strptime(cacheTime, "%c")
            except TypeError:
                cacheTime = datetime(*(time.strptime(cacheTime, "%c")[0:6]))
            if cacheTime < yesterday:
                # cache time is expired, clear the cache
                self.__reset_cache()
        
        pass

    def __reset_cache(self):
        now = datetime.now()
        self.__cache["cache_time"] = datetime.strftime(now, '%c')
        self.__cache["channels_by_index"] = {}
        self.__cache["channels_by_id"] = {}
        self.__cache["total_channels"] = -1
        self.__cache["shows_by_id"] = {}
        self.__cache["shows_by_index"] = {}
        self.__cache["total_shows"] = -1
        self.__cache["episodes_by_id"] = {}
        self.__cache["sources_by_id"] = {}
        self.__cache["movies_by_id"] = {}
        self.__cache["movies_by_index"]= {}
        self.__cache["total_movies"] = -1

    def __http_get(self, url):
        print "Guidebox url: " + url
        response = urllib.urlopen(url)
        j = json.load(response)
        #print "Response: " + json.dumps(j)
        return j

    def __build_query(self, query, params=None):
        """
        Build a query for Guidebox API. Base URL for the API is extended with query and params.
        :param query: A list of URL elements, in the form ['search', 'channels', 'title', 'abc', ...]
        :param params: Params in the form {'key': ['value1', 'value2'], ...}
        :return: The query as a string
        """
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
    
    
    
    def __load_more_channels(self, count):
        """
        Load additional channels into the cache
        """
        # check what channels we've fetched
        start = len(self.__cache["channels_by_index"])
        limit = count
        query = self.__build_query(["channels", self.__channelTypes["all"], start, limit])
        results = self.__http_get(query)
        self.__cache["total_channels"] = results["total_results"]
        counter = start
        for result in results["results"]:
            channelId = result["id"]
            self.__cache["channels_by_id"][channelId] = result
            self.__cache["channels_by_index"][counter] = channelId
            result["total_shows"] = -1
            result["shows"] = {}
            counter += 1
    
    def __load_channel_by_id(self, channelId):
        """
        Loads a single channel by ID into the cache
        """
        query = self.__build_query(["channel", channelId])
        results = self.__http_get(query)
        self.__cache["channels_by_id"][channelId] = results
        results["total_shows"] = -1
        results["shows"] = {}
        
    
    def get_channel_page(self, page=1, step=50):
        start = step * (page - 1)
        last = start + step
        print "Getting page " + str(page) + " of " + str(step) + " channels"
        channels = []
        print "Beginning to make sure channels are loaded"
        while (last-1 not in self.__cache["channels_by_index"] and
               (self.__cache["total_channels"] == -1 or 
                self.__cache["total_channels"] > len(self.__cache["channels_by_index"]))):
            # load big number of channels to keep from having to load a lot later
            print "Loading more channels" 
            self.__load_more_channels(50)
        for index in range(start, last):
            if index in self.__cache["channels_by_index"]: 
                channelId = self.__cache["channels_by_index"][index]
                channel = self.__cache["channels_by_id"][channelId]
                channels.append(channel)
        return channels
    
    def get_channel_by_id(self, channelId):
        if not channelId in self.__cache["channels_by_id"]:
            self.__load_channel_by_id(channelId)
        return self.__cache["channels_by_id"][channelId]
    
    def get_channel_count(self):
        return self.__cache["total_channels"]
    
    def __load_show_by_id(self, showId):
        
        query = self.__build_query(["show", showId])
        show = self.__http_get(query)
        if showId not in self.__cache["shows_by_id"]:
            self.__cache["shows_by_id"][showId] = show
        else:
            self.__cache["shows_by_id"][showId].update(show)

        if "seasons" not in show:
            show["seasons"] = {}
        
    def __load_more_shows(self, count, sources="all", platform="web"):
        start = len(self.__cache["shows_by_index"])
        limit = count
        query = self.__build_query(["shows", "all", start, limit, sources, platform])
        results = self.__http_get(query)
        counter = start
        for result in results["results"]:
            showId = result["id"]
            self.__cache["shows_by_id"][showId] = result
            result["seasons"] = {}
            self.__cache["shows_by_index"][counter] = showId
            counter += 1
        
    def __load_more_channel_shows(self, channelId, count, sources="all", platform="web"):
        if channelId not in self.__cache["channels_by_id"]:
            self.__load_channel_by_id(channelId)
        channel = self.__cache["channels_by_id"][channelId]
        start = len(channel["shows"])
        limit = count
        query = self.__build_query(["shows", channel["short_name"], start, limit, sources, platform])
        results = self.__http_get(query)
        channel["total_results"] = results["total_results"]
        counter = start
        for show in results["results"]:
            showId = show["id"]
            self.__cache["shows_by_id"][showId] = show
            channel["shows"][counter] = showId
            show["seasons"] = {}
            counter += 1
    
    def get_channel_shows_page(self, channelId, page=1, step=50):
        start = step * (page - 1)
        last = start + step
        if channelId not in self.__cache["channels_by_id"]:
            self.__load_channel_by_id(channelId)
        channel = self.__cache["channels_by_id"][channelId]
        while (last-1 not in channel["shows"] and 
               (channel["total_shows"] == -1 or 
                len(channel["shows"]) > channel["total_shows"])):
            # load big number of show to keep from having to load a lot later
            self.__load_more_channel_shows(channelId, 50, platform=self.__platform)
        shows = []
        for index in range(start, last):
            if index in channel["shows"]:
                showId = channel["shows"][index]
                show = self.__cache["shows_by_id"][showId]
                shows.append(show)
        return shows
    
    def get_extended_show_info(self, showId):
        if (showId not in self.__cache["shows_by_id"] or 
            "cast" not in  self.__cache["shows_by_id"][showId]):
            self.__load_show_by_id(showId)
        return self.__cache["shows_by_id"][showId]
    
    def get_extended_show_info_batch(self, showIds):
        threads = []
        shows = []
        for showId in showIds:
            async = self.__pool.apply_async(self.get_extended_show_info, (showId,))
            threads.append(async)
        for thread in threads:
            show = thread.get()
            shows.append(show)
        return shows
    
    def get_shows_page(self, page=1, step=50):
        start = step * (page - 1)
        last = start + step
        shows = self.__cache["shows_by_index"]
        while (last-1 not in shows and (self.__cache["total_shows"] == -1 or len(shows) < self.__cache["total_shows"])):
            # load big number of show to keep from having to load a lot later
            self.__load_more_shows(50, platform=self.__platform)
        shows = []
        for index in range(start, last):
            showId = self.__cache["shows_by_index"][index]
            shows.append(self.__cache["shows_by_id"][showId])
        return shows
    
    def get_show_by_id(self, showId):
        if showId not in self.__cache["shows_by_id"]:
            self.__load_show_by_id(showId)
        return self.__cache["shows_by_id"][showId]
    
    def get_show_count_for_channel(self, channelId):
        channel = self.__cache["channels_by_id"][channelId]
        return channel["total_shows"]
    
    def get_total_show_count(self):
        return self.__cache["total_shows"]
    
    
    def __load_show_seasons(self, showId):
        query = self.__build_query(["show", showId, "seasons"])
        results = self.__http_get(query)
        if showId not in self.__cache["shows_by_id"]:
            self.__load_show_by_id(showId)
        show = self.__cache["shows_by_id"][showId]
        for season in results["results"]:
            seasonNumber = season["season_number"]
            season["total_episodes"] = -1
            season["episodes"] = {}
            show["seasons"][int(seasonNumber)] = season
    
    def get_seasons(self, showId):
        if showId not in self.__cache["shows_by_id"]:
            self.__load_show_by_id(showId)
        show = self.__cache["shows_by_id"][showId]
        if not show["seasons"]:
            self.__load_show_seasons(showId)
        seasons = []
        print "Show seasons: "
        print show["seasons"]
        for seasonNum in sorted(show["seasons"]):
            seasons.append(show["seasons"][seasonNum])
        return seasons
    
    def get_season(self, showId, seasonNumber):
        seasons = self.get_seasons(showId)
        for season in seasons:
            if int(season["season_number"]) == int(seasonNumber):
                return season
        print "Season " + str(seasonNumber) + " not found in show " + showId
        print "Dump of seasons: " + json.dumps(seasons)
        return None
    
    def __load_more_episodes(self, showId, seasonNumber, count, sources="all", platform="web"):
        if showId not in self.__cache["shows_by_id"]:
            self.__load_show_by_id(showId)
        show = self.__cache["shows_by_id"][showId]
        if not show["seasons"]:
            self.__load_show_seasons(showId)
        season = show["seasons"][int(seasonNumber)]
        start = len(season["episodes"])
        limit = count
        query = self.__build_query(["show", showId, "episodes", seasonNumber, start, limit, sources, platform])
        results = self.__http_get(query)
        season["total_episodes"] = results["total_results"]
        counter = start
        for episode in results["results"]:
            episodeId = episode["id"]
            season["episodes"][counter] = episodeId
            self.__cache["episodes_by_id"][episodeId] = episode
            counter += 1
    
    def __load_episode_by_id(self, episodeId):
        query = self.__build_query(["episode", episodeId])
        results = self.__http_get(query)
        self.__cache["episodes_by_id"][episodeId] = results

    def get_episode_count_for_season(self, showId, seasonNumber):
        show = self.get_show_by_id(showId)
        seasons = show["seasons"]
        season = seasons[int(seasonNumber)]
        return season["total_episodes"]

    def get_episode_by_id(self, episodeId):
        if episodeId not in self.__cache["episodes_by_id"]:
            self.__load_episode_by_id(episodeId)
        episode = self.__cache["episodes_by_id"][episodeId]
        return episode
        
    def get_episode_page(self, showId, seasonNumber, page=1, step=50):
        season = self.get_season(showId, seasonNumber)
        start = step * (page - 1)
        last = start + step
        while not last-1 in season["episodes"]:
            # load big number of show to keep from having to load a lot later
            self.__load_more_episodes(showId, seasonNumber, 50, platform=self.__platform)
        episodes = []
        for index in range(start, last):
            if index in season["episodes"]:
                episodeId = season["episodes"][index]
                episode = self.__cache["episodes_by_id"][episodeId]
                episodes.append(episode)
        return episodes
    
    def get_extended_episode_info(self, episodeId):
        """
        Get extended episode info, including credits and images
        """
        if episodeId not in self.__cache["episodes_by_id"]:
            self.__load_episode_by_id(episodeId)
        episode = self.__cache["episodes_by_id"][episodeId]
        if "free_web_sources" not in episode:
            self.__load_episode_by_id(episodeId)
        return self.__cache["episodes_by_id"][episodeId]
    
    def get_extended_episode_info_batch(self, episodeIds):
        threads = []
        episodes = []
        for episodeId in episodeIds:
            async = self.__pool.apply_async(self.get_extended_episode_info, (episodeId,))
            threads.append(async)
        for thread in threads:
            episode = thread.get()
            episodes.append(episode)
        return episodes
    
    def __load_movie_by_id(self, movieId):
        if movieId in self.__cache["movies_by_id"]:
            movie = self.__cache["movies_by_id"][movieId]
            if "cast" in movie:
                return
            
        
        query = self.__build_query(["movie", movieId])
        results = self.__http_get(query)
        if movieId in self.__cache["movies_by_id"]:
            movie = self.__cache["movies_by_id"][movieId]
            movie.update(results)
        else:
            self.__cache["movies_by_id"][movieId] = results
    
    def __load_more_movies(self, count=50, sources="all", platform="web"):
        start = len(self.__cache["movies_by_id"])
        limit = count
        query = self.__build_query(["movies", "all", start, limit, sources, platform])
        results = self.__http_get(query)
        self.__cache["total_movies"] = results["total_results"]
        counter = start
        for movie in results["results"]:
            movieId = movie["id"]
            self.__cache["movies_by_id"][movieId] = movie
            self.__cache["movies_by_index"][counter] = movieId
            counter += 1
            
    def __load_movie_images(self, movieId):
        if movieId not in self.__cache["movied_by_id"]:
            self.__load_movie_by_id(movieId)
        movie = self.__cache["movied_by_id"][movieId]
        query = self.__build_query(["movie", movieId, "images", "all"])
        results = self.__http_get(query)
        movie["images"] = results
        
    def __search(self, searchType, searchTerm, exact=True):
        fuzziness = "exact" if exact else "fuzzy"
        # triple URL encode the search term
        searchTerm = urllib.quote_plus(searchTerm, safe='')
        searchTerm = urllib.quote(searchTerm, safe='')
        searchTerm = urllib.quote(searchTerm, safe='')
        if searchType == "show":
            query = self.__build_query(["search", "title", searchTerm, fuzziness])
        else:   
            query = self.__build_query(["search", searchType, "title", searchTerm, fuzziness])
        return self.__http_get(query)
    
    def get_movie_page(self, page=1, step=50):
        start = step * (page - 1)
        last = start + step
        movies = []
        while (last-1 not in self.__cache["movies_by_index"] and 
               (self.__cache["total_movies"] == -1 or 
                self.__cache["total_movies"] > len(self.__cache["movies_by_index"]))):
            # load big number of channels to keep from having to load a lot later
            self.__load_more_movies(50, platform=self.__platform)
        for index in range(start, last):
            if index in self.__cache["movies_by_index"]: 
                movieId = self.__cache["movies_by_index"][index]
                movie = self.__cache["movies_by_id"][movieId]
                movies.append(movie)
        return movies
    
    def get_extended_movie_info(self, movieId):
        self.__load_movie_by_id(movieId)
        return self.__cache["movies_by_id"][movieId]
    
    def get_extended_movie_info_batch(self, movieIds):
        threads = []
        movies = []
        for movieId in movieIds:
            async = self.__pool.apply_async(self.get_extended_movie_info, (movieId,))
            threads.append(async)
        for thread in threads:
            movie = thread.get()
            movies.append(movie)
        return movies
    
    def get_movie_count(self):
        return self.__cache["total_movies"]
    
    def search_channel(self, searchTerm, exact=True):
        return self.__search("channel", searchTerm, exact)
    
    def search_show(self, searchTerm, exact=True):
        return self.__search("show", searchTerm, exact)
    
    def search_movie(self, searchTerm, exact=True):
        return self.__search("movie", searchTerm, exact)

    @staticmethod
    def get_platform(osPlatform):
        if osPlatform in ("linux", "raspberry_pi", "win", "osx", "unknown"):
            return "web"
        if osPlatform in ("ios", "atv2"):
            return "ios"
        if osPlatform in ("android"):
            return "android"

    def get_cache(self):
        return self.__cache
    

    