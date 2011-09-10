import shelve
import cPickle
import os
import easygui
import atexit

class NotFound(object):
    pass

class FilePathOption(object):
    @staticmethod
    def showOption(name, default):
        return easygui.diropenbox(None, "Choose a directory", default)
    
class StringOption(object):
    @staticmethod
    def showOption(name, default):
        return easygui.enterbox("Enter a string for setting '%s'"%name, 
                                "Alter setting", default)
    
class BooleanOption(object):
    @staticmethod
    def showOption(name, default):
        return easygui.boolbox(name)


class WallpaperSource(object):
    NAME = None
    OPTIONS = {}
    
    def __init__(self, setting_provider):
        self.settings = setting_provider
        
    def set_setting(self, setting, value):
        self.settings.set_settings(self.NAME, setting, value)
    
    def get_setting(self, setting):
        r = self.settings.get_setting(self.NAME, setting)
        if isinstance(r, NotFound):
            if setting in self.OPTIONS:
                r = self.OPTIONS[setting][1] # Default
        return r
        
    def selected(self):
        raise NotImplemented()
    
    def getNextWallpaper(self):
        ''' This should *always* return a value. If shit goes wrong then
            return False, not an exception. Must return an ABSOLUTE path'''
        raise NotImplemented()
    
            
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