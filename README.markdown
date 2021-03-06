YouTube Playlist Aggregator
===========================

YouTube Playlist Aggregator (YTPA) is a tool to aggregate YouTube playlists.
At the moment YTPA supports adding videos from any number of users and/or
playlists to another playlist.


Usage
-----

<pre>
usage: ytpa.py [-h] [-u USERNAME] [-p PLAYLIST] destination_playlist

positional arguments:
  destination_playlist  the playlist to which all videos will be added. It
                        will be created if it doesn't exist

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        user whose videos will be processed, you may specify
                        this argument multiple times
  -p PLAYLIST, --playlist PLAYLIST
                        playlist of which the videos will be processed, you
                        may specify this argument multiple times. Must be
                        specified in the form of "username/playlistname".
  --private             if the destination playlist does not yet exist, create
                        it as a private playlist. Default is a public
                        playlist.
</pre>


License
-------

This program is free software. It comes without any warranty, to the extent
permitted by applicable law. You can redistribute it and/or modify it under
the terms of the Do What The Fuck You Want To Public License, Version 2, as
published by Sam Hocevar.
See http://sam.zoy.org/wtfpl/COPYING for more details.
