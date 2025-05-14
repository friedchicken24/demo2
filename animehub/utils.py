import os
import secrets
import string
from datetime import datetime # Removed timedelta as it's not used here
from functools import wraps

from flask import flash, redirect, url_for, request, abort # Added request
from flask_login import current_user

# db will be imported locally in functions that need to commit

def generate_token(length=32):
    """Generate a secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def role_required(role_name):
    """Decorator to restrict access to users with a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('user.login', next=request.path))

            if not hasattr(current_user, 'roles'):
                 flash('User object is missing role information. Please contact an administrator.', 'danger')
                 abort(403) # Or redirect to an error page

            user_role_names = [role.role_name for role in current_user.roles]
            if role_name not in user_role_names:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def any_role_required(role_names): # role_names should be a list or tuple
    """Decorator to restrict access to users with any of the specified roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('user.login', next=request.path))

            if not hasattr(current_user, 'roles'):
                 flash('User object is missing role information. Please contact an administrator.', 'danger')
                 abort(403)

            user_role_names = [role.role_name for role in current_user.roles]
            if not any(role in user_role_names for role in role_names):
                flash('You do not have permission to access this page.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def update_last_login(user_obj): # Renamed user to user_obj to avoid conflict if datetime.user is ever a thing
    """Update user's last login timestamp.
    The caller is responsible for db.session.commit().
    """
    if user_obj:
        user_obj.last_login_at = datetime.utcnow()
    # No db.session.commit() here.

def count_words(text):
    """Count the number of words in a text."""
    if not text or not isinstance(text, str):
        return 0
    return len(text.split())

def get_user_lists(user_id): # This function might be redundant if user.user_lists is used.
    """Get all lists for a user."""
    from models import UserList # Local import
    return UserList.query.filter_by(user_id=user_id).order_by(UserList.is_main_list.desc(), UserList.list_name).all()

def format_datetime_display(dt_obj): # Renamed to be more specific
    """Format datetime for display."""
    if not dt_obj:
        return "N/A" # Or an empty string, or "Not set"
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

def format_date_display(dt_obj): # Renamed to be more specific
    """Format date for display."""
    if not dt_obj:
        return "N/A" # Or an empty string, or "Not set"
    return dt_obj.strftime("%Y-%m-%d")

def get_or_create_default_user_lists(user_id):
    """
    Ensures a user has the default lists (e.g., Watching, Reading).
    This function handles its own db.session.commit().
    Assumes UserList model does NOT have a specific 'list_type' (anime/manga).
    If it did, logic here would need to set that.
    """
    from models import UserList # Local import
    from app import db         # Local import for commit

    # Simplified default lists, assuming they are generic for now.
    # If UserList had a 'type' (anime/manga), this structure would be different.
    default_list_definitions = [
        {'name': 'Watching', 'is_main': True, 'description_suffix': 'anime series and movies.'},
        {'name': 'Completed', 'is_main': True, 'description_suffix': 'anime series and movies.'},
        {'name': 'On Hold', 'is_main': True, 'description_suffix': 'anime series and movies.'},
        {'name': 'Dropped', 'is_main': True, 'description_suffix': 'anime series and movies.'},
        {'name': 'Plan to Watch', 'is_main': True, 'description_suffix': 'anime series and movies.'},
        {'name': 'Reading', 'is_main': True, 'description_suffix': 'manga and light novels.'},
        {'name': 'Completed Reading', 'is_main': True, 'description_suffix': 'manga and light novels.'}, # Differentiated name
        {'name': 'On Hold Reading', 'is_main': True, 'description_suffix': 'manga and light novels.'}, # Differentiated name
        {'name': 'Dropped Reading', 'is_main': True, 'description_suffix': 'manga and light novels.'}, # Differentiated name
        {'name': 'Plan to Read', 'is_main': True, 'description_suffix': 'manga and light novels.'},
    ]

    created_lists = []
    lists_to_add_to_session = []

    for list_data in default_list_definitions:
        existing_list = UserList.query.filter_by(
            user_id=user_id,
            list_name=list_data['name']
        ).first()

        if not existing_list:
            new_list = UserList(
                user_id=user_id,
                list_name=list_data['name'],
                description=f"Default list for your {list_data['name'].lower()} {list_data['description_suffix']}",
                is_public=True, # Default to public, user can change
                is_main_list=list_data['is_main']
            )
            lists_to_add_to_session.append(new_list)
            created_lists.append(new_list) # Keep track of newly created list objects

    if lists_to_add_to_session:
        db.session.add_all(lists_to_add_to_session)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Consider logging this error
            current_app.logger.error(f"Error creating default user lists for user_id {user_id}: {e}")
            # Depending on desired behavior, you might re-raise or handle gracefully
            # For now, we'll let it pass, and the function will return fewer (or no) created_lists.
    return created_lists


def update_content_stats(content_type, content_id):
    """
    Update content statistics like average score and member count.
    This function handles its own db.session.commit().
    """
    from app import db, current_app # Local import for commit and logging
    from models import Anime, Manga, Rating, ListItem, UserList # ListItem & UserList for members_count
    from sqlalchemy import func # For func.count and func.distinct

    content_model_class = None
    if content_type == 'anime':
        content_model_class = Anime
    elif content_type == 'manga':
        content_model_class = Manga
    else:
        current_app.logger.warning(f"Unsupported content_type for stats update: {content_type}")
        return

    content_item = content_model_class.query.get(content_id)
    if not content_item:
        current_app.logger.warning(f"Content not found for stats update: {content_type} ID {content_id}")
        return

    # 1. Update score_count and average_score from Ratings
    ratings_query = Rating.query.filter_by(content_type=content_type, content_id=content_id)
    
    # Calculate sum of scores and count of ratings in one go if possible, or fetch all
    # For simplicity, fetching all and then processing:
    all_ratings = ratings_query.all()
    valid_scores = [r.score for r in all_ratings if r.score is not None and 1 <= r.score <= 10]

    if valid_scores:
        content_item.score_count = len(valid_scores)
        content_item.average_score = sum(valid_scores) / content_item.score_count
    else:
        content_item.score_count = 0
        content_item.average_score = 0.00 # Or None, depending on model definition

    # 2. Update members_count (number of unique users who have this item in any of their lists)
    # This query counts distinct user_ids associated with ListItems for this content.
    members_count_val = db.session.query(func.count(UserList.user_id.distinct())) \
        .join(ListItem, UserList.list_id == ListItem.list_id) \
        .filter(ListItem.content_type == content_type) \
        .filter(ListItem.content_id == content_id) \
        .scalar() # scalar() returns the first element of the first result or None

    content_item.members_count = members_count_val if members_count_val is not None else 0

    # 3. favorites_count (Placeholder - requires a UserFavorites model and logic)
    # Example if you had a UserFavorite model:
    # from models import UserFavorite
    # favorites_count_val = UserFavorite.query.filter_by(content_type=content_type, content_id=content_id).count()
    # content_item.favorites_count = favorites_count_val if favorites_count_val is not None else 0
    # For now, we don't touch favorites_count if there's no mechanism to update it.

    try:
        db.session.add(content_item) # Add to session in case it's a new object or to track changes
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating content stats for {content_type} ID {content_id}: {e}")
        # Optionally re-raise or handle