from datetime import datetime
import pytz
from tzlocal import get_localzone


def get_time_now_utc():
    return datetime.now(pytz.utc)


def convert_time_to_utc(timestamp):
    # Convert timestamp to UTC and then to the machine's local timezone
    timestamp_utc = datetime.strptime(timestamp, 
                                      "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
    return timestamp_utc


def convert_to_local_time(timestamp_utc: datetime):
    # Get the system's local time zone
    local_tz = get_localzone()
    timestamp_local = timestamp_utc.astimezone(local_tz)
    return timestamp_local


def convert_time_to_display(timestamp: datetime) -> str:
    # Format the timestamp to display only minutes and seconds
    return timestamp.strftime('%H:%M:%S')

