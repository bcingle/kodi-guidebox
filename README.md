# kodi-guidebox
A Kodi video addon for the Guidebox streaming API

Guidebox is a web service that provides links to streaming media sources.  It provides a navigable API and search capabilities to find your favorite shows. This addon is simply a front-end with navigation and pagination for the API, with a starting point of Channels or Shows. 

This addon uses a free API key from Guidebox.  They place some limits on usage, such as the number of API calls per second and per month.  If the limit is reached, then I will either delete the shared key and require users to acquire their own key, or move to a paid key and ask for donations.  But for now the free key is sufficient.

For more information about the Guidebox API, go here: https://api.guidebox.com/

This addon uses fanart from fanart.tv.  It is recommended to go to https://fanart.tv, create an account there, and create a free personal API key for use in this addon.  It may help performance, as the shared API key may become subject to limitations because it is a free version, similar to the Guidebox key.
