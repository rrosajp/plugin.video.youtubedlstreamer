# Authors: ChatGPT and ilikenwf
# License: GNU GPL

# Import required modules
import sys
import os
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import yt_dlp

PLUGIN_URL = sys.argv[0]
PLUGIN_ID = int(sys.argv[1])
PLUGIN_NAME = PLUGIN_URL.replace("plugin://","")

# Create a Kodi addon with a menu with two entries: "Search" and "Search from history"
class MyAddon(xbmcaddon.Addon):
    HISTORY_FILE_PATH = None
    QUERY = None
    
    def __init__(self):
        xbmcaddon.Addon.__init__(self)
        self.handle = int(sys.argv[1])
        self.path = sys.argv[0]
        
        profile = xbmc.translatePath(os.path.join("special://profile/addon_data/", xbmcaddon.Addon().getAddonInfo("id")))
        self.HISTORY_FILE_PATH = os.path.join(profile, "history.txt")
    
        if not os.path.exists(profile):
           # Create parent directories if they don't exist
           os.makedirs(profile)        

    def end_of_directory(self, succeeded=True, update_listing=False, cache_to_disc=True):
        xbmcplugin.endOfDirectory(handle=self.handle, succeeded=succeeded,
                                  updateListing=update_listing, cacheToDisc=cache_to_disc)

    def build_main_menu(self):
        # Add the "Search" menu entry
        search_url = "{0}?{1}".format(self.path, urllib.parse.urlencode({"search": "search"}))
        xbmcplugin.addDirectoryItem(self.handle, search_url, xbmcgui.ListItem("Search"), isFolder=False)

        # Add the "Search from history" menu entry
        history_url = "{0}?{1}".format(self.path, urllib.parse.urlencode({"history": "history"}))
        xbmcplugin.addDirectoryItem(self.handle, history_url, xbmcgui.ListItem("Search from history"), isFolder=False)
        
        # Add the "Clear history" menu entry
        clear_history_url = "{0}?{1}".format(self.path, urllib.parse.urlencode({"clear_history": "clear_history"}))
        xbmcplugin.addDirectoryItem(self.handle, clear_history_url, xbmcgui.ListItem("Clear history"), isFolder=False)

    def clear_history(self):
        if confirm := xbmcgui.Dialog().yesno(
            "Clear history", "Are you sure you want to clear the history?"
        ):
            # Clear the history file
            open(self.HISTORY_FILE_PATH, "w").close()

            # Show a notification to inform the user that the history file has been cleared
            xbmc.executebuiltin("Notification(Clear history, History file has been cleared)")


    def search_and_play(self):
        if not self.QUERY:
        # Prompt user to enter search query
            self.QUERY = xbmcgui.Dialog().input("Enter search query")

        if self.QUERY:        
            search_query = self.QUERY
            self.QUERY = None

            # Create a progress dialog instance
            progress_dialog = xbmcgui.DialogProgress()

            # Show the spinner
            progress_dialog.create("Please wait", "Retrieving search results...")

            # Read the history file
            with open(self.HISTORY_FILE_PATH, "r") as history_file:
                history = history_file.readlines()

            history = list(reversed(history))

            if search_query+"\n" not in history:
                # Truncate the history file to keep only the first 10 lines
                if len(history) >= 10:
                    history = history[:10]
                    with open(self.HISTORY_FILE_PATH, "w") as history_file:
                        history_file.write("".join(history))

                # Add the search query to the history
                with open(self.HISTORY_FILE_PATH, "a") as history_file:
                    history_file.write(search_query + "\n")

            # Create a YoutubeDL instance and set it to extract only audio and video formats
            ydl = yt_dlp.YoutubeDL({"quiet": True, "format": "best"})

            # Use the YoutubeDL instance to extract stream URIs for the search query
            result = ydl.extract_info(search_query, download=False)
            streams = []
            if "formats" in result:
                # Get the list of stream URIs in the order they were returned by yt-dlp
                streams = [(f["format"], f["url"]) for f in result["formats"]]

            # Use the reversed() function to reverse the order of the streams
            streams = list(reversed(streams))

            # Hide the spinner
            progress_dialog.close()

            # Present a dialog to choose which stream to play
            options = [f[0] or f[1] for f in streams]
            selected_stream = xbmcgui.Dialog().select("Select stream to play", options)

            if selected_stream >= 0:                
                # Pass the selected stream to the Kodi player
                player = xbmc.Player()
                player.play(streams[selected_stream][1])
                
    def search_from_history(self):
        # Read the history file
        with open(self.HISTORY_FILE_PATH, "r") as history_file:
            history = history_file.readlines()

        # Present a dialog to choose which search query to use
        selected_query = xbmcgui.Dialog().select("Select search query", history)

        if selected_query >= 0:
            # Use the selected search query
            self.QUERY = history[selected_query].strip()
            self.search_and_play()

        # Return to the main menu
        self.build_main_menu()
        self.end_of_directory(succeeded=True)

    def run(self):
        params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))

        if "search" in params:
            self.search_and_play()

        elif "history" in params:
            self.search_from_history()
            
        elif "clear_history" in params:
            self.clear_history()

        else:
            self.build_main_menu()
            self.end_of_directory(succeeded=True)

if __name__ == "__main__":
    MyAddon().run()
