import base64
import json
import os
import requests
import spotipy

from dunces.models import SlackUser, SpotifyTrack
from dunces.helpers.secure import CipherSuite


class SpotifyApi(object):
    def __init__(self,
                 slack_user: SlackUser,
                 cipher_suite: CipherSuite,
                 client_id=os.environ['SPOTIFY_CLIENT_ID'],
                 client_secret=os.environ['SPOTIFY_CLIENT_SECRET']):
        self.user_name = cipher_suite.decrypt(slack_user.spotify_user_name_encrypt)
        auth_manager = SpotifyAuthManager(
            client_id,
            client_secret,
            cipher_suite.decrypt(slack_user.spotify_refresh_token_encrypt)
        )
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

    def add_track(self, playlist_id, track: SpotifyTrack):
        self.spotify.user_playlist_add_tracks(self.user_name,
                                              playlist_id,
                                              [track.spotify_track_id])

    def fetch_track_ids(self, playlist_id):
        tracks = []
        offset = 0
        while True:
            print(f'Fetching playlist {playlist_id} from offset {offset}')
            response = self.spotify.user_playlist_tracks(
                user=self.user_name,
                playlist_id=playlist_id,
                # fields='tracks.items(track(name,id,album(name,href),artists(id,name)))')
                fields='items(track(id))',
                limit=100,  # Max is 100
                offset=offset
            )

            offset += 100
            new_track_ids = list(map(lambda item: item['track']['id'], response['items']))
            tracks = tracks + new_track_ids
            if len(new_track_ids) < 100:
                print(f'Found {len(tracks)} tracks')
                return tracks


class SpotifyAuthManager:
    def __init__(self, client_id, client_secret, user_refresh_token):
        auth_header = base64.b64encode(str(client_id + ':' + client_secret).encode())
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + auth_header.decode()
        }
        self.data = {
            'grant_type': 'refresh_token',
            'refresh_token': user_refresh_token
        }

    def get_access_token(self, as_dict=False):
        try:
            return self._fetch_token()
        except Exception:
            print('Fetching token failed once, trying again.')
            return self._fetch_token()

    def _fetch_token(self):
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=self.headers,
            data=self.data)
        data = json.loads(response.text)
        return data['access_token']
