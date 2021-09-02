from typing import List

from dacite import from_dict, Config
from dataclasses import dataclass

# from dunces.models import SpotifyTrack
#
# spotify_track = SpotifyTrack('track_id', 'playlist_id', 'team_id')
#
# print(spotify_track)

# client = boto3.resource('dynamodb', endpoint_url="http://localhost:4566")
# table = client.Table('dunces-app-local')
# table.put_item(Item={**{"PK": "one", "SK": "two"}, **{'blah': 'aha'}})


@dataclass
class A:
  x: int


@dataclass
class ListOfA:
  some_list: List[A]


print(from_dict(ListOfA, {"some_list": [{"x": 1}]}, config=Config(check_types=False, type_hooks={List: List})))
