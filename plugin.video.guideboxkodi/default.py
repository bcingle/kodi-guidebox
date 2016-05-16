import sys
import urllib
import json
from addontools import AddonHelper
from guidebox import Guidebox
from themoviedb import TheMovieDB


chromeLauncherBaseUrl = "plugin://plugin.program.chrome.launcher/"
print "Args: " + ";".join(sys.argv)

addonHelper = AddonHelper(sys.argv)
currentPath = addonHelper.get_current_path()
osPlatform = addonHelper.get_platform()
guideboxPlatform = Guidebox.get_platform(osPlatform)
# consider redirecting to settings dialog if API keys are not provided.  If not, cryptic errors will be thrown.
guideboxApiKey = addonHelper.get_setting("guidebox-api-key")
if not guideboxApiKey or guideboxApiKey == "":
    addonHelper.notify("Please set Guidebox API key")
    addonHelper.open_addon_settings()
    sys.exit("Please set Guidebox API key")
guidebox = Guidebox(guideboxApiKey, addonHelper.get_user_data("guidebox-cache"), platform=guideboxPlatform )
theMovieDB = TheMovieDB(addonHelper.get_setting("themoviedb-api-key"))

action = addonHelper.get_param("action")

channelId = addonHelper.get_param("channelId")
showId = addonHelper.get_param("showId")
episodeId = addonHelper.get_param("episodeId")
movieId = addonHelper.get_param("movieId")
searchTerm = addonHelper.get_param("search_term")
selectedChannel = addonHelper.get_param("channel")
selectedShow = addonHelper.get_param("show")
selectedSeason = addonHelper.get_param("season")
selectedEpisode = addonHelper.get_param("episode")
selectedFolder = addonHelper.get_param("folder")
selectedMovie = addonHelper.get_param("movie")
sourceType = addonHelper.get_param("sourceType")
pageSize = int(addonHelper.get_setting("page-size"))
page = int(addonHelper.get_param("page", 1)) # enable pagination
pageStart = (page-1) * pageSize
pageLastItem = pageStart + pageSize

# load favorites
favoriteMovies = addonHelper.get_user_data("saved_movies")
if favoriteMovies is None:
    favoriteMovies = []
    addonHelper.set_user_data("saved_movies", favoriteMovies)
favoriteChannels = addonHelper.get_user_data("saved_channels")
if favoriteChannels is None:
    favoriteChannels = []
    addonHelper.set_user_data("saved_channels", favoriteChannels)
favoriteShows = addonHelper.get_user_data("saved_shows")
if favoriteShows is None:
    favoriteShows = []
    addonHelper.set_user_data("saved_shows", favoriteShows)
favoriteEpisodes = addonHelper.get_user_data("saved-episodes")
if favoriteEpisodes is None:
    favoriteEpisodes = []
    addonHelper.set_user_data("saved_episodes", favoriteEpisodes)

sourceTypeStringCodes = {
    "32003": "choose",
    "32004": "free",
    "32005": "subscription",
    "32006": "tv_everywhere",
    "32007": "purchase"
}

# Settings for a selection return the ordinal number which needs to be mapped to a key in the string codes dictionary
sourceTypeSettingCodes = ["32003", "32004", "32005", "32006", "32007"]
print addonHelper.get_setting("only-source")
onlySourceType = sourceTypeStringCodes[sourceTypeSettingCodes[int(addonHelper.get_setting("only-source"))]]
print "This is the Source setting: " + onlySourceType

def build_channel_folders():
    print "Fetching a channel page"
    channels = guidebox.get_channel_page(page, pageSize)
    channelCount = guidebox.get_channel_count()
    for channel in channels:
        add_channel_folder(channel["id"])
    if channelCount == -1 or channelCount > pageLastItem:
        addonHelper.add_folder("More", path={"folder": selectedFolder, "page": page+1}, artwork={"thumb": "next.png"})

def build_favorite_channels_folders():
    if not favoriteChannels:
        return
    for channelId in favoriteChannels:
        add_channel_folder(channelId)

def add_channel_folder(channelId):
    print "Adding channel with ID " + str(channelId)
    channel = guidebox.get_channel_by_id(channelId)
    if channel["id"] in favoriteChannels:
        contextMenu = [("Remove from Favorite Channels", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteChannel", "channelId": channelId}) + ")")]
    else:
        contextMenu = [("Add to Favorite Channels", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteChannel", "channelId": channelId}) + ")")]
    addonHelper.add_folder(channel["name"], path={"channel": channel["id"]}, artwork={"thumb": channel["artwork_208x117"]}, contextMenu=contextMenu, overrideContextMenu=True)

def build_movie_folders():
    movies = guidebox.get_movie_page(page, pageSize)
    movieIds = []
    for movie in movies:
        movieIds.append(movie["id"])
    movies = guidebox.get_extended_movie_info_batch(movieIds)
    movieCount = guidebox.get_movie_count()
    for movie in movies:
        add_movie_folder(movie["id"])
    if movieCount == -1 or movieCount > pageLastItem:
        addonHelper.add_folder("Next", path={"channel": channelId, "page": page+1}, artwork={"thumb": "next.png"})
        
def build_favorite_movie_folders():
    if not favoriteMovies:
        return
    movies = guidebox.get_extended_movie_info_batch(favoriteMovies)
    for movie in movies:
        add_movie_folder(movie["id"])
         
def add_movie_folder(movieId):
    movie = guidebox.get_extended_movie_info(movieId)
    if movie["id"] in favoriteMovies:
        contextMenu = [("Remove from Favorite Movies", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteMovie", "movieId": movie["id"], "callback": currentPath}) + ")")]
    else:
        contextMenu = [("Add to Favorite Movies", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteMovie", "movieId": movie["id"], "callback": currentPath}) + ")")]
    images = theMovieDB.get_movie_images(movie["themoviedb"])
    listInfo = {}
    artwork = {}
    if "overview" in movie:
        listInfo["plot"] = movie["overview"]
    if "rating" in movie:
        listInfo["mpaa"] = movie["rating"]
    if "release_date" in movie:
        listInfo["premiered"] = movie["release_date"]
        listInfo["year"] = movie["release_year"]
    if "genres" in movie and len(movie["genres"]) > 0:
        listInfo["genre"] = movie["genres"][0]["title"]
    if "backdrop" in images:
        artwork["background"] = images["backdrop"]
        artwork["landscape"] = images["backdrop"]
        artwork["fanart"] = images["backdrop"]
    if "poster" in images:
        artwork["poster"] = images["poster"]
    if "cast" in movie:
        cast = []
        for castEntry in movie["cast"]:
            cast.append((castEntry["name"], castEntry["character_name"]))
        listInfo["castandrole"] = cast
    if "duration" in movie:
        listInfo["duration"] = int(movie["duration"])
    listInfo["tvshowtitle"] = movie["title"]
    listInfo["mediatype"] = "movie"
    addonHelper.add_folder(movie["title"], path={"movie": movie["id"]}, artwork=artwork, contextMenu=contextMenu, listInfo=listInfo, mediaType="video", overrideContextMenu=True)


def build_show_folders(channelId):
    if channelId is None:
        shows = guidebox.get_shows_page(page, pageSize)
        showCount = guidebox.get_total_show_count()
        pathKey = "folder"
        pathValue = "browseShows"
    else:
        shows = guidebox.get_channel_shows_page(channelId, page, pageSize)
        showCount = guidebox.get_show_count_for_channel(channelId)
        pathKey = "channel"
        pathValue = channelId
    showIds = []
    for show in shows:
        showIds.append(show["id"])
    shows = guidebox.get_extended_show_info_batch(showIds)
    for show in shows:
        add_show_folder(show["id"])
    if showCount == -1 or showCount > pageLastItem:
        addonHelper.add_folder("More", path={pathKey: pathValue, "page": page+1}, artwork={"thumb": "next.png"})
        
def build_favorite_shows_folders():
    if not favoriteShows:
        return
    print "Attempting to multithread the obtaining of show info"
    shows = guidebox.get_extended_show_info_batch(favoriteShows)
    for showId in shows:
        add_show_folder(showId)

def add_show_folder(showId):
    show = guidebox.get_extended_show_info(showId)
    listInfo = {}
    artwork = {}
    if "overview" in show:
        listInfo["plot"] = show["overview"]
    #if "rating" in show:
    #    listInfo["rating"] = show["overview"]
    if "rating" in show:
        listInfo["mpaa"] = show["rating"]
    if "first_aired" in show:
        listInfo["premiered"] = show["first_aired"]
        listInfo["year"] = str(show["first_aired"])[0:4]
    if "genres" in show and len(show["genres"]) > 0:
        listInfo["genre"] = show["genres"][0]["title"]
    if "fanart" in show:
        artwork["background"] = show["fanart"]
        artwork["landscape"] = show["fanart"]
        artwork["fanart"] = show["fanart"]
    if "banner" in show:
        artwork["banner"] = show["banner"]
    if "artwork_608x342" in show:
        artwork["thumb"] = show["artwork_608x342"]
    if "poster" in show:
        artwork["poster"] = show["poster"]
    if "cast" in show:
        cast = []
        for castEntry in show["cast"]:
            cast.append((castEntry["name"], castEntry["character_name"]))
        listInfo["castandrole"] = cast
    if "runtime" in show:
        listInfo["duration"] = int(show["runtime"]) * 60 # guidebox runtimes are in minutes instead of seconds
    if "status" in show:
        listInfo["status"] = show["status"]
    listInfo["tvshowtitle"] = show["title"]
    listInfo["mediatype"] = "tvshow"
    if showId in favoriteShows:
        contextMenu = [("Remove from Favorite Shows", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteShow", "showId": show["id"]}) + ")")]
    else:
        contextMenu = [("Add to Favorites Shows", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteShow", "showId": show["id"]}) + ")")]
    addonHelper.add_folder(show["title"], path={"show": show["id"]}, artwork=artwork, contextMenu=contextMenu, listInfo=listInfo, mediaType="video", overrideContextMenu=True)


def build_season_folders(showId):
    show = guidebox.get_show_by_id(showId)
    seasons = guidebox.get_seasons(showId)
    print "Contents of show object: " + json.dumps(show)
    print "Contents of the season object: " + json.dumps(seasons)
    for season in seasons:
        print "A single season: " + json.dumps(season)
        poster = theMovieDB.get_season_poster(show["themoviedb"], season["season_number"])
        listInfo = {}
        artwork = {}
        if poster:
            artwork["poster"] = poster
        elif "poster" in show:
            artwork["poster"] = show["poster"]
        if "fanart" in show:
            artwork["fanart"] = show["fanart"]
        if "overview" in show:
            listInfo["plot"] = show["overview"]
        #if "rating" in show:
        #    listInfo["rating"] = show["overview"]
        if "rating" in show:
            listInfo["mpaa"] = show["rating"]
        if "first_aired" in show:
            listInfo["premiered"] = show["first_aired"]
            listInfo["year"] = show["first_aired"][0:4]
        if "genres" in show and len(show["genres"]) > 0:
            listInfo["genre"] = show["genres"][0]["title"]
        if "fanart" in show:
            artwork["background"] = show["fanart"]
            artwork["landscape"] = show["fanart"]
            artwork["fanart"] = show["fanart"]
        if "banner" in show:
            artwork["banner"] = show["banner"]
        if "artwork_608x342" in show:
            artwork["thumb"] = show["artwork_608x342"]
        if "cast" in show:
            cast = []
            for castEntry in show["cast"]:
                cast.append((castEntry["name"], castEntry["character_name"]))
            listInfo["castandrole"] = cast
        if "runtime" in show:
            listInfo["duration"] = int(show["runtime"]) * 60 # guidebox runtimes are in minutes instead of seconds
        if "status" in show:
            listInfo["status"] = show["status"]
        listInfo["tvshowtitle"] = show["title"]
        listInfo["season"] = season["season_number"]
        listInfo["mediatype"] = "season"
        addonHelper.add_folder("Season " + str(season["season_number"]), path={"show": showId, "season": season["season_number"]}, artwork=artwork, listInfo=listInfo, mediaType="video")


def build_episode_folders(showId, seasonNumber):
    show = guidebox.get_extended_show_info(showId)
    episodes = guidebox.get_episode_page(showId, seasonNumber, page, pageSize)
    episodeIds = []
    for episode in episodes:
        episodeIds.append(episode["id"])
    episodes = guidebox.get_extended_episode_info_batch(episodeIds)
    episodeCount = guidebox.get_episode_count_for_season(showId, seasonNumber)
    print "Total episode count for this season: " + str(episodeCount)
    print "pageLastItem: " + str(pageLastItem)
    for episode in episodes:
        add_episode_folder(show, episode) 
    if episodeCount == -1 or episodeCount > pageLastItem:
        addonHelper.add_folder("Next", path={"show": showId, "season": seasonNumber, "page": page+1}, artwork={"thumb": "next.png"})

def build_favorite_episode_folders():
    episodes = guidebox.get_extended_episode_info_batch(favoriteEpisodes)
    for episode in episodes:
        show = guidebox.get_extended_show_info(episode["show_id"])
        add_episode_folder(show, episode)
    
def add_episode_folder(show, episode):
    episode = guidebox.get_extended_episode_info(episode["id"])
    # episode = guidebox.fetch_episode_info(episode["id"]) # get more information (not necessary because we only get thumbs anyway)
    listInfo = {}
    artwork = {}
    if "fanart" in show:
        artwork["background"] = show["fanart"]
        artwork["landscape"] = show["fanart"]
        artwork["fanart"] = show["fanart"]
    if "banner" in show:
        artwork["banner"] = show["banner"]
#        if "poster" in show:
#            artwork["poster"] = show["poster"]
    if "rating" in show:
        listInfo["mpaa"] = show["rating"]
    if "thumbnail_608x342" in episode:
        artwork["thumb"] = episode["thumbnail_608x342"]
    if "season_number" in episode:
        listInfo["season"] = episode["season_number"]
    if "episode_number" in episode:
        listInfo["episode"] = episode["episode_number"]
    if "first_aired" in episode:
        listInfo["premiered"] = episode["first_aired"]
    if "overview" in episode:
        listInfo["plot"] = episode["overview"]
    if "cast" in show:
        cast = []
        for castEntry in show["cast"]:
            cast.append((castEntry["name"], castEntry["character_name"]))
        if "guest_stars" in episode:
            for castEntry in episode["guest_stars"]:
                cast.append((castEntry["name"], castEntry["character_name"]))
        listInfo["castandrole"] = cast
    listInfo["mediatype"] = "episode"
    if "duration" in episode:
        listInfo["duration"] = episode["duration"]
    if showId in favoriteShows:
        contextMenu = [("Remove from Favorite Episodes", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteEpisode", "episodeId": episode["id"]}) + ")")]
    else:
        contextMenu = [("Add to Favorites Episodes", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteEpisode", "episodeId": episode["id"]}) + ")")]
    addonHelper.add_folder(str(episode["episode_number"]) + " - " + episode["title"], path={"episode": episode["id"]}, artwork=artwork, contextMenu=contextMenu, listInfo=listInfo, mediaType="video")

def build_episode_source_type_folders(episodeId):
    for key, sourceType in sourceTypeStringCodes.iteritems():
        if sourceType == "choose":
            continue
        addonHelper.add_folder(addonHelper.get_string(key), path={"episode": episodeId, "sourceType": sourceType})


def build_episode_links(episodeId, sourceType):
    episodeInfo = guidebox.get_extended_episode_info(episodeId)
    if sourceType in ("all", "choose"):
        build_episode_links(episodeId, "free")
        build_episode_links(episodeId, "subscription")
        build_episode_links(episodeId, "tv_everywhere")
        build_episode_links(episodeId, "purchase")
    else:
        sources = episodeInfo[sourceType + "_" + guideboxPlatform + "_sources"]
        for source in sources:
            addonHelper.add_endpoint(source["display_name"], url=build_chrome_launcher_url(source["link"]))

def build_movie_source_type_folders(episodeId):
    for key, sourceType in sourceTypeStringCodes.iteritems():
        if sourceType == "choose":
            continue
        addonHelper.add_folder(addonHelper.get_string(key), path={"movie": episodeId, "sourceType": sourceType})

def build_movie_links(movieId, sourceType):
    movie = guidebox.get_extended_movie_info(movieId)
    if sourceType in ("all", "choose"):
        build_episode_links(movieId, "free")
        build_episode_links(movieId, "subscription")
        build_episode_links(movieId, "tv_everywhere")
        build_episode_links(movieId, "purchase")
    else:
        sources = movie[sourceType + "_" + guideboxPlatform + "_sources"]
        for source in sources:
            addonHelper.add_endpoint(source["display_name"], url=build_chrome_launcher_url(source["link"]))

def build_chrome_launcher_url(link):
    return chromeLauncherBaseUrl + "?url=" + urllib.quote(link) + "&mode=showSite&stopPlayback=yes"

def add_favorite_channel(channelId):
    favoriteChannels = addonHelper.get_user_data("saved_channels")
    favoriteChannels.append(int(channelId))
    addonHelper.set_user_data("saved_channels", favoriteChannels)
    addonHelper.notify("Favorite channel added")
    addonHelper.refresh_current_path()
    return

def add_favorite_show(showId):
    favoriteShows = addonHelper.get_user_data("saved_shows")
    favoriteShows.append(int(showId))
    addonHelper.set_user_data("saved_shows", favoriteShows)
    addonHelper.notify("Favorite show added")
    addonHelper.refresh_current_path()
    return

def add_favorite_episode(episodeId):
    favoriteEpisodes = addonHelper.get_user_data("saved_episodes")
    favoriteEpisodes.append(int(episodeId))
    addonHelper.set_user_data("saved_episodes", favoriteEpisodes)
    addonHelper.notify("Favorite episode added")
    addonHelper.refresh_current_path()
    return

def add_saved_movie(movieId):
    favoriteMovies = addonHelper.get_user_data("saved_movies")
    favoriteMovies.append(int(movieId))
    addonHelper.set_user_data("saved_movies", favoriteMovies)
    addonHelper.notify("Favorite movie added")
    addonHelper.refresh_current_path()

def remove_favorite_channel(channelId):
    favoriteChannels = addonHelper.get_user_data("saved_channels")
    favoriteChannels = filter(lambda a: a != int(channelId), favoriteChannels)
    addonHelper.set_user_data("saved_channels", favoriteChannels)
    addonHelper.notify("Favorite channel removed")
    addonHelper.refresh_current_path()
    return

def remove_favorite_show(showId):
    favoriteShows = addonHelper.get_user_data("saved_shows")
    favoriteShows = filter(lambda a: a != int(showId), favoriteShows)
    addonHelper.set_user_data("saved_shows", favoriteShows)
    addonHelper.notify("Favorite shows removed")
    addonHelper.refresh_current_path()
    return

def remove_favorite_episode(episodeId):
    favoriteEpisodes = addonHelper.get_user_data("saved_episodes")
    favoriteEpisodes = filter(lambda a: a != int(episodeId), favoriteEpisodes)
    addonHelper.set_user_data("saved_episodes", favoriteEpisodes)
    addonHelper.notify("Favorite episode removed")
    addonHelper.refresh_current_path()
    return

def remove_saved_movie(movieId):
    favoriteMovies = addonHelper.get_user_data("saved_movies")
    favoriteMovies = filter(lambda a: a != int(movieId), favoriteMovies)
    addonHelper.set_user_data("saved_movies", favoriteMovies)
    addonHelper.notify("Favorite movie removed")
    addonHelper.refresh_current_path()
    
def search_movies(searchTerm=None):
    if searchTerm is None:
        searchTerm = addonHelper.get_user_input_alphanum("Enter search term")
        exact = addonHelper.get_user_input_yesno("Search fuzziness", "Exact results?")
    movies = guidebox.search_movie(searchTerm, exact)["results"]
    movieIds = []
    for movie in movies:
        movieIds.append(movie["id"])
    movies = guidebox.get_extended_movie_info_batch(movieIds)
#     if page > 1:
#         addonHelper.add_folder("Previous", path={"action": action, "search_term": searchTerm, "page": page-1}, artwork={"thumb": "previous.png"})
    for movie in movies:
        add_movie_folder(movie["id"])
#     if len(movies) >= pageSize:
#         addonHelper.add_folder("Next", path={"action": action, "search_term": searchTerm, "page": page+1}, artwork={"thumb": "next.png"})
    return

def search_channels(searchTerm=None):
    if searchTerm is None:
        searchTerm = addonHelper.get_user_input_alphanum("Enter search term")
        exact = addonHelper.get_user_input_yesno("Search fuzziness", "Exact results?")
    channels = guidebox.search_channel(searchTerm, exact)["results"]
#     if page > 1:
#         addonHelper.add_folder("Previous", path={"action": action, "search_term": searchTerm, "page": page-1}, artwork={"thumb": "previous.png"})
    for channel in channels:
        add_channel_folder(channel["id"])
#     if len(channels) >= pageSize:
#         addonHelper.add_folder("Next", path={"action": action, "search_term": searchTerm, "page": page+1}, artwork={"thumb": "next.png"})
    return

def search_shows(searchTerm=None):
    if searchTerm is None:
        searchTerm = addonHelper.get_user_input_alphanum("Enter search term")
        exact = addonHelper.get_user_input_yesno("Search fuzziness", "Exact results?")
    shows = guidebox.search_show(searchTerm, exact)["results"]
    showIds = []
    for show in shows:
        showIds.append(show["id"])
    shows = guidebox.get_extended_show_info_batch(showIds)
#     if page > 1:
#         addonHelper.add_folder("Previous", path={"action": action, "search_term": searchTerm, "page": page-1}, artwork={"thumb": "previous.png"})
    for show in shows:
        add_show_folder(show["id"])
#     if len(shows) >= pageSize:
#         addonHelper.add_folder("Next", path={"action": action, "search_term": searchTerm, "page": page+1}, artwork={"thumb": "next.png"})
    return

def load_root_folders():
    for folderName in rootFolders:
        folder = folders[folderName]
        addonHelper.add_folder(folder["label"], {"folder": folderName}, artwork=folder["art"])


rootFolders = ["browseChannels", "browseShows", "browseMovies", "favoriteChannels", "favoriteShows", "favoriteEpisodes", "favoriteMovies", "search"]

folders = {
    "browseChannels": {
        "label": addonHelper.get_string("32023"),
        "id": "browseChannels",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_channel_folders()
    },
    "browseShows": {
        "label": addonHelper.get_string("32024"),
        "id": "browseShows",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_show_folders(None)
    },
    "browseMovies": {
        "label": addonHelper.get_string("32025"),
        "id": "browseMovies",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_movie_folders()
    },
    "favoriteChannels": {
        "label": addonHelper.get_string("32021"),
        "id": "favoriteChannels",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_channels_folders()
    },
    "favoriteShows": {
        "label": addonHelper.get_string("32022"),
        "id": "favoriteShows",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_shows_folders()
    },
    "favoriteEpisodes": {
        "label": addonHelper.get_string("32031"),
        "id": "favoriteEpisodes",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_episode_folders()
    },
    "favoriteMovies": {
        "label": addonHelper.get_string("32026"),
        "id": "favoriteMovies",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_movie_folders()
    },
    "search": {
        "label": addonHelper.get_string("32027"),
        "id": "search",
        "art": {},
        "subfolders": ["searchMovies", "searchChannels", "searchShows"]
    },
   "searchMovies": {
        "label": addonHelper.get_string("32028"),
        "id": "searchMovies",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: search_movies()
    },
    "searchChannels": {
        "label": addonHelper.get_string("32029"),
        "id": "searchChannels",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: search_channels()
    },
    "searchShows": {
        "label": addonHelper.get_string("32030"),
        "id": "searchShows",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: search_shows()
    }
           
}

actions = {
    "addFavoriteChannel": lambda: add_favorite_channel(channelId),
    "addFavoriteShow": lambda: add_favorite_show(showId),
    "addFavoriteEpisode": lambda: add_favorite_episode(episodeId),
    "addFavoriteMovie": lambda: add_saved_movie(movieId),
    "removeFavoriteChannel": lambda: remove_favorite_channel(channelId),
    "removeFavoriteShow": lambda: remove_favorite_show(showId),
    "removeFavoriteEpisode": lambda: remove_favorite_episode(episodeId),
    "removeFavoriteMovie": lambda: remove_saved_movie(movieId),
    "searchMovies": lambda: search_movies(searchTerm),
    "searchChannels": lambda: search_channels(searchTerm),
    "searchShows": lambda: search_shows(searchTerm)
}

if sourceType and selectedMovie:
    # display a list of streaming links for a movie
    build_movie_links(selectedMovie, sourceType)
    pass

elif selectedMovie:
    # display a list of streaming sources for a movie
    if onlySourceType == "choose":
        build_movie_source_type_folders(selectedMovie)
    else:
        build_movie_links(selectedMovie, onlySourceType)

elif sourceType and selectedEpisode:
    # display a list of streaming links for a source
    build_episode_links(selectedEpisode, sourceType)

elif selectedEpisode:
    # display a list of streaming sources for an episode
    if onlySourceType == "choose":
        build_episode_source_type_folders(selectedEpisode)
    else:
        build_episode_links(selectedEpisode, onlySourceType)

elif selectedSeason and selectedShow:
    # if season is selected, show must also be selected
    # display the episodes for a season
    build_episode_folders(selectedShow, selectedSeason)
#    addonHelper.set_view_mode("508")
    pass

elif selectedShow:
    # display the seasons for a show
    build_season_folders(selectedShow)
    pass

elif selectedChannel:
    # display the shows for a channel
    build_show_folders(selectedChannel)
    addonHelper.set_view_mode("508")
    pass

elif selectedFolder:
    # populate the selected folder
    folder = folders[selectedFolder]
    if not folder["subfolders"]:
        # Some folders require population of subfolders from an API
        folder["subfolder_builder"]()
    else:
        # others are predefined
        for folderName in folder["subfolders"]:
            subfolder = folders[folderName]
            addonHelper.add_folder(subfolder["label"], path={"folder": folderName}, artwork=subfolder["art"])
    pass
elif action and action in actions:
    print "Executing action " + action
    actions[action]()
else:
    # show the root folder
    load_root_folders()

addonHelper.end()
addonHelper.set_user_data("guidebox-cache", guidebox.get_cache())

