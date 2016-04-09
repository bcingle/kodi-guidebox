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

    def build_url(self, query):
        return self['base_url'] + '?' + urllib.urlencode(query)

    def get_param(self, name, default=None):
        print "Retrieving parameter " + name
        params = self['params'].get(name, default)
        if params:
            return params[0]
        else:
            return default

    def add_folder(self, label, path={}, icon=None, thumbnail=None, artwork=None):
        self.add_endpoint(label, self.build_url(path), icon, thumbnail, folder=True)
        print "Added a folder: " + label
        print path


    def add_endpoint(self, label, url=None, icon=None, thumbnail=None, folder=False):
        li = xbmcgui.ListItem(label=label, iconImage=icon, thumbnailImage=thumbnail)
        xbmcplugin.addDirectoryItem(handle=self['addon_handle'], url=url, listitem=li, isFolder=folder)
        print "Added navigation element to menu: " + label + " with path " + url

    def end(self):
        xbmcplugin.endOfDirectory(self['addon_handle'])
        print "Closed navigation"

    @staticmethod
    def is_platform(platform):
        return xbmc.getCondVisibility('System.Platform.' + platform)
        
    def get_string(self, id)
        return self['xbmcaddon'].getLocalizedString(id)

    def get_setting(self, id)
        return self['xbmcaddon'].getSetting(id)
