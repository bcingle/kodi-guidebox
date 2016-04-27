import urllib
import json

class TheMovieDB :
    
    apiPath = "https://api.themoviedb.org/"
    apiVersion = "3"
    
    def __init__(self, apiKey):
        self.__apiKey = apiKey
        self.__apiPath = TheMovieDB.apiPath + TheMovieDB.apiVersion
        self.__apiKeyParam = urllib.urlencode({"api_key": self.__apiKey})
        self.__imageBaseUrl = None
        # load config only if required
        #self.load_config()
    
    def load_config(self):
        results = self.http_get_json("%s/configuration?%s" % (self.__apiPath, self.__apiKeyParam))
        self.__imageBaseUrl= results["images"]["secure_base_url"]
        
    @staticmethod
    def http_get_json(url):
        print "TheMovieDB URL: " + url
        response = urllib.urlopen(url)
        print response
        j = json.load(response)
        return j

    def get_season_poster(self, showId, seasonNumber):
        query = "%s/tv/%s/season/%s/images?%s" % (self.__apiPath, showId, seasonNumber, self.__apiKeyParam)
        results = self.http_get_json(query)
        # sometimes there is no poster, in which case we have nothing to return
        if not results["posters"] or len(results["posters"]) == 0:
            return None
        # if image base url hasn't been loaded, do it now
        if not self.__imageBaseUrl:
            self.load_config()
        return "%soriginal%s" % (self.__imageBaseUrl, results["posters"][0]["file_path"])
        
    def get_episode_poster(self, showId, seasonNumber, episodeNumber):
        query = "%s/tv/%s/season/%s/episode/%s/images?%s" % (self.__apiPath, showId, seasonNumber, episodeNumber, self.__apiKeyParam)
        results = self.http_get_json(query)
        if not results["stills"] or len(results["stills"]) == 0:
            return None
        # if image base url hasn't been loaded, do it now
        if not self.__imageBaseUrl:
            self.load_config()
        return "%soriginal%s" % (self.__imageBaseUrl, results["stills"][0]["file_path"])