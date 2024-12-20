import os
import sys
import time
import random
import argparse
import datetime
import platform
from colorama import Fore
from colorama import just_fix_windows_console
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--playlist',
                    help='include user playlist (use multiple times for more than a single playlist)',
                    action='append')
parser.add_argument('-A', '--all-user-playlists',
                    help='include all user playlists',
                    action='store_true')
parser.add_argument('-m', '--made-for-you',
                    help="include spotify's 'Made For You' playlists",
                    action='store_true')
parser.add_argument('-v', '--verbose',
                    help='print verbose track information',
                    action='store_true')
parser.add_argument('-q', '--clear-the-queue',
                    help='clear the  queue',
                    action='store_true')
parser.add_argument('-s', '--save-tracks',
                    help='save a record of played tracks between listening sessions and do not repeat.',
                    action='store_true')
parser.add_argument('-C', '--clear-saved-tracks',
                    help='clear saved track information',
                    action='store_true')
parser.add_argument('-d', '--debug',
                    help='show error messages',
                    action='store_true')

args = parser.parse_args()
arg_verbose = args.verbose
arg_made_for_you = args.made_for_you
arg_clear_the_queue = args.clear_the_queue
arg_playlist = args.playlist
arg_all_user_playlists = args.all_user_playlists
arg_save_tracks = args.save_tracks
arg_clear_saved_tracks = args.clear_saved_tracks
arg_debug = args.debug


# supress error messages
class DevNull:
    def write(self, msg):
        pass


# return formatted date time
def get_datetime():
    date_time = datetime.datetime.now()
    fdate_time = date_time.strftime("%b %d %I:%M %p")
    return fdate_time


# returns active or inactive connected device in that order
def get_device(wait=False):
    try:
        devices = sp.devices()['devices']
        target_device_id = None
        if any(devices):
            for device in devices:
                if device['is_active']:
                    target_device_id = device['id']
            if not target_device_id:
                for device in devices:
                    target_device_id = device['id']
        if wait and target_device_id is None:
            print(Fore.LIGHTRED_EX + "Open Spotify on a device to start playback. <Ctrl-C to quit>\nWaiting for device...",
                  Fore.RESET, end='', flush=True)
            while target_device_id is None:
                time.sleep(3)
                target_device_id = get_device()
            print(Fore.LIGHTRED_EX + "done.", Fore.RESET)
    except:
        get_device()
    return target_device_id


# clear the queue (experimental)
def clear_the_queue():
    # sp.start_playback(device_id=get_device(wait=True))
    this_queue = sp.queue()
    if len(this_queue['queue']) != 0:
        print("clearing", len(this_queue['queue']) - 10, "tracks in queue")
        while len(this_queue['queue']) > 10:
            sp.next_track(device_id=device_id)
            print(len(this_queue['queue']) - 10)
            this_queue = sp.queue()
        print("queue cleared")


# return a list of playlist ids
def get_playlist_ids():
    target_playlist_ids = list()
    if arg_playlist:
        for ap in arg_playlist:
            # todo: this is too slow
            for i, p in enumerate(sp.current_user_playlists()['items']):
                if ap.upper() == p['name'].upper():
                    target_playlist_ids.append(p['id'])
                    break
                if i == len(sp.current_user_playlists()['items']) - 1:
                    print(f"playlist {ap} not found")
    if arg_all_user_playlists:
        for p in sp.current_user_playlists()['items']:
            if p['name'] == 'DJ':
                continue
            target_playlist_ids.append(p['id'])
    if arg_made_for_you:
        try:
            print("Attempting to collect playlists from Spotify's Made For You category...")
            mfy_category_id = "0JQ5DAUnp4wcj0bCb3wh3S"
            mfy_playlists = sp.category_playlists(category_id=mfy_category_id)['playlists']['items']
            for item in mfy_playlists:
                if "Mix" not in item['name']:
                    continue
                target_playlist_ids.append(item['id'])
        except spotipy.exceptions.SpotifyException:
            print("Spotify nerfed access to playlists created by Spotify. Thanks Spotify! ¯\\_(ツ)_/¯")
    return target_playlist_ids


# return single track
def get_next_track(next_tracks: dict):
    i = random.randint(0, (len(next_tracks['tracks']) - 1))
    target_track = dict()
    target_track['uri'] = next_tracks['tracks'][i]['track']['uri']
    target_track['artist_name'] = next_tracks['tracks'][i]['track']['artists'][0]['name']
    target_track['album_name'] = next_tracks['tracks'][i]['track']['album']['name']
    target_track['track_name'] = next_tracks['tracks'][i]['track']['name']
    target_track['popularity'] = next_tracks['tracks'][i]['track']['popularity']
    target_track['playlist'] = next_tracks['playlist']
    return target_track


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


# main
# supress stderr unless debug param is present
if not arg_debug:
    sys.stderr = DevNull()

# create spotipy instance
scope = ("user-library-read,user-read-playback-state,user-modify-playback-state,user-read-recently-played, \
         user-top-read, playlist-read-private")
try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope), requests_timeout=5, retries=3)
except spotipy.oauth2.SpotifyOauthError:
    print("No client_id. Pass it or set a SPOTIPY_CLIENT_ID environment variable.")
    exit(1)

# necessary for ANSI color codes to work in windows
if platform.system() == 'Windows':
    just_fix_windows_console()

# list to record played tracks
played_tracks = list()

# currently playing track
currently_playing = None

# where to save played tracks between listening sessions
script_path = os.path.dirname(os.path.realpath(__file__))
saved_tracks_file = os.path.join(script_path, 'played_tracks.txt')

# get spotify device id
device_id = get_device()
# get a list of playlist ids
playlist_ids = get_playlist_ids()
if not playlist_ids:
    print("No playlists found.")
    exit(1)

# clear the queue (experimental)
if arg_clear_the_queue:
    clear_the_queue()

# clear saved track info
if arg_clear_saved_tracks:
    if os.path.exists(saved_tracks_file):
        os.remove(saved_tracks_file)

# import or create saved track information
if arg_save_tracks:
    print(Fore.LIGHTYELLOW_EX + f"saving tracks to: {saved_tracks_file}", Fore.RESET)
    try:
        with open(saved_tracks_file, 'r') as f:
            played_tracks.extend([line.strip() for line in f])
    except FileNotFoundError:
        with open(saved_tracks_file, 'w') as f:
            pass

# loop forever queueing random tracks from random playlists
while True:
    try:
        queue = sp.queue()
        queued_tracks = len(queue['queue'])
        if queued_tracks < 20:
            tracks = get_playlist_tracks(playlist_ids)
            track = get_next_track(tracks)
            if not sp.current_playback():
                sp.start_playback(device_id=device_id, uris=[track['uri']])
                played_tracks.append(track['uri'])
            elif track['uri'] in played_tracks:
                continue
            else:
                sp.add_to_queue(uri=track['uri'])
                played_tracks.append(track['uri'])
            if arg_save_tracks:
                time.sleep(1)
                if sp.currently_playing()['item']['uri'] != currently_playing:
                    with open(saved_tracks_file, 'a') as f:
                        currently_playing = sp.currently_playing()['item']['uri']
                        f.write(currently_playing + "\n")
            if arg_verbose:
                current_time = get_datetime()
                print(Fore.LIGHTYELLOW_EX + f"TIME:", Fore.LIGHTWHITE_EX + f"{current_time}",
                      Fore.LIGHTYELLOW_EX + f"TRACK:", Fore.LIGHTWHITE_EX + f"{track['track_name']}",
                      Fore.LIGHTYELLOW_EX + f"ALBUM:", Fore.LIGHTWHITE_EX + f"{track['album_name']}",
                      Fore.LIGHTYELLOW_EX + f"ARTIST:", Fore.LIGHTWHITE_EX + f"{track['artist_name']}",
                      Fore.LIGHTYELLOW_EX + f"POPULARITY:", Fore.LIGHTWHITE_EX + f"{track['popularity']}",
                      Fore.LIGHTYELLOW_EX + f"PLAYLIST:", Fore.LIGHTWHITE_EX + f"{track['playlist']}", Fore.RESET)
        time.sleep(3)
    except:
        device_id = get_device(wait=True)
