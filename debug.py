import boto3
from service.models import SpotifyTrack

spotify_track = SpotifyTrack('track_id', 'playlist_id', 'team_id')

print(spotify_track)

# client = boto3.resource('dynamodb', endpoint_url="http://localhost:4566")
# table = client.Table('dunces-app-local')
# table.put_item(Item={**{"PK": "one", "SK": "two"}, **{'blah': 'aha'}})
