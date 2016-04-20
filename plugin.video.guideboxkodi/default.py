import sys
import urllib
import json
from addontools import AddonHelper
from guidebox import Guidebox

addonName = "plugin."
chromeLauncherBaseUrl = "plugin://plugin.program.chrome.launcher/"
print "Args: " + ";".join(sys.argv)

addonHelper = AddonHelper(sys.argv)
guidebox = Guidebox(addonHelper.get_setting("guidebox-api-key"))

action = addonHelper.get_param("action")

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
favoriteChannels = addonHelper.get_setting("favorite-channels").split(",")
favoriteShows = addonHelper.get_setting("favorite-shows").split(",")
currentPath = addonHelper.get_current_path()


def build_channel_folders():
    channels = guidebox.list_all_channels(start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", {"folder": selectedFolder, "page": page-1}, thumbnail="previous.png")
    for channel in channels["results"]:
        if channel["id"] in favoriteChannels:
            contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteChannel", "channelId": channel["id"], "callback": currentPath}) + ")")]
        else:
            contextMenu = [("Add to Favorites", "RunPlugin(" + addonHelper.build_url({"addFavoriteChannel": channel["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(channel["name"], {"channel": channel["short_name"]}, None, channel["artwork_208x117"], contextMenu=contextMenu)
    if channels["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", {"folder": selectedFolder, "page": page+1}, thumbnail="next.png")

def build_favorite_channels_folders():
    if page > 0:
        addonHelper.add_folder("Previous", {"folder": selectedFolder, "page": page-1}, thumbnail="previous.png")
    for channelId in favoriteChannels[pageStart:pageLastItem]:
        channel = guidebox.fetch_channel_by_id(channelId)
        contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"action": "removeFavoriteChannel", "channelId": channel["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(channel["name"], {"channel": channel["short_name"]}, None, channel["artwork_208x117"], contextMenu=contextMenu)
    if len(favoriteChannels) > pageLastItem:
        addonHelper.add_folder("Next", {"folder": selectedFolder, "page": page+1}, thumbnail="next.png")


def build_show_folders(channelId):
    shows = guidebox.list_shows_for_channel(channelId=channelId, start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", {"channel": channelId, "page": page-1}, thumbnail="previous.png")
    for show in shows["results"]:
        if show["id"] in favoriteShows:
            contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"removeFavoriteShow": show["id"], "callback": currentPath}) + ")")]
        else:
            contextMenu = [("Add to Favorites", "RunPlugin(" + addonHelper.build_url({"addFavoriteCShow": show["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(show["title"], {"show": show["id"]}, thumbnail=show["artwork_208x117"], contextMenu=contextMenu)
    if shows["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", {"channel": channelId, "page": page+1}, thumbnail="next.png")
        
def build_favorite_shows_folders():
    if page > 0:
        addonHelper.add_folder("Previous", {"folder": selectedFolder, "page": page-1}, thumbnail="previous.png")
    for showId in favoriteShows[pageStart:pageLastItem]:
        show = guidebox.fetch_show_info(showId)
        print json.dumps(show)
        contextMenu = [("Remove from Favorites", "RunPlugin(" + addonHelper.build_url({"removeFavoriteShow": show["id"], "callback": currentPath}) + ")")]
        addonHelper.add_folder(show["title"], {"show": show["id"]}, thumbnail=show["artwork_208x117"], contextMenu=contextMenu)
    if len(favoriteShows) > pageLastItem:
        addonHelper.add_folder("Next", {"folder": selectedFolder, "page": page+1}, thumbnail="next.png")


def build_season_folders(showId):
    seasons = guidebox.list_seasons_for_show(showId)
    for season in seasons["results"]:
        addonHelper.add_folder("Season " + str(season["season_number"]), {"show": showId, "season": season["season_number"]})


def build_episode_folders(showId, seasonNumber):
    episodes = guidebox.list_episodes_for_show_season(showId, seasonNumber, start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", {"show": showId, "season": seasonNumber, "page": page-1}, thumbnail="previous.png")
    for episode in episodes["results"]:
        addonHelper.add_folder(episode["title"], {"episode": episode["id"]}, thumbnail=episode["thumbnail_208x117"])
    if episodes["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", {"show": showId, "season": seasonNumber, "page": page+1}, thumbnail="next.png")


def build_source_type_folders(episodeId):
    addonHelper.add_folder("All Sources", {"episode": episodeId, "sourceType": "all"})
    addonHelper.add_folder("Free", {"episode": episodeId, "sourceType": "free"})
    addonHelper.add_folder("Subscription", {"episode": episodeId, "sourceType": "subscription"})
    addonHelper.add_folder("TV Everywhere", {"episode": episodeId, "sourceType": "tv_everywhere"})
    addonHelper.add_folder("Purchase", {"episode": episodeId, "sourceType": "purchase"})


def build_episode_links(episodeId, sourceType):
    episodeInfo = guidebox.fetch_episode_info(episodeId)
    if sourceType == "all":
        build_episode_links(episodeId, "free")
        build_episode_links(episodeId, "subscription")
        build_episode_links(episodeId, "tv_everywhere")
        build_episode_links(episodeId, "purchase")
    else:
        for source in episodeInfo[sourceType + "_" + Guidebox.get_platform() + "_sources"]:
            addonHelper.add_endpoint(source["display_name"], build_chrome_launcher_url(source["link"]))


def build_chrome_launcher_url(link):
    return chromeLauncherBaseUrl + "?url=" + urllib.quote(link) + "&mode=showSite&stopPlayback=yes"

def add_favorite_channel(channelId):
    favoriteChannels.append(channelId)
    channelString = ','.join(favoriteChannels)
    addonHelper.set_setting("favorite-channels", channelString)
    callback = addonHelp.get_param("callback")
    addonHelper.navigate_now(callback)
    return

def add_favorite_show(showId):
    favoriteShows.append(showId)
    showString = ','.join(favoriteShows)
    addonHelper.set_setting("favorite-shows", showString)
    callback = addonHelp.get_param("callback")
    addonHelper.navigate_now(callback)
    return

def remove_favorite_channel(channelId):
    filter(lambda a: a != channelId, favoriteChannels)
    channelString = ','.join(favoriteChannels)
    addonHelper.set_setting("favorite-channels", channelString)
    callback = addonHelp.get_param("callback")
    addonHelper.navigate_now(callback)
    return

def remove_favorite_show(showId):
    filter(lambda a: a != channelId, favoriteCShows)
    showString = ','.join(favoriteShows)
    addonHelper.set_setting("favorite-shows", showString)
    callback = addonHelp.get_param("callback")
    addonHelper.navigate_now(callback)
    return

def load_root_folders():
    for id, subfolder in rootFolders.iteritems():
        addonHelper.add_folder(subfolder["label"], {"folder": id}, subfolder["icon"], subfolder["thumbnail"])


rootFolders = {
    "browseChannels": {
        "label": "Browse Channels",
        "id": "browseChannels",
        "icon": None,
        "thumbnail": None,
        "subfolders": [],
        "subfolder_builder": lambda: build_channel_folders()
    }
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
#    "favoriteChannels": {
#        "label": "Favorite Channels",
#        "id": "favoriteChannels",
#        "icon": None,
#        "thumbnail": None,
#        "subfolders": [],
#        "subfolder_builder": lambda: build_favorite_channels_folders()
#    },
#    "favoriteShows": {
#        "label": "Favorite Shows",
#        "id": "favoriteShows",
#        "icon": None,
#        "thumbnail": None,
#        "subfolders": [],
#        "subfolder_builder": lambda: build_favorite_shows_folders()
#    }
}

if selectedMovie:
    pass

elif sourceType and selectedEpisode:
    # display a list of streaming links for a source
    build_episode_links(selectedEpisode, sourceType)

elif selectedEpisode:
    # display a list of streaming sources for an episode
    build_source_type_folders(selectedEpisode)

elif selectedSeason and selectedShow:
    # if season is selected, show must also be selected
    # display the episodes for a season
    build_episode_folders(selectedShow, selectedSeason)
    pass

elif selectedShow:
    # display the seasons for a show
    build_season_folders(selectedShow)
    pass

elif selectedChannel:
    # display the shows for a channel
    build_show_folders(selectedChannel)
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
            addonHelper.add_folder(subfolder["label"], {"folder": folderName}, subfolder["icon"], subfolder["thumbnail"])
    pass
elif action:
    channelId = addon.get_param("channelId")
    showId = addon.get_param("showId")
    if action == "addFavoriteChannel":
        
        add_favorite_channel(channelId)
        pass
    elif action == "addFavoriteShow":
        add_favorite_show(showId)
        pass
    elif action == "removeFavoriteChannel":
        remove_favorite_channel(channelId)
        pass
    elif action == "removeFavoriteShow":
        remove_favorite_show(showId)
        pass
    else:
        load_root_folders()
else:
    # show the root folder
    load_root_folders()

addonHelper.end()
