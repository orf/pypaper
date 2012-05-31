import sources
import reddit
import urlparse
import urllib
import random

from reddit import helpers

class RedditWallpaper(sources.WallpaperSource):
    ''' Pulls imgur links from r/wallpaper based on filters '''
    NAME = "Reddit"
    OPTIONS = {"Hide NSFW":sources.BooleanOption(default= True, reload_on_change=True),
               "Subreddit name":sources.StringOption(default="wallpaper", reload_on_change=True),
               "Filter":sources.DropDownOption(default="Hot", choices=["Hot","Top Today",
                                                                         "Top Week","Top Month",
                                                                         "Top Year","Top all time",
                                                                         "New"],
                                                reload_on_change=True),
               "Shuffle":sources.BooleanOption(default=True, reload_on_change=True),
               }
    
    def __init__(self, *args, **kwargs):
        super(RedditWallpaper, self).__init__(*args, **kwargs)
        self.reddit_client = reddit.Reddit(user_agent="pypaper")
        self.subreddit = None
        
    def sourceSelected(self):
        self.subreddit = self.reddit_client.get_subreddit(self.get_setting("Subreddit name"))
        
        filters = {"Hot":helpers._get_sorter(""),
                   "Top Today":helpers._get_sorter("top", t="day"),
                   "Top Week":helpers._get_sorter("top", t="week"),
                   "Top Month":helpers._get_sorter("top", t="month"),
                   "Top Year":helpers._get_sorter("top", t="year"),
                   "Top all time":helpers._get_sorter("top", t="all"),
                   "New":helpers._get_sorter("new", sort="rising")}
        
        filter = self.get_setting("Filter")
        links = list(filters[filter](self.subreddit))
        file_list = list()
        for link in links:
            kind = link.content_id.split("_")[0]
            if kind == "t3" and not "request" in link.title.lower():
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
                    file_list.append(url)

        if self.get_setting("Shuffle"):
            random.shuffle(file_list)
        return file_list
    
    def getWallpaper(self, url):
        return urllib.urlretrieve(url, filename=self.get_wallpaper_file())[0]


module = RedditWallpaper