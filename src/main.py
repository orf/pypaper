import systray
import glob
import os
import imp
import functools
import sources

import win32gui
import win32con

__VERSION__ = "0.1"
ICON = "wallpaper.ico"

class SourceManager(object):
    def __init__(self):
        
        self.current_provider = None
        self.settings = sources.SettingsProvider("settings.db")
        
        self.modules = []
        for file in glob.glob(os.path.join("sources","*.py")):
            name = os.path.splitext(os.path.split(file)[1])[0]
            if not name == "__init__":
                mod = imp.load_module(name,open(file),file,imp.get_suffixes()[1]).module
                
                if mod.NAME == self.settings.get_setting("_MANAGER","LastProvider"):
                    self.setProvider(mod)
                
                self.modules.append(mod)
    
    def getCurrentSource(self):
        if self.current_provider:
            return self.current_provider
        
    def nextWallpaper(self, _):
        x = self.getCurrentSource()
        if x:
            self.set_wallpaper(x.getNextWallpaper())
    
    def setProvider(self, klass):
        if not self.verifySettings(klass):
            print "Invalid settings"
            return
        self.current_provider = klass(self.settings)
        self.current_provider.selected()
        self.set_wallpaper(self.current_provider.getNextWallpaper())
        self.settings.set_setting("_MANAGER","LastProvider",klass.NAME)
    
    def set_wallpaper(self, path):
        win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, path, 3)
    
    def generate_source_menu(self):
        returner = []
        for module in self.modules:
            _settings = []
            for setting in module.OPTIONS:
                _settings.append((setting, None, functools.partial(self.settingsInput, module, setting)))
                
            returner.append((module.NAME, None, (
                                                 ("Activate",None,functools.partial(self.activateSource, module)),
                                                 ("Settings",None,_settings)
                                                 )))
        return returner
    
    def verifySettings(self, module):
        for option in module.OPTIONS:
            if isinstance(self.settings.get_setting(module.NAME, option),sources.NotFound) \
               and not module.OPTIONS[option][1]: #default
                if not self.settingsInput(module, option, None):
                    return None
        return True
    
    def settingsInput(self, module, setting, toolbarmenu):
        current_setting = self.settings.get_setting(module.NAME,setting)
        if isinstance(current_setting, sources.NotFound):
            if setting in module.OPTIONS:
                current_setting = module.OPTIONS[setting][1]
        
        new_input = module.OPTIONS[setting][0].showOption(setting, current_setting)
        
        if new_input != None:
            self.settings.set_setting(module.NAME, setting, new_input)
            return True
        else:
            return None
        
    def activateSource(self, module, toolbarmenu):
        if not isinstance(self.current_provider, module):
            self.setProvider(module)


if __name__ == "__main__":
    
    manager = SourceManager()
    options = (
               ('Next Wallpaper', None, manager.nextWallpaper),
               ('Wallpaper Source', None, (manager.generate_source_menu())),
               )
    
    tray = systray.SysTrayIcon(ICON,
                               "PyPaper %s"%__VERSION__,
                               options)