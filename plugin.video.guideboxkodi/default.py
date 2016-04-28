import sys
import urllib
import json
from addontools import AddonHelper
from guidebox import Guidebox
from themoviedb import TheMovieDB

addonName = "plugin."
chromeLauncherBaseUrl = "plugin://plugin.program.chrome.launcher/"
print "Args: " + ";".join(sys.argv)

addonHelper = AddonHelper(sys.argv)
guidebox = Guidebox(addonHelper.get_setting("guidebox-api-key"), addonHelper.get_user_data("guidebox-cache"))
theMovieDB = TheMovieDB(addonHelper.get_setting("themoviedb-api-key"))

action = addonHelper.get_param("action")

channelId = addonHelper.get_param("channelId")
showId = addonHelper.get_param("showId")
selectedChannel = addonHelper.get_param("channel")
selectedShow = addonHelper.get_param("show")
selectedSeason = addonHelper.get_param("season")
selectedEpisode = addonHelper.get_param("episode")
selectedFolder = addonHelper.get_param("folder")
selectedMovie = addonHelper.get_param("movie")
sourceType = addonHelper.get_param("sourceType")
pageSize = int(addonHelper.get_setting("page-size"))
page = int(addonHelper.get_param("page", 0)) # enable pagination
pageStart = page * pageSize
pageLastItem = pageStart + pageSize

# load favorites
favoriteChannels = addonHelper.get_setting("favorite-channels")
if len(favoriteChannels) > 0:
    favoriteChannels = favoriteChannels.split(",")
else:
    favoriteChannels = []
favoriteShows = addonHelper.get_setting("favorite-shows")
if len(favoriteShows) > 0:
    favoriteShows = favoriteShows.split(",")
else:
    favoriteShows = []


currentPath = addonHelper.get_current_path()
osPlatform = addonHelper.get_platform()
guideboxPlatform = Guidebox.get_platform(osPlatform)

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
    channels = guidebox.list_all_channels(start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", path={"folder": selectedFolder, "page": page-1}, artwork={"thumb": "previous.png"})
    for channel in channels["results"]:
        if channel["id"] in favoriteChannels:
            contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteChannel", "channelId": channel["id"], "callback": currentPath}) + ")")]
        else:
            contextMenu = [("Add to Favorites", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteChannel", "channelId": channel["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(channel["name"], path={"channel": channel["short_name"]}, artwork={"thumb": channel["artwork_208x117"]}, contextMenu=contextMenu, of=len(channels["results"]), overrideContextMenu=True)
    if channels["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", path={"folder": selectedFolder, "page": page+1}, artwork={"thumb": "next.png"})

def build_favorite_channels_folders():
    if not favoriteChannels:
        return
    if page > 0:
        addonHelper.add_folder("Previous", path={"folder": selectedFolder, "page": page-1}, artwork={"thumb": "previous.png"})
    for channelId in favoriteChannels[pageStart:pageLastItem]:
        channel = guidebox.fetch_channel_by_id(channelId)
        contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteChannel", "channelId": channel["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(channel["name"], path={"channel": channel["short_name"]}, artwork={"thumb": channel["artwork_208x117"]}, contextMenu=contextMenu, of=len(favoriteChannels[pageStart:pageLastItem]), overrideContextMenu=True)
    if len(favoriteChannels) > pageLastItem:
        addonHelper.add_folder(label="Next", path={"folder": selectedFolder, "page": page+1}, artwork={"thumb": "next.png"})


def build_show_folders(channelId):
    shows = guidebox.list_shows_for_channel(channelId=channelId, start=pageStart, limit=pageSize, platform=guideboxPlatform)
    if page > 0:
        addonHelper.add_folder("Previous", path={"channel": channelId, "page": page-1}, artwork={"thumb": "previous.png"})
    for show in shows["results"]:
        show = guidebox.fetch_show_info(show["id"])
        if show["id"] in favoriteShows:
            contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteShow", "showId": show["id"], "callback": currentPath}) + ")")]
        else:
            contextMenu = [("Add to Favorites", "RunPlugin(" + addonHelper.build_url({"action": "addFavoriteShow", "showId": show["id"], "callback": currentPath}) + ")")]
        
        listInfo = {}
        artwork = {}
        if "overview" in show:
            listInfo["plot"] = show["overview"]
        if "rating" in show:
            listInfo["rating"] = show["overview"]
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
        addonHelper.add_folder(show["title"], path={"show": show["id"]}, artwork=artwork, contextMenu=contextMenu, of=len(shows["results"]), listInfo=listInfo, mediaType="video", overrideContextMenu=True)
    if shows["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", path={"channel": channelId, "page": page+1}, artwork={"thumb": "next.png"})
        
def build_favorite_shows_folders():
    if not favoriteShows:
        return
    if page > 0:
        addonHelper.add_folder("Previous", path={"folder": selectedFolder, "page": page-1}, thumbnail="previous.png")
    for showId in favoriteShows[pageStart:pageLastItem]:
        show = guidebox.fetch_show_info(showId)
        listInfo = {}
        artwork = {}
        if "overview" in show:
            listInfo["plot"] = show["overview"]
        if "rating" in show:
            listInfo["rating"] = show["overview"]
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
        contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteShow", "showId": show["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(show["title"], path={"show": show["id"]}, artwork=artwork, contextMenu=contextMenu, of=len(favoriteShows[pageStart:pageLastItem]), listInfo=listInfo, mediaType="video", overrideContextMenu=True)
    if len(favoriteShows) > pageLastItem:
        addonHelper.add_folder("Next", path={"folder": selectedFolder, "page": page+1}, artwork={"thumb": "next.png"})


def build_season_folders(showId):
    show = guidebox.fetch_show_info(showId)
    seasons = guidebox.list_seasons_for_show(showId)
    for season in seasons["results"]:
        poster = theMovieDB.get_season_poster(show["themoviedb"], season["season_number"])
        artwork = {}
        if poster:
            artwork["poster"] = poster
        addonHelper.add_folder("Season " + str(season["season_number"]), path={"show": showId, "season": season["season_number"]}, artwork=artwork, of=len(seasons["results"]))


def build_episode_folders(showId, seasonNumber):
    show = guidebox.fetch_show_info(showId)
    episodes = guidebox.list_episodes_for_show_season(showId, seasonNumber, start=pageStart, limit=pageSize, platform=guideboxPlatform)
    if page > 0:
        addonHelper.add_folder("Previous", path={"show": showId, "season": seasonNumber, "page": page-1}, artwork={"thumb": "previous.png"})
    for episode in episodes["results"]:
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
                for castEntry in show["guest_stars"]:
                    cast.append((castEntry["name"], castEntry["character_name"]))
            listInfo["castandrole"] = cast
        addonHelper.add_folder(str(episode["episode_number"]) + " - " + episode["title"], path={"episode": episode["id"]}, artwork=artwork, of=len(episodes), listInfo=listInfo, mediaType="video")
    if episodes["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", path={"show": showId, "season": seasonNumber, "page": page+1}, artwork={"thumb": "next.png"})


def build_source_type_folders(episodeId):
    for id, sourceType in sourceTypeStringCodes.iteritems():
        if sourceType == "choose":
            continue
        addonHelper.add_folder(addonHelper.get_string(id), path={"episode": episodeId, "sourceType": sourceType}, of=len(sourceTypeStringCodes))


def build_episode_links(episodeId, sourceType):
    episodeInfo = guidebox.fetch_episode_info(episodeId)
    if sourceType in ("all", "choose"):
        build_episode_links(episodeId, "free")
        build_episode_links(episodeId, "subscription")
        build_episode_links(episodeId, "tv_everywhere")
        build_episode_links(episodeId, "purchase")
    else:
        sources = episodeInfo[sourceType + "_" + Guidebox.get_platform(osPlatform) + "_sources"]
        for source in sources:
            addonHelper.add_endpoint(source["display_name"], url=build_chrome_launcher_url(source["link"]), of=len(episodeInfo[sourceType + "_" + Guidebox.get_platform(osPlatform) + "_sources"]))


def build_chrome_launcher_url(link):
    return chromeLauncherBaseUrl + "?url=" + urllib.quote(link) + "&mode=showSite&stopPlayback=yes"

def add_favorite_channel(channelId):
    favoriteChannels.append(channelId)
    channelString = ','.join(favoriteChannels)
    print "New favorite channel string: " + channelString
    addonHelper.set_setting("favorite-channels", channelString)
    addonHelper.notify("Favorite channel added")
    #callback = addonHelper.get_param("callback")
    #print "Navigating to the callback location " + callback
    #addonHelper.navigate_now(callback)
    return

def add_favorite_show(showId):
    favoriteShows.append(showId)
    showString = ','.join(favoriteShows)
    print "New favorite show string: " + showString
    addonHelper.set_setting("favorite-shows", showString)
    addonHelper.notify("Favorite show added")
    #callback = addonHelper.get_param("callback")
    #print "Navigating to the callback location " + callback
    #addonHelper.navigate_now(callback)
    return

def remove_favorite_channel(channelId):
    filter(lambda a: a != channelId, favoriteChannels)
    channelString = ','.join(favoriteChannels)
    print "New favorite channel string: " + channelString
    addonHelper.set_setting("favorite-channels", channelString)
    addonHelper.notify("Favorite channel removed")
    #callback = addonHelper.get_param("callback")
    #print "Navigating to the callback location " + callback
    #addonHelper.navigate_now(callback)
    return

def remove_favorite_show(showId):
    filter(lambda a: a != showId, favoriteShows)
    showString = ','.join(favoriteShows)
    print "New favorite show string: " + showString
    addonHelper.set_setting("favorite-shows", showString)
    addonHelper.notify("Favorite show removed")
    #callback = addonHelper.get_param("callback")
    #print "Navigating to the callback location " + callback
    #addonHelper.navigate_now(callback)
    return

def load_root_folders():
    for id, subfolder in rootFolders.iteritems():
        addonHelper.add_folder(subfolder["label"], {"folder": id}, artwork=subfolder["art"])


rootFolders = {
    "browseChannels": {
        "label": "Browse Channels",
        "id": "browseChannels",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_channel_folders()
    },
    # "browseShows": {
    #     "label": "Browse Shows",
    #     "id": "browseShows",
    #     "icon": None,
    #     "thumbnail": None,
    #     "subfolders": [],
    #     "subfolder_builder": lambda: build_channel_folders()
    # },
    # "browseFavorites": {
    #     "label": "Browse Favorites",
    #     "id": "browseFavorites",
    #     "icon": None,
    #     "thumbnail": None,
    #     "subfolders": [],
    #     "subfolder_builder": lambda: {}
    # },
    "favoriteChannels": {
        "label": "Favorite Channels",
        "id": "favoriteChannels",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_channels_folders()
    },
    "favoriteShows": {
        "label": "Favorite Shows",
        "id": "favoriteShows",
        "art": {},
        "subfolders": [],
        "subfolder_builder": lambda: build_favorite_shows_folders()
    }
}

actions = {
    "addFavoriteChannel": lambda: add_favorite_channel(channelId),
    "addFavoriteShow": lambda: add_favorite_show(showId),
    "removeFavoriteChannel": lambda: remove_favorite_channel(channelId),
    "removeFavoriteShow": lambda: remove_favorite_show(showId),
}

if selectedMovie:
    pass

elif sourceType and selectedEpisode:
    # display a list of streaming links for a source
    build_episode_links(selectedEpisode, sourceType)

elif selectedEpisode:
    # display a list of streaming sources for an episode
    if onlySourceType == "choose":
        build_source_type_folders(selectedEpisode)
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
    folder = rootFolders[selectedFolder]
    if not folder["subfolders"]:
        # Some folders require population of subfolders from an API
        folder["subfolder_builder"]()
    else:
        # others are predefined
        for folderName in folder["subfolders"]:
            subfolder = rootFolders[folderName]
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