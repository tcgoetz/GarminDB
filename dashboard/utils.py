def get_sport_icon(sport, empty=False):
    if sport == "running":
        return "🏃"
    elif sport == "hiking":
        return "🥾"
    else:
        return sport if not empty else ""


def timestamp_to_seconds(date):
    return date.hour * 3600 + date.minute * 60 + date.second


def timedelta_to_seconds(td):
    hours = td.seconds // 3600
    minutes = (td.seconds - hours) // 60
    seconds = td.seconds - (hours * 3600) - (minutes * 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
