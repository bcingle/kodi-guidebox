import sys
import urllib
from addontools import AddonHelper
from guidebox import Guidebox

chromeLauncherBaseUrl = "plugin://plugin.program.chrome.launcher/"
print "Args: " + ";".join(sys.argv)

addonHelper = AddonHelper(sys.argv)
guidebox = Guidebox(addonHelper.get_setting("guidebox-api-key"))

selectedChannel = addonHelper.get_param("channel")
selectedShow = addonHelper.get_param("show")
selectedSeason = addonHelper.get_param("season")
selectedEpisode = addonHelper.get_param("episode")
selectedFolder = addonHelper.get_param("folder")
selectedMovie = addonHelper.get_param("movie")
sourceType = addonHelper.get_param("sourceType")
pageSize = 12 # consider putting this value in Settings
page = int(addonHelper.get_param("page", 0)) # enable pagination
pageStart = page * pageSize
pageLastItem = pageStart + pageSize


def build_channel_folders():
    channels = guidebox.list_all_channels(start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", {"folder": selectedFolder, "page": page-1}, thumbnail="previous.png")
    for channel in channels["results"]:
        addonHelper.add_folder(channel["name"], {"channel": channel["short_name"]}, None, channel["artwork_208x117"])
    if channels["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", {"folder": selectedFolder, "page": page+1}, thumbnail="next.png")


def build_show_folders(channelId):
    shows = guidebox.list_shows_for_channel(channelId=channelId, start=pageStart, limit=pageSize)
    if page > 0:
        addonHelper.add_folder("Previous", {"channel": channelId, "page": page-1}, thumbnail="previous.png")
    for show in shows["results"]:
        addonHelper.add_folder(show["title"], {"show": show["id"]}, thumbnail=show["artwork_208x117"])
    if shows["total_results"] > pageLastItem:
        addonHelper.add_folder("Next", {"channel": channelId, "page": page+1}, thumbnail="next.png")


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
    episodeInfo = guidebox.list_episode_info(episodeId)
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


rootFolders = {
    "browseChannels": {
        "label": "Browse Channels",
        "id": "browseChannels",
        "icon": None,
        "thumbnail": None,
        "subfolders": [],
        "subfolder_builder": lambda: build_channel_folders()
    }#,
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
    # }
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

else:
    # show the root folder
    for id, subfolder in rootFolders.iteritems():
        addonHelper.add_folder(subfolder["label"], {"folder": id}, subfolder["icon"], subfolder["thumbnail"])

addonHelper.end()
