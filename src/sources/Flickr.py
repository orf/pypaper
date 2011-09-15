import sources
import dtflickr
import urllib

ORDERING_VAL = {"Interesting":"interestingness-desc",
                "Time":"date-posted-desc",
                "Relevance":"relevance"}


class FlickrWallpaper(sources.WallpaperSource):
    NAME = 'Flickr'
    OPTIONS = {"API key":(sources.StringOption(), "a8972a5dc7c703b720cdb2dbfc4ff476"),
               "Search text":(sources.StringOption(), "wallpaper"),
               "Ordering":(sources.DropDownOption(["Interesting","Time","Relevance"]),"Interesting"),
               }
    
    def __init__(self, *args, **kwargs):
        super(FlickrWallpaper, self).__init__(*args, **kwargs)
        self.photo_list = []
        self.client = dtflickr.Flickr(api_key=self.get_setting("API key"))
    
    def selected(self):
        search = self.get_setting("Search text")
        ordering = ORDERING_VAL[self.get_setting("Ordering")]
        self.photo_list = self.client.photos.search(text=search, sort=ordering).photos.photo
        print "Selected"
        
    def getNextWallpaper(self):
        paper = self._getNextWallpaper()
        return urllib.urlretrieve(paper)[0]
        
    def _getNextWallpaper(self):
        while True:
            info = self.photo_list.pop()
            
            size_back = {"Original":None, "Large":None}
            
            sizes = self.client.photos.getSizes(photo_id=info.id).sizes
            if not sizes.candownload:
                print "Cant download photo %s, skipping"%info.id
                continue
            for photo in sizes.size:
                if photo.label == "Original":
                    size_back["Original"] = photo.source
                elif photo.label == "Large":
                    size_back["Large"] = photo.source
                    
            if not any(size_back.values()):
                print "No urls found"
                continue
            print size_back
            if size_back["Original"]:
                return size_back["Original"]
            return size_back["Large"]
        
module = FlickrWallpaper