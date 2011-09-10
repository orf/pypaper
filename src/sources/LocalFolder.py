import sources
import os
import re
import itertools
import random

class LocalFileProvider(sources.WallpaperSource):
    ''' I run through a folder full of images and load them 
        one by one '''
    NAME = "Local Folder"
    OPTIONS = {"Directory":(sources.FilePathOption, None),
               "File extensions":(sources.StringOption, "jpg,png"),
               "Shuffle":(sources.BooleanOption, True)}
    
    def __init__(self, *args, **kwargs):
        super(LocalFileProvider, self).__init__(*args, **kwargs)
        self.file_list = []
    
    def selected(self):
        directory = self.get_setting("Directory")
        extensions = self.get_setting("File extensions")
        MATCH_PATTERN = ".*(%s)$"%("|".join(set(extensions.split(","))))
        MATCH_REGEX = re.compile(MATCH_PATTERN)
        #[f for f in os.listdir(directory) if MATCH_REGEX.match(f)]
        files = os.listdir(directory)
        if self.get_setting("Shuffle"):
            random.shuffle(files)
        self.file_list = itertools.cycle(
                                itertools.ifilter(MATCH_REGEX.match, files)
                                )
    
    def getNextWallpaper(self):
        return os.path.join(self.get_setting("Directory"),
                            self.file_list.next())
        
module = LocalFileProvider