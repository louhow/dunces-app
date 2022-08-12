from datetime import datetime, timezone

import pytz


def get_datetime():
  return datetime.now(timezone.utc).isoformat()


class DateFormatter:
  @staticmethod
  def to_date(iso_time):
    return datetime.fromisoformat(iso_time) \
      .replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Central')) \
      .strftime('%b %-d, %Y')
