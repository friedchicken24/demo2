from flask import url_for
from models import (
    User, Anime, Manga, Genre, Studio, Creator, 
    Fanart, Fanfiction, Comment, Rating, Tag, ContentTag,
    UserList, ListItem, AnimeSong
)

def get_anime_cover_or_placeholder(anime):
    """Return anime cover image or a placeholder."""
    if anime.cover_image_url:
        return anime.cover_image_url
    return url_for('static', filename='img/anime_placeholder.svg')

def get_manga_cover_or_placeholder(manga):
    """Return manga cover image or a placeholder."""
    if manga.cover_image_url:
        return manga.cover_image_url
    return url_for('static', filename='img/manga_placeholder.svg')

def get_user_avatar_or_placeholder(user):
    """Return user avatar or a placeholder."""
    if user.profile_picture_url:
        return user.profile_picture_url
    return url_for('static', filename='img/user_placeholder.svg')

def format_anime_status(status):
    """Format anime status for display."""
    status_map = {
        'finished_airing': 'Finished Airing',
        'currently_airing': 'Currently Airing',
        'not_yet_aired': 'Not Yet Aired',
        'cancelled': 'Cancelled',
        'on_hiatus': 'On Hiatus'
    }
    return status_map.get(status, status)

def format_manga_status(status):
    """Format manga status for display."""
    status_map = {
        'finished_publishing': 'Finished Publishing',
        'currently_publishing': 'Currently Publishing',
        'not_yet_published': 'Not Yet Published',
        'on_hiatus': 'On Hiatus',
        'discontinued': 'Discontinued'
    }
    return status_map.get(status, status)

def format_list_item_status(status):
    """Format list item status for display."""
    status_map = {
        'watching': 'Watching',
        'completed': 'Completed',
        'on_hold': 'On Hold',
        'dropped': 'Dropped',
        'plan_to_watch': 'Plan to Watch',
        'reading': 'Reading',
        'completed_manga': 'Completed',
        'on_hold_manga': 'On Hold',
        'dropped_manga': 'Dropped',
        'plan_to_read': 'Plan to Read'
    }
    return status_map.get(status, status)

def get_user_content_rating(user_id, content_type, content_id):
    """Get a user's rating for specific content."""
    return Rating.query.filter_by(
        user_id=user_id,
        content_type=content_type,
        content_id=content_id
    ).first()

def get_content_tags(content_type, content_id):
    """Get tags for specific content."""
    content_tags = ContentTag.query.filter_by(
        content_type=content_type,
        content_id=content_id
    ).all()
    
    tags = []
    for content_tag in content_tags:
        tags.append(content_tag.tag)
    
    return tags

def check_item_in_any_list(user_id, content_type, content_id):
    """Check if item exists in any of user's lists."""
    user_lists = UserList.query.filter_by(user_id=user_id).all()
    
    for user_list in user_lists:
        item = ListItem.query.filter_by(
            list_id=user_list.list_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if item:
            return True, user_list, item
    
    return False, None, None

def truncate_text(text, max_length=100):
    """Truncate text to specified length."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'
