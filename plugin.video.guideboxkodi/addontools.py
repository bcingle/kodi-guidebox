
import urlparse
import urllib
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import json
import os
import pickle

class AddonHelper(dict):
    '''
    Set of tools that can be easily used to communicate with the XBMC/Kodi Plugin API. These tools
    make it easier to do common plugin tasks, like build URLs to sub folders, add folders, etc.
    '''
    def __init__(self, args):
        self['base_url'] = args[0]
        self['xbmcaddon'] = xbmcaddon.Addon()
        self["addon_name"] = self["xbmcaddon"].getAddonInfo("name")
        self["addon_id"] = self["xbmcaddon"].getAddonInfo("id")
        print "Base URL: " + str(self['base_url'])
        self['addon_handle'] = int(args[1])
        print "Addon Handle: " + str(self['addon_handle'])
        if len(args) >= 3:
            self['params'] = urlparse.parse_qs(args[2][1:])
        else:
            self['params'] = {}
        print "Parameters: " + str(self['params'])
        xbmcplugin.setContent(self['addon_handle'], 'movies')
        self['full_path'] = self['base_url'] + '?' + urllib.urlencode(self['params']);
        self["user_data_folder"] = xbmc.translatePath("special://profile/addon_data/"+self['addon_id'])
        if not os.path.isdir(self["user_data_folder"]):
            os.mkdir(self["user_data_folder"])
        self["user_data_file"] = os.path.join(self["user_data_folder"], "userdata.json")

    def build_url(self, query):
        """
        Build a url from a given query. The query should be a tuple in the form ["key1": "value1", "key2": "value2", ...]
        """
        return self['base_url'] + '?' + urllib.urlencode(query)

    def get_param(self, name, default=None):
        """
        Get a parameter by name, as passed to the addon
        """
        print "Retrieving parameter " + name
        params = self['params'].get(name, default)
        if params:
            return params[0]
        else:
            return default

    def add_folder(self, label, path={}, artwork=None, contextMenu=None, mediaType=None, listInfo=None, of=0, overrideContextMenu=False):
        """
        Add a subfolder to the current view with the given parameters. A subfolder is a special endpoint that
        links back to the same plugin with different parameters
        
        :param label: String, the label of the entry that will be shown
        :param path: Dictionary of parameters to pass to this addon
        :param artwork: A dictionary, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setArt
        :param contextMenu: A dictionary, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-addContextMenuItems
        :param mediaType: String, type of media for listInfo, one of ['video', 'music', 'pictures'] - only applicable if listInfo is also defined
        :param listInfo: A dictionary with listInfo properties, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setInfo
        """
        self.add_endpoint(label, url=self.build_url(path), folder=True, artwork=artwork, contextMenu=contextMenu, mediaType=mediaType, listInfo=listInfo, overrideContextMenu=overrideContextMenu)
        print "Added a folder: " + label
        print path


    def add_endpoint(self, label, url=None, folder=False, artwork=None, contextMenu=None, overrideContextMenu=False, mediaType=None, listInfo=None, of=0):
        """
        Add an endpoint. An endpoint is an item in the list of items shown to the user, either a folder or
        a link/url recognized by XBMC
        
        :param label: String, the label of the entry that will be shown
        :param url: String, the url of the entry, where this item directs to
        :param folder: True/False, whether this is a folder (default False)
        :param artwork: A dictionary, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setArt
        :param contextMenu: A dictionary, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-addContextMenuItems
        :param mediaType: String, type of media for listInfo, one of ['video', 'music', 'pictures'] - only applicable if listInfo is also defined
        :param listInfo: A dictionary with listInfo properties, as defined at http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setInfo
        """
        li = xbmcgui.ListItem(label=label)
        if artwork:
            print "Adding artwork " + json.dumps(artwork)
            li.setArt(artwork)
        if mediaType and listInfo:
            print "Adding info " + json.dumps(listInfo)
            li.setInfo(mediaType, listInfo)
        if contextMenu:
            print "Adding context menu items " + json.dumps(contextMenu)
            li.addContextMenuItems(contextMenu, overrideContextMenu)
        xbmcplugin.addDirectoryItem(handle=self['addon_handle'], url=url, listitem=li, isFolder=folder, totalItems=of)
        print "Added navigation element to menu: " + label + " with path " + url

    def end(self, viewMode=None):
        """
        Mark the end of adding subfolders and end points
        
        :param viewMode: Optional param to set a view mode for the list
        """
        if viewMode:
            self.set_view_mode(viewMode)
        xbmcplugin.endOfDirectory(self['addon_handle'])
        print "Closed navigation"

    def is_platform(self, platform):
        """
        Returns true is Kodi is running on the given platform
        """
        return xbmc.getCondVisibility('System.Platform.' + platform)
        
    def get_string(self, key):
        """
        Get a localized string from the strings.xml localization file
        :param id: The id of the string, given by a number lik '320001'
        """
        return self['xbmcaddon'].getLocalizedString(int(key))

    def get_setting(self, key):
        """
        Get the string representation of some setting from the user settings for this plugin
        :param id: The name of the setting to get
        """
        return self['xbmcaddon'].getSetting(key)
    
    def set_setting(self, id, value):
        """
        Manually set some user setting
        """
        self['xbmcaddon'].setSetting(id, value)
        
    def navigate_now(self, path={}):
        """
        Immediately redirect to a new path
        """
        path = self.build_url(path);
        xbmc.executebuiltin('RunPlugin(' + path + ')')
        
    def get_current_path(self):
        """
        Provide the full plugin:// path that was used to call this plugin, including parameters
        """
        return self["full_path"]
    
    def set_view_mode(self, viewMode):
        """
        Sets the view mode for the vurrent list. Must be called after adding all folders and before calling AddonHelper.end(). 
        It is preferable to pass the view mode to the end() function instead of using this, but not always possible.
        """
        xbmc.executebuiltin("Container.SetViewMode(" + viewMode + ")")
        
    def get_platform(self):
        """
        Returns one of:
        linux
        win
        osx
        ios
        android
        atv2
        raspberry_pi
        unknown
        """
        if self.is_platform('Linux.RaspberryPi'):
            return "raspberry_pi"
        if self.is_platform("Linux"):
            return "linux"
        if self.is_platform("Windows"):
            return "win"
        if self.is_platform("OSX"):
            return "osx"
        if self.is_platform("IOS"):
            return "ios"
        if self.is_platform("ATV2"):
            return "atv2"
        if self.is_platform("Android"):
            return "android"
        return "unknown"

    def notify(self, message, time=5000, sound=True):
        """
        Displays a notification in Kodi
        :param message: Message of the notification
        :param time: Time to display njotification in ms (default 5000)
        :param sound: Whether to play sound or not (default True)
        """
        print "Showing notification with message [" + message + "], time " + str(time) + " and sound " + str(sound)
        xbmcgui.Dialog().notification(self["addon_name"], message, time=time, sound=sound)
    
    def set_user_data(self, key, value):
        """
        Set any data or object as the user's data. Writes to a file in the user's "special" folder for this addon.
        :param key: The key for the user data, must be a string or convertible to a string
        :param value: The value for the user data, any data tupe (old value will be overwritten if key already exists)
        """
        if not os.path.isfile(self["user_data_file"]):
            userData = {}
        else:
            userData = pickle.load(open(self["user_data_file"], "rb"))
        userData[str(key)] = value
        pickle.dump(userData, open(self["user_data_file"], "wb"))
        
    def get_user_data(self, key):
        """
        Get full user data stored in the user's special folder
        :param key: The key for the data to be retrieved, must be a string or convertible to a string
        :returns: The value stored in user data, or None if no value was stored with the given key
        """
        if not os.path.isfile(self["user_data_file"]):
            return None
        userData = pickle.load(open(self["user_data_file"], "rb"))
        key = str(key)
        if key in userData:
            return userData[key]
        else:
            return None
