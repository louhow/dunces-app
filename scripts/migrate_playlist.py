from default_settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from service.dao import Dao
from service.models import SpotifyTrack

dao = Dao('dunces-app-prod', AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

dao.insert_spotify_track(SpotifyTrack('spotify_track_id', 'slack_team_id', 'slack_user_id', 'create_time', 'spotify_playlist_id'))

