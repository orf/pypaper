import systray
import glob
import os
import imp
import functools
import sources
import datetime
import win32gui
import win32con
import pywintypes
import Image
import tempfile
import threading
import easygui
import sys
import imghdr
import winpaths

__VERSION__ = "0.3"
ICON = "wallpaper.ico"
WALL_LOCK = threading.Lock()

LOG = []

def AddToLog(message):
    msg = "%s: %s\n"%(datetime.datetime.now(),message)
    sys.stdout.write(msg)
    LOG.append(msg)

def ViewLogFile(systray):
    easygui.textbox(title="PyPaper LogFile",text=LOG)

class SourceManager(object):
    def __init__(self):
        """
        Create the SourceManager.
        The SourceManager is responsible for managing all the different wallpaper sources that live in sources/
        We start by creating the SettingsProvider which is essentially a key-value store for our modules settings.

        If this is created/loaded without a hitch we then load all of our modules one by one.
        """

        self.tpath = os.path.join(winpaths.get_appdata(), "pypaper")
        self.tconvert = os.path.join(self.tpath, "desktop.converted.jpeg")
        if not os.path.isdir(self.tpath):
            os.mkdir(self.tpath)

        self.current_provider = None
        try:
            self.settings = sources.SettingsProvider("settings.db")

        except Exception,e:
            easygui.msgbox("Error creating the settings database: %s"%e)
            sys.exit(1)

        self.modules = []
        for file in glob.glob(os.path.join("sources","*.py")):
            name = os.path.splitext(os.path.split(file)[1])[0]
            if not name == "__init__":
                try:
                    mod = imp.load_module(name,open(file),file,imp.get_suffixes()[1]).module
                except Exception,e:
                    AddToLog("Error loading module %s: %s"%(name, e))
                    continue
                else:
                    AddToLog("Loaded module %s"%name)

                if mod.NAME == self.settings.get_setting("_MANAGER","LastProvider"):
                    self.setProvider(mod)

                self.modules.append(mod)
        AddToLog("Initialized")

    def setProvider(self, klass):
        """
        I set the current providing source. I take a class to create (e.g LocalFolder.LocalFileProvider)
        I make sure the settings are all valid before creating it.

        I then call selected() on it to populate the class and then call getNextWallpaper to get the next wallpaper.

        Returns: True if the module was loaded correctly otherwise False
        """
        if not self.verifySettings(klass):
            easygui.msgbox("Error: The settings for %s are incorrect!\n" +
                           "Please ensure they are valid before re-selecting"%klass.NAME)
            return False

        self.current_provider = klass(self.settings, AddToLog, tdir=self.tpath)
        self.current_provider.selected()
        self.nextWallpaper()
        self.settings.set_setting("_MANAGER","LastProvider",klass.NAME)
        return True
    
    def getCurrentSource(self):
        return self.current_provider
        
    def nextWallpaper(self, *args):
        source = self.getCurrentSource()
        WALL_LOCK.acquire()
        try:

            for i in xrange(5):
                try:
                    self._nextWallpaper(source)
                    break
                except pywintypes.error,e:
                    AddToLog("Error setting wallpaper: %s"%e)
        finally:
            WALL_LOCK.release()
    
    def _nextWallpaper(self, source):
        wall = source.getNextWallpaper()
        if not imghdr.what(wall) in ("jpeg","bmp"):
            # Windows only likes jpeg or bmp images it seems, i don't know why.
            # Lets convert it :)
            wall = self.ConvertImage(wall)
        AddToLog("Set wallpaper to %s"%wall)
        self.set_wallpaper(wall)

    def ConvertImage(self, paper):
        new = open(self.tconvert,"wb")
        x = Image.open(paper)
        x.save(new)
        new.close()
        return self.tconvert
    
    def set_wallpaper(self, path):
        win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, path, 3)
    
    def generate_source_menu(self):
        returner = []
        for module in self.modules:
            _settings = []
            for setting in module.OPTIONS:
                _settings.append((setting, None, functools.partial(self.settingsInput, module, setting)))
                
            menus = (module.NAME, None, [("Activate",None,functools.partial(self.activateSource, module)),
                                        ("Settings",None,_settings),])
            returner.append(menus)
        return returner
    
    def verifySettings(self, module):
        for option in module.OPTIONS:
            if isinstance(self.settings.get_setting(module.NAME, option), sources.NotFound) \
               and not module.OPTIONS[option].default:
                if not self.settingsInput(module, option, None):
                    return None            
        return True
    
    def settingsInput(self, module, setting, toolbarmenu):
        current_setting = self.settings.get_setting(module.NAME,setting)
        if isinstance(current_setting, sources.NotFound):
            if setting in module.OPTIONS:
                current_setting = module.OPTIONS[setting].default
        
        new_input = module.OPTIONS[setting].showOption(setting, current_setting)
        
        if new_input is not None:
            self.settings.set_setting(module.NAME, setting, new_input)
            if module.OPTIONS[setting].reload_on_change:
                AddToLog("Setting %s has been altered, reloading module"%setting)
                self.activateSource(module, None)
            return True
        else:
            return None
        
    def activateSource(self, module, toolbarmenu):
        #if not isinstance(self.current_provider, module):
        #    self.setProvider(module)
        self.setProvider(module)


if __name__ == "__main__":
    manager = SourceManager()
    options = (
               ('Next Wallpaper', None, manager.nextWallpaper),
               ('Wallpaper Source', None, (manager.generate_source_menu())),
               ('View Log', None, ViewLogFile),
               )
    tray = systray.SysTrayIcon(ICON,
                               "PyPaper %s"%__VERSION__,
                               options)