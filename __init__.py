import os
import spotipy
from spotipy.cache_handler import CacheFileHandler
from commands import *

password = Str.input_pass()

client_id = [29, -23, -3, -21, -56, -9, -45, 1, 16, 67, -14, -16, -53, 26, -9, -59, -41, 51, 67, 18, 31, -21, -4,
             -20, -62, -10, -44, 0, 16, 66, -18, 29]
client_id = Str.decrypt(client_id, password)

client_secret = [32, -19, -48, -15, -61, -51, 0, 3, 18, 21, -20, 28, -53, 30, -60, -55, 0, 49, 19, 16, -20, -14,
                 -7, 31, -11, -7, -42, 3, 16, 22, -21, -19]
client_secret = Str.decrypt(client_secret, password)

del password

_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")

sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyOAuth(client_id=client_id,
                                                              client_secret=client_secret,
                                                              redirect_uri="https://spotipy.egigoka.me",
                                                              cache_handler=CacheFileHandler(cache_path=_cache_path),
                                                              scope="ugc-image-upload "
                                                                    "user-read-recently-played "
                                                                    "user-read-playback-position "
                                                                    "user-top-read "
                                                                    "playlist-modify-private "
                                                                    "playlist-read-collaborative "
                                                                    "playlist-read-private "
                                                                    "playlist-modify-public "
                                                                    "streaming "
                                                                    "app-remote-control "
                                                                    "user-read-email "
                                                                    "user-read-private "
                                                                    "user-follow-read "
                                                                    "user-follow-modify "
                                                                    "user-library-modify "
                                                                    "user-library-read "
                                                                    "user-read-currently-playing "
                                                                    "user-read-playback-state "
                                                                    "user-modify-playback-state"))

del client_id
del client_secret

def get_all_playlists():
    results = sp.current_user_playlists(limit=50)
    playlists = []
    while results:
        playlists += results['items']
        results = sp.next(results) if results['next'] else None
    return playlists


def get_playlist(name, playlists):
    for playlist in playlists:
        if playlist['name'].lower() == name.lower():
            Print.colored(f"selected {playlist['name']}", "green")
            return playlist
    Print.colored(f"playlist not found: {repr(name)}", "red")
    return None


def get_playlist_track_uris(playlist_uri):
    results = sp.playlist_items(playlist_id=playlist_uri, limit=100, offset=0)
    uris = []
    while results:
        for item in results['items']:
            track = item['track']
            if track:
                uris.append(track['uri'])
        results = sp.next(results) if results['next'] else None
    return uris


def get_all_liked_uris():
    offset = 0
    uris = []
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        if not results['items']:
            break
        for item in results['items']:
            track = item['track']
            if track:
                uris.append(track['uri'])
        offset += len(results['items'])
        Print.rewrite(f"fetched {offset} liked songs")
    return uris


def flush_batch(batch, batch_start_pos):
    for i in range(0, len(batch), 100):
        sp.playlist_add_items(selected_playlist, batch[i:i + 100], position=batch_start_pos + i)
        Print.rewrite(f"inserted up to position {batch_start_pos + i + min(100, len(batch) - i)}")


playlists = get_all_playlists()
target_playlist = get_playlist("работа?", playlists)
excluded_playlists = [
    get_playlist("работа", playlists),
    get_playlist("!работа", playlists),
]

if not target_playlist:
    for idx, playlist in enumerate(playlists):
        print(idx, playlist['name'])
    target_playlist = CLI.get_int("select playlist to add filtered liked songs")
    target_playlist = playlists[target_playlist]

excluded_playlists = [playlist for playlist in excluded_playlists if playlist]
selected_playlist = target_playlist['uri']

excluded_track_uris = set()
excluded_counts = {}
for playlist in excluded_playlists:
    uris = get_playlist_track_uris(playlist['uri'])
    excluded_track_uris.update(uris)
    excluded_counts[playlist['name']] = len(uris)
Print.colored(f"excluded {len(excluded_track_uris)} songs from {len(excluded_playlists)} playlists", "yellow")

Print.colored("fetching current playlist...", "cyan")
current_uris = get_playlist_track_uris(selected_playlist)
current_set = set(current_uris)

Print.colored("fetching liked songs...", "cyan")
liked_uris = get_all_liked_uris()
target_uris = [u for u in liked_uris if u not in excluded_track_uris]
target_set = set(target_uris)

to_remove = [u for u in current_uris if u not in target_set]
to_add_set = {u for u in target_uris if u not in current_set}

Print.colored(f"diff: -{len(to_remove)} +{len(to_add_set)}", "yellow")

if not to_remove and not to_add_set:
    print("playlist already up to date")
else:
    for i in range(0, len(to_remove), 100):
        batch = to_remove[i:i + 100]
        sp.playlist_remove_all_occurrences_of_items(selected_playlist, batch)
        Print.rewrite(f"removed {min(i + 100, len(to_remove))}/{len(to_remove)}")

    # insert missing songs at correct positions preserving liked-song order
    after_remove_set = current_set - set(to_remove)
    actual_pos = 0
    batch = []
    batch_start_pos = 0

    for uri in target_uris:
        if uri in after_remove_set:
            if batch:
                flush_batch(batch, batch_start_pos)
                actual_pos += len(batch)
                batch = []
            actual_pos += 1
        elif uri in to_add_set:
            if not batch:
                batch_start_pos = actual_pos
            batch.append(uri)

    if batch:
        flush_batch(batch, batch_start_pos)

    print(f"done: removed {len(to_remove)}, added {len(to_add_set)}")

print(f"\nliked songs:      {len(liked_uris)}")
for name, count in excluded_counts.items():
    print(f"{name + ':':18s} {count}")
print(f"{target_playlist['name'] + ':':18s} {len(target_uris)}")
