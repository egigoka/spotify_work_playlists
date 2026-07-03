import spotipy
from commands import *

password = Str.input_pass()

client_id = [29, -23, -3, -21, -56, -9, -45, 1, 16, 67, -14, -16, -53, 26, -9, -59, -41, 51, 67, 18, 31, -21, -4,
             -20, -62, -10, -44, 0, 16, 66, -18, 29]
client_id = Str.decrypt(client_id, password)

client_secret = [32, -19, -48, -15, -61, -51, 0, 3, 18, 21, -20, 28, -53, 30, -60, -55, 0, 49, 19, 16, -20, -14,
                 -7, 31, -11, -7, -42, 3, 16, 22, -21, -19]
client_secret = Str.decrypt(client_secret, password)

del password

sp = spotipy.Spotify(auth_manager=spotipy.oauth2.SpotifyOAuth(client_id=client_id,
                                                              client_secret=client_secret,
                                                              redirect_uri="https://spotipy.egigoka.me",
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


def clear_playlist(playlist_uri):
    cnt = 0
    while True:
        results = sp.playlist_items(playlist_id=playlist_uri, limit=100, offset=0)
        if not results['items']:
            break

        uris = []
        for item in results['items']:
            track = item['track']
            if track:
                uris.append(track['uri'])

        if uris:
            sp.playlist_remove_all_occurrences_of_items(playlist_uri, uris)
        cnt += len(results['items'])
        Print.rewrite("removed", cnt, "songs")


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
for playlist in excluded_playlists:
    excluded_track_uris.update(get_playlist_track_uris(playlist['uri']))

Print.colored(f"excluded {len(excluded_track_uris)} songs", "yellow")

clear_playlist(selected_playlist)

offset = 0
cnt = 0
added_cnt = 0

while True:
    # get 50 songs from liked playlist
    results = sp.current_user_saved_tracks(limit=50, offset=offset)
    if not results['items']:
        break
    uris = []
    for idx, item in enumerate(results['items']):
        track = item['track']
        cnt = idx + offset + 1
        # print(idx + offset + 1, track['artists'][0]['name'], " – ", track['name'], track['uri'])
        # Print.prettify(track)
        if track['uri'] not in excluded_track_uris:
            uris.append(track['uri'])

    if uris:
        # add songs to playlist in same order as liked songs
        sp.playlist_add_items(selected_playlist, uris, position=added_cnt)
        added_cnt += len(uris)
    Print.rewrite(f"processed {cnt} songs")
    offset += len(results['items'])

print(f"processed {cnt} songs, added {added_cnt} songs")
