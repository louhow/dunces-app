from dunces.dao.dynamo_dao import DuplicateItemException
from dunces.handlers.slack_event import DEFAULT_SLACK_USER
from dunces.models.slack import SlackChannel, SlackRequest
from dunces.models.spotify import SpotifyTrack
from dunces.services.clients.spotify import SpotifyClient


class SlackChannelMissingPlaylistException(Exception):
  def __init__(self, team_id, channel_id):
    self.team_id = team_id
    self.channel_id = channel_id
  

class SpotifyService:
  def __init__(self, dao, cipher_suite):
    self.dao = dao
    self.cipher_suite = cipher_suite
  
  def insert_spotify_track(self, req: SlackRequest, spotify_track_id) -> SpotifyTrack or None:
    """
    Creates an audit record and adds a spotify track ID to a playlist
    :param req: SlackRequest
    :param spotify_track_id: the ID of the spotify track
    :return: the inserted SpotifyTrack, if it was added. None if the same SlackRequest was processed twice
    :raises DuplicateItemException[SpotifyTrack]: When somebody is trying to uniquely add the same spotify track twice
    :raises SlackChannelMissingPlaylistException: when the requested team/channel does not have a default playlist
    """
    # TODO move this out to a Slack service
    slack_channel = self.dao.get_item(SlackChannel(req.team_id, req.channel_id))
    if slack_channel is None:
      raise SlackChannelMissingPlaylistException(req.team_id, req.channel_id)
  
    spotify_track = SpotifyTrack(spotify_track_id,
                                 slack_channel.spotify_playlist_id,
                                 req.team_id,
                                 req.user_id,
                                 req.event_timestamp)
    try:
      self.dao.insert_item(spotify_track)
    except DuplicateItemException as e:
      # Lambda cold boots may result in slack sending the same event multiple times, so
      # only send a message if this isn't a dupe
      if req.event_timestamp != e.get_existing_item().slack_timestamp:
        raise e
      else:
        return None
  
    spotify_api = SpotifyClient(DEFAULT_SLACK_USER, self.cipher_suite)
    spotify_api.add_track(slack_channel.spotify_playlist_id, spotify_track)
    return spotify_track
