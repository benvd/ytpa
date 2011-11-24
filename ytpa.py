#!/usr/bin/python

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

# FIXME: retrieve all videos from a user/playlist, as opposed to
# only the first 25

# TODO: better error handling for exceptions from google's api

# TODO: config file (~/.ytpa)
#  - dev key
#  - username
#  - email
#  - default playlist (will be used if none specified)

# TODO: implement private playlist creation

# TODO: make sure playlist ID vs name usage is consistent
# in the YouTube class

from gdata.base.service import RequestError
import argparse
import gdata.youtube.service
import getpass
import re
import sys


DESCRIPTION = """YouTube Playlist Aggregator (YTPA) is a tool to aggregate YouTube playlists.
At the moment YTPA supports adding videos from any number of users and/or playlists to another playlist."""
USERNAME_HELP = """user whose videos will be processed, you may specify this argument multiple times"""
PLAYLIST_HELP = """playlist of which the videos will be processed, you may specify this argument multiple times.
Must be specified in the form of \"username/playlistname\"."""
DESTINATION_HELP = """the playlist to which all videos will be added. It will be created if it doesn\'t exist"""

DEVELOPER_KEY = ''
USERNAME = ''
EMAIL_ADDRESS = ''


class YouTube:
    """Wrapper around Google's YouTube API, to make it a little
    less horrible to use. YMMV"""

    youtube_id_regex = re.compile('/([A-Za-z0-9_-]+)$')
    user_base_uri = 'http://gdata.youtube.com/feeds/api/users/%s/uploads'
    playlist_base_uri = 'http://gdata.youtube.com/feeds/api/playlists/%s'

    def __init__(self, developer_key, emailaddress, password):
        """Create a new YouTube instance. Get a developer key from
        http://code.google.com/apis/youtube/dashboard/. Email address
        and password refer to a regular YouTube account to log in as."""
        self.service = gdata.youtube.service.YouTubeService()
        self.developer_key = developer_key
        self.emailaddress = emailaddress
        self.password = password

    def authenticate(self):
        """Authenticate towards YouTube with the credentials passed
        during the instantiation of the YouTube class."""
        self.service.ssl = True
        self.service.developer_key = self.developer_key
        self.service.email = self.emailaddress
        self.service.password = self.password
        self.service.source = 'playlist-aggregator'
        self.service.ProgrammaticLogin()

    def playlist_id_from_uri(self, playlist_uri):
        """Return the id of the playlist url."""
        return re.search(self.youtube_id_regex, playlist_uri).group(1)

    def playlist_uri_from_id(self, playlist_id):
        """Return the uri for the playlist id."""
        return self.playlist_base_uri % playlist_id

    def playlist_id(self, username, playlist_name):
        """Return the playlist id for the given user/playlist combo.
        Return None if no such playlist exists."""
        playlists = self.service.GetYouTubePlaylistFeed(username=username)
        while playlists is not None:
            for playlist in playlists.entry:
                if playlist.title.text == playlist_name:
                    return self.playlist_id_from_uri(playlist.id.text)
            next_page = playlists.GetNextLink()
            if next_page is None:
                return None
            playlists = self.service.Query(next_page.href)

    def all_videos_of_user(self, username):
        """Return all videos uploaded by the user."""
        uri = self.user_base_uri % username
        feed = self.service.GetYouTubeVideoFeed(uri)
        all_videos = []
        while feed is not None:
            all_videos.extend([re.search(self.youtube_id_regex, video.id.text).group(1) for video in feed.entry])
            next_page = feed.GetNextLink()
            if next_page is None:
                break
            feed = self.service.Query(next_page.href)
        return all_videos

    def all_videos_of_playlist(self, playlist_id):
        """Return all videos of the playlist."""
        uri = self.playlist_uri_from_id(playlist_id)
        all_videos = self.service.GetYouTubePlaylistVideoFeed(uri=uri)
        return [re.search(self.youtube_id_regex, video.id.text).group(1)
                for video in all_videos.entry]

    def playlists_exists(self, playlist_id):
        """Return whether the playlist exists."""
        try:
            playlist_uri = self.playlist_uri_from_id(playlist_id)
            self.service.GetYouTubePlaylistVideoFeed(uri=playlist_uri)
            return True
        except RequestError:
            return False

    def create_playlist(self, name, description=None, private=False):
        """Create a playlist and return the playlist id.
        Will fail if the playlists already exists."""
        playlist = self.service.AddPlaylist(name, description)
        return self.playlist_id_from_uri(playlist.id.text)

    def add_video_to_playlist(self, video_id, playlist_id):
        """Add a video to a playlist. The playlist must be owned by
        the logged in user."""
        playlist_uri = self.playlist_uri_from_id(playlist_id)
        self.service.AddPlaylistVideoEntryToPlaylist(playlist_uri, video_id)

    def add_user_videos_to_playlist(self, user, playlist_id):
        """Add all videos uploaded by the user to the playlist."""
        all_videos = self.all_videos_of_user(user)
        for video_id in all_videos:
            self.add_video_to_playlist(video_id, playlist_id)


    def add_playlist_videos_to_playlist(self, source_playlist_id, destination_playlist_id):
        """Add all videos of the source playlist to the destination playlist."""
        all_videos = self.all_videos_of_playlist(source_playlist_id)
        for video_id in all_videos:
            self.add_video_to_playlist(video_id, destination_playlist_id)


def main():
    args = parse_args()

    password = getpass.getpass()
    youtube = YouTube(DEVELOPER_KEY, EMAIL_ADDRESS, password)
    print 'Logging in to YouTube ...'
    youtube.authenticate()

    print 'Getting playlist id for playlist %s ...' % args.destination_playlist
    destination_playlist_id = youtube.playlist_id(USERNAME, args.destination_playlist)

    if destination_playlist_id is None:
        print 'Playlist %s not found, creating it ...' % args.destination_playlist
        destination_playlist_id = youtube.create_playlist(args.destination_playlist)

    if args.username is not None:
        for user in args.username:
            print 'Adding videos of %s ...' % user
            youtube.add_user_videos_to_playlist(user, destination_playlist_id)

    if args.playlist is not None:
        for playlist in args.playlist:
            playlist_username, playlist_name = playlist.split('/')
            print 'Adding videos of %s\'s playlist %s ...' % (playlist_username, playlist_name)
            playlist_id = youtube.playlist_id(playlist_username, playlist_name)
            youtube.add_playlist_videos_to_playlist(playlist_id, destination_playlist_id)

    print 'Done.'

def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-u', '--username', help=USERNAME_HELP, action='append')
    parser.add_argument('-p', '--playlist', help=PLAYLIST_HELP, action='append')
    parser.add_argument('destination_playlist', help=DESTINATION_HELP)

    args = parser.parse_args()
    if args.username is None and args.playlist is None:
        parser.print_usage(file=sys.stderr)
        sys.stderr.write('At least one of --user or --playlist should be specified.\n')
        sys.exit(1)

    return args

if __name__ == '__main__':
    main()
