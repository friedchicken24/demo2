from flask import url_for
from datetime import datetime

def format_date(date):
    """Format date for display in admin interface."""
    if date is None:
        return "Not set"
    return date.strftime("%Y-%m-%d")

def format_datetime(dt):
    """Format datetime for display in admin interface."""
    if dt is None:
        return "Not set"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_anime_status_badge_class(status):
    """Return appropriate Bootstrap badge class for anime status."""
    status_map = {
        'finished_airing': 'success',
        'currently_airing': 'primary',
        'not_yet_aired': 'warning',
        'cancelled': 'danger',
        'on_hiatus': 'secondary'
    }
    return f"badge bg-{status_map.get(status, 'light')}"

def get_manga_status_badge_class(status):
    """Return appropriate Bootstrap badge class for manga status."""
    status_map = {
        'finished_publishing': 'success',
        'currently_publishing': 'primary',
        'not_yet_published': 'warning',
        'on_hiatus': 'secondary',
        'discontinued': 'danger'
    }
    return f"badge bg-{status_map.get(status, 'light')}"

def get_role_badge_class(role_name):
    """Return appropriate Bootstrap badge class for role."""
    role_map = {
        'admin': 'danger',
        'moderator': 'warning',
        'editor': 'info',
        'user': 'secondary'
    }
    return f"badge bg-{role_map.get(role_name, 'light')}"

def truncate_text(text, max_length=100):
    """Truncate text to specified length, adding ellipsis if needed."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def format_anime_type(anime_type):
    """Return formatted anime type."""
    return anime_type if anime_type else "Unknown"

def format_manga_type(manga_type):
    """Return formatted manga type."""
    return manga_type if manga_type else "Unknown"

def format_anime_status(status):
    """Format anime status for display."""
    status_map = {
        'finished_airing': 'Finished Airing',
        'currently_airing': 'Currently Airing',
        'not_yet_aired': 'Not Yet Aired',
        'cancelled': 'Cancelled',
        'on_hiatus': 'On Hiatus'
    }
    return status_map.get(status, "Unknown")

def format_manga_status(status):
    """Format manga status for display."""
    status_map = {
        'finished_publishing': 'Finished Publishing',
        'currently_publishing': 'Currently Publishing',
        'not_yet_published': 'Not Yet Published',
        'on_hiatus': 'On Hiatus',
        'discontinued': 'Discontinued'
    }
    return status_map.get(status, "Unknown")

def get_creator_role_badge(role):
    """Return appropriate Bootstrap badge for creator role."""
    role_map = {
        'author': 'badge bg-info',
        'artist': 'badge bg-success',
        'author_artist': 'badge bg-primary'
    }
    return role_map.get(role, 'badge bg-secondary')

def format_creator_role(role):
    """Format creator role for display."""
    role_map = {
        'author': 'Author',
        'artist': 'Artist',
        'author_artist': 'Author & Artist'
    }
    return role_map.get(role, "Unknown")
