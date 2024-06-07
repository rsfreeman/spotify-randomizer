import time
import datetime
import random
import sys
import argparse
from colorama import Fore
from colorama import just_fix_windows_console
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--playlist',
                    help='include user playlist (use multiple times for more than a single playlist)',
                    action='append')
parser.add_argument('-m', '--made-for-you',
                    help="include spotify's 'Made For You' playlists",
                    action='store_true')
parser.add_argument('-v', '--verbose',
                    help='print verbose track information',
                    action='store_true')
args = parser.parse_args()
arg_verbose = args.verbose
arg_made_for_you = args.made_for_you
arg_playlist = args.playlist

# necessary for ANSI color codes to work in windows
just_fix_windows_console()

# create spotipy instance
scope = ("user-library-read,user-read-playback-state,user-modify-playback-state,user-read-recently-played, \
         user-top-read, playlist-read-private")

# authenticate
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope), requests_timeout=5, retries=3)
except spotipy.oauth2.SpotifyOauthError:
    print("No client_id. Pass it or set a SPOTIPY_CLIENT_ID environment variable.")
    exit(1)


# redirect stderr from console
class DevNull:
    def write(self, msg):
        pass


sys.stderr = DevNull()


# return formatted date time
def get_datetime():
    date_time = datetime.datetime.now()
    fdate_time = date_time.strftime("%b %d %I:%M %p")
    return fdate_time


# returns active or inactive connected device in that order
def get_device():
    devices = sp.devices()['devices']
    this_device_id = None
    if any(devices):
        for device in devices:
            if device['is_active']:
                this_device_id = device['id']
        if not this_device_id:
            for device in devices:
                this_device_id = device['id']
    return this_device_id


# return a list of playlist ids
def get_playlist_ids():
    target_playlist_ids = list()
    if arg_playlist:
        for ap in arg_playlist:
            for p in sp.current_user_playlists()['items']:
                if ap.upper() == p['name'].upper():
                    target_playlist_ids.append(p['id'])
    if arg_made_for_you:
        mfy_category_id = "0JQ5DAt0tbjZptfcdMSKl3"
        mfy_playlists = sp.category_playlists(category_id=mfy_category_id)['playlists']['items']
        for item in mfy_playlists:
            if "Mix" not in item['name']:
                continue
            target_playlist_ids.append(item['id'])
    return target_playlist_ids


# return single track
def get_next_track(next_tracks: dict):
    i = random.randint(0, (len(next_tracks['tracks']) - 1))
    this_track = dict()
    this_track['uri'] = next_tracks['tracks'][i]['track']['uri']
    this_track['artist_name'] = next_tracks['tracks'][i]['track']['artists'][0]['name']
    this_track['album_name'] = next_tracks['tracks'][i]['track']['album']['name']
    this_track['track_name'] = next_tracks['tracks'][i]['track']['name']
    this_track['popularity'] = next_tracks['tracks'][i]['track']['popularity']
    this_track['playlist'] = next_tracks['playlist']
    return this_track


# return tracks from a list of playlist ids
def get_playlist_tracks(identifiers: list):
    i = random.randint(0, (len(identifiers) - 1))
    playlist_id = identifiers[i]
    playlist_name = sp.playlist(playlist_id, fields='name')['name']
    results = sp.playlist_items(playlist_id,
                                fields='next,items.track.id,items.track.name,items.track.popularity, '
                                       'items.track.uri,items.track.artists.name,items.track.album.name',
                                limit=100,
                                additional_types='track')
    playlist_tracks = dict()
    playlist_tracks['playlist'] = playlist_name
    playlist_tracks['tracks'] = list()
    playlist_tracks['tracks'].extend(results['items'])
    while results['next']:
        results = sp.next(results)
        playlist_tracks['tracks'].extend(results['items'])
    return playlist_tracks


device_id = get_device()
if not device_id:
    print("No devices found. Open Spotify on a device to start playback.")
    exit(1)
playlist_ids = get_playlist_ids()
if not playlist_ids:
    print("No playlists found.")
    exit(1)

played_tracks = list()
# loop forever queueing random tracks from random playlists
while True:
    queue = sp.queue()
    queued_tracks = len(queue['queue'])
    if queued_tracks < 20:
        tracks = get_playlist_tracks(playlist_ids)
        track = get_next_track(tracks)
        if not sp.current_playback() and len(played_tracks) == 0:
            sp.start_playback(device_id=device_id, uris=[track['uri']])
            played_tracks.append(track['uri'])
        elif track['uri'] in played_tracks:
            continue
        else:
            try:
                sp.add_to_queue(uri=track['uri'])
            except spotipy.exceptions.SpotifyException:
                try:
                    sp.add_to_queue(device_id=device_id, uri=track['uri'])
                except spotipy.exceptions.SpotifyException:
                    print("No devices found. Open Spotify on a device to start playback.")
                    exit(1)
            played_tracks.append(track['uri'])
        if arg_verbose:
            curr_time = get_datetime()
            print(Fore.LIGHTYELLOW_EX + f"TIME:", Fore.LIGHTWHITE_EX + f"{curr_time}",
                  Fore.LIGHTYELLOW_EX + f"TRACK:", Fore.LIGHTWHITE_EX + f"{track['track_name']}",
                  Fore.LIGHTYELLOW_EX + f"ALBUM:", Fore.LIGHTWHITE_EX + f"{track['album_name']}",
                  Fore.LIGHTYELLOW_EX + f"ARTIST:", Fore.LIGHTWHITE_EX + f"{track['artist_name']}",
                  Fore.LIGHTYELLOW_EX + f"POPULARITY:", Fore.LIGHTWHITE_EX + f"{track['popularity']}",
                  Fore.LIGHTYELLOW_EX + f"PLAYLIST:", Fore.LIGHTWHITE_EX + f"{track['playlist']}", Fore.RESET)
    time.sleep(3)
