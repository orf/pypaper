import sources
import os
import re
import itertools
import random
import imghdr

class LocalFileProvider(sources.WallpaperSource):
    ''' I run through a folder full of images and load them one by one '''
    
    NAME = "Local Folder"
    OPTIONS = {"Directory":sources.DirectoryOption(default=None, reload_on_change=True),
               "Shuffle":sources.BooleanOption(default=True, reload_on_change=True)}
    
    def __init__(self, *args, **kwargs):
        super(LocalFileProvider, self).__init__(*args, **kwargs)

    def sourceSelected(self):

        directory = self.get_setting("Directory")

        files = []
        for path in os.listdir(directory):
            p = os.path.join(directory, path)
            if os.path.isfile(p) and imghdr.what(p):
                files.append(p)

        if self.get_setting("Shuffle"):
            random.shuffle(files)

        self.log("INFO","Found %s images from folder %s"%(len(files),directory))

        return files

    
    def getWallpaper(self, path):
        # The file may have been deleted since we called selected(). Make sure it still exists
        if not os.path.isfile(path):
            raise sources.NotFound()
        return path

        
module = LocalFileProvider