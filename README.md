# spotify-random

Endlessly queue random tracks from random playlists. Includes option to mix Spotify 'Made for You' playlists.

### Requires python3 and the modules below

    python3 -m pip install spotipy colorama 


### Set environment variables


[Spotipy Documentation](https://spotipy.readthedocs.io/en/2.24.0/#getting-started)

**Windows**

    $env:SPOTIPY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
    $env:SPOTIPY_CLIENT_SECRET='YOUR_SPOTIFY_CIENT_SECRET'  
    $env:SPOTIPY_REDIRECT_URI='http://localhost:8080'  

**Linux**

    export SPOTIPY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
    export SPOTIPY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET'
    export SPOTIPY_REDIRECT_URI='http://localhost'

**Options**

      -p PLAYLIST, --playlist PLAYLIST    include user playlist (use multiple times for more than a single playlist)
      -A, --all-user-playlists            include all user playlists
      -m, --made-for-you                  include spotify's 'Made For You' playlists
      -v, --verbose                       print verbose track information
      -q, --clear-the-queue               clear the queue (experimental)
      -s, --save-tracks                   save a record of played tracks between listening sessions and do not repeat.
      -C, --clear-saved-tracks            clear saved track information
      -d, --debug                         show error messages

**Examples**

Play a mix of songs from all user playlists and print verbose track information

    python3 .\spotify-random.py -A -v

Play a mix of songs from playlist1 and playlist2. Include Spotify *Made For You* playlists. Save tracks and print verbose track information

    python3 .\spotify-random.py -p playlist1 -p playlist2 -m -s -v
