import shelve
import cPickle
import easygui
import atexit
import os

class NotFound(Exception):
    pass

class EndOfPapers(Exception):
    pass

class PaperError(Exception):
    """
    I am an exception that is raised when attempts to get a list of wallpapers has failed 5 times.
    """
    pass

class Option(object):
    def __init__(self, default=None, reload_on_change=False):
        self.default = default
        self.reload_on_change = reload_on_change

    def showOption(self, name, default):
        raise NotImplemented()

    def validateChoice(self, choice):
        raise NotImplemented()

class DropDownOption(Option):
    def __init__(self, **kwargs):
        self.choices = kwargs.pop("choices")
        super(DropDownOption, self).__init__(**kwargs)
        
    def showOption(self, name, default):
        return easygui.choicebox("Choose an option", "Choose", self.choices)

class DirectoryOption(Option):
    def showOption(self, name, default):
        return easygui.diropenbox(None, "Choose a directory", default)
    
class StringOption(Option):
    def showOption(self, name, default):
        return easygui.enterbox("Enter a string for setting '%s'"%name, 
                                "Alter setting", default)

class BooleanOption(Option):
    def showOption(self, name, default):
        return easygui.boolbox(name)


class WallpaperSource(object):
    NAME = None
    OPTIONS = {}
    
    def __init__(self, setting_provider, log_function, tdir):
        self.settings = setting_provider
        self.log_function = log_function
        self.cache = []
        self.timesSelected = 0
        self.tdir = tdir

    def get_wallpaper_file(self):
        return os.path.join(self.tdir, "wallpaper.temp")
        
    def set_setting(self, setting, value):
        self.settings.set_settings(self.NAME, setting, value)
    
    def get_setting(self, setting):
        r = self.settings.get_setting(self.NAME, setting)
        if isinstance(r, NotFound):
            if setting in self.OPTIONS:
                r = self.OPTIONS[setting].default # Default
        return r

    def selected(self):
        self.timesSelected+=1
        self.cache = self.sourceSelected()
        return self.cache

    def getNextWallpaper(self, _timescalled=0):
        """
        I am a recursive function. I go through self.cache (populated by sourceSelected) and call getWallpaper.
        If there are no elements left (i.e all fail) then I call myself, which refreshes the list, and continue
        to try each item again. If I fail 5 times I raise PaperError which will notify the user of an error.
        """

        if _timescalled == 5:
            raise PaperError()

        if not len(self.cache):
            self.selected()

        while True:
            try:
                item = self.cache.pop()
            except IndexError:
                # Ok, so we have no more items left. Increment _timescalled and call ourselves again.
                self.getNextWallpaper(_timescalled+1)
            else:
                try:
                    return self.getWallpaper(item)
                except NotFound:
                    continue
                except Exception, e:
                    self.log("Error","Error getting wallpaper item '%s': %s"%(item, e))
                    continue


    def sourceSelected(self):
        """
        This method is called when a user selects this source. Use it to fetch info from
        somewhere (an internet resource, file system etc) and return it. Each element from the
        returned list will be passed to getWallpaper, where you can handle downloading or processing it.

        Once all the items in getWallpaper have been processed selected() is called again to return a fresh list.
        The timesSelected attribute will be incremented every time this happens (1 being the 1st time) and reset to 1
        if the user re-selects the source after selecting another one.

        Returns: List of elements (File paths, ID's etc) to be sequentially passed to getWallpaper()
        """
        raise NotImplemented()
    
    def getWallpaper(self, element):
        """
        I take an element (an item returned from selected()) and return a file path to the wallpaper.
        Use this method to download an image (if element is a URL) or something. If its a file path make sure it
        still exists?

        I raise NotFound if the element is invalid (i.e file does not exist anymore or network resource
        is unreachable).
        """
        raise NotImplemented()

    def log(self, level, message):
        """
        Log a message to the log window.
        level: string describing the level (ERROR, WARNING etc)
        message: message to log.
        """
        self.log_function("%s: %s: %s"%(self.NAME, level, message))
    
            
class SettingsProvider(object):
    def __init__(self, file):
        self.db = shelve.open(file, protocol=cPickle.HIGHEST_PROTOCOL)
        atexit.register(self.db.close)
    
    def get_setting(self, name, setting_name):
        KEY_NAME = "%s_%s"%(name, setting_name)
        if self.db.has_key(KEY_NAME):
            return self.db[KEY_NAME]
        return NotFound()
    
    def set_setting(self, name, setting_name, value):
        KEY_NAME = "%s_%s"%(name, setting_name)
        self.db[KEY_NAME] = value