import sources
import reddit
import urlparse
import urllib
import itertools

from reddit import helpers

class RedditWallpaper(sources.WallpaperSource):
    ''' Pulls imgur links from r/wallpaper based on filters '''
    NAME = "Reddit"
    OPTIONS = {"Hide NSFW":(sources.BooleanOption(), True),
               "Subreddit name":(sources.StringOption(), "wallpaper"),
               "Filter":(sources.DropDownOption(["Hot","Top Today",
                                                 "Top Week","Top Month",
                                                 "Top Year","Top all time",
                                                 "New"]), "Hot")
               }
    
    def __init__(self, *args, **kwargs):
        super(RedditWallpaper, self).__init__(*args, **kwargs)
        self.file_list = set()
        self.reddit_client = reddit.Reddit(user_agent="pypaper")
        self.subreddit = None
        
    def selected(self):
        self.subreddit = self.reddit_client.get_subreddit(self.get_setting("Subreddit name"))
        
        filters = {"Hot":helpers._get_sorter("/"),
                   "Top Today":helpers._get_sorter("/top", time="day"),
                   "Top Week":helpers._get_sorter("/top", time="week"),
                   "Top Month":helpers._get_sorter("/top", time="month"),
                   "Top Year":helpers._get_sorter("/top", time="year"),
                   "Top all time":helpers._get_sorter("/top", time="all"),
                   "New":helpers._get_sorter("/new", time="rising")}
        
        filter = self.get_setting("Filter")
        links = list(filters[filter](self.subreddit))
        for link in links:
            if link.kind == "t3":
                if "imgur.com" in link.domain:
                    if link.over_18 and self.get_setting("Hide NSFW"):
                        continue
                    # Make it a direct link
                    parsed = urlparse.urlsplit(link.url)
                    if parsed.netloc == "i.imgur.com":
                        url = link.url
                    else:
                        # Extract the ID
                        id = parsed.path[1:] # Remove the /
                        url = "http://i.imgur.com/%s.jpg"%id
                    self.file_list.add(url)
        
        self.file_list = itertools.cycle(self.file_list)
    
    def getNextWallpaper(self):
        url = self.file_list.next()
        tf, _ = urllib.urlretrieve(url)
        return tf


module = RedditWallpaper