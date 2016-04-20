
import urlparse
import urllib
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc

class AddonHelper(dict):
    '''
    Set of tools that can be easily used to communicate with the XBMC/Kodi Plugin API. These tools
    make it easier to do common plugin tasks, like build URLs to sub folders, add folders, etc.
    '''
    def __init__(self, args):
        self['base_url'] = args[0]
        self['xbmcaddon'] = xbmcaddon.Addon()
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

    def add_folder(self, label, path={}, icon=None, thumbnail=None, artwork=None, contextMenu=None):
        """
        Add a subfolder to the current view with the given parameters. A subfolder is a special endpoint that
        links back to the same plugin with different parameters
        """
        self.add_endpoint(label, self.build_url(path), icon, thumbnail, folder=True, contextMenu=contextMenu)
        print "Added a folder: " + label
        print path


    def add_endpoint(self, label, url=None, icon=None, thumbnail=None, folder=False, contextMenu=None):
        """
        Add an endpoint. An endpoint is an item in the list of items shown to the user, either a folder or
        a link/url recognized by XBMC
        """
        li = xbmcgui.ListItem(label=label, iconImage=icon, thumbnailImage=thumbnail)
        if contextMenu:
            li.addContextMenuItems(contextMenu)
        xbmcplugin.addDirectoryItem(handle=self['addon_handle'], url=url, listitem=li, isFolder=folder)
        print "Added navigation element to menu: " + label + " with path " + url

    def end(self):
        """
        Mark the end of adding subfolders and end points
        """
        xbmcplugin.endOfDirectory(self['addon_handle'])
        print "Closed navigation"

    @staticmethod
    def is_platform(platform):
        """
        Returns true is Kodi is running on the given platform
        """
        return xbmc.getCondVisibility('System.Platform.' + platform)
        
    def get_string(self, id):
        """
        Get a localized string from the strings.xml localization file
        :param id: The id of the string, given by a number lik '320001'
        """
        return self['xbmcaddon'].getLocalizedString(id)

    def get_setting(self, id):
        """
        Get the string representation of some setting from the user settings for this plugin
        :param id: The name of the setting to get
        """
        return self['xbmcaddon'].getSetting(id)
    
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
        return self["full_path"]
        
