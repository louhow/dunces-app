from settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from dunces.helpers.dao import Dao

dao = Dao('the-app-dev', AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
tracks = []

for idx, track in enumerate(tracks):
  print(f'inserted {track}')
  dao.insert_spotify_track(track)
