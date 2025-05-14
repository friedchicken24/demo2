from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DateField, IntegerField, FloatField, # FloatField không thấy dùng
    SelectField, BooleanField, PasswordField, SelectMultipleField,
    URLField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, Email, Optional, URL, NumberRange, EqualTo
)
# Choices cho các SelectField thường được populate trong route, không cần định nghĩa cứng ở đây
# trừ khi chúng thực sự cố định.

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(message="Invalid email address.")])
    # Password là Optional khi edit, DataRequired khi create (logic này xử lý trong route)
    password = PasswordField('Password (leave blank to keep current)', validators=[Optional(), Length(min=8, message="Password must be at least 8 characters long.")])
    display_name = StringField('Display Name', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=2000)]) # Tăng giới hạn
    profile_picture_url = URLField('Profile Picture URL', validators=[Optional(), URL(message="Invalid URL.")])
    is_active = BooleanField('Active Account', default=True)
    is_verified = BooleanField('Verified Account', default=False)
    roles = SelectMultipleField('Roles', coerce=int, validators=[Optional()]) # Roles là optional, có thể không có role nào
    submit = SubmitField('Save User')

class RoleForm(FlaskForm):
    role_name = StringField('Role Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Role')

class GenreForm(FlaskForm):
    name = StringField('Genre Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Genre')

class StudioForm(FlaskForm):
    name = StringField('Studio Name', validators=[DataRequired(), Length(min=1, max=100)])
    established_date = DateField('Established Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    website = URLField('Website URL', validators=[Optional(), URL(message="Invalid URL.")])
    submit = SubmitField('Save Studio')

class CreatorForm(FlaskForm):
    name = StringField('Creator Name', validators=[DataRequired(), Length(min=1, max=150)])
    # Choices cho role sẽ được lấy từ model enum values trong route
    role = SelectField('Role', validators=[DataRequired(message="Please select a role.")])
    bio = TextAreaField('Biography', validators=[Optional(), Length(max=5000)]) # Tăng giới hạn
    submit = SubmitField('Save Creator')

class AnimeForm(FlaskForm):
    title_romaji = StringField('Title (Romaji)', validators=[DataRequired(), Length(max=255)])
    title_english = StringField('Title (English)', validators=[Optional(), Length(max=255)])
    title_japanese = StringField('Title (Japanese)', validators=[Optional(), Length(max=255)])
    synopsis = TextAreaField('Synopsis', validators=[Optional()])
    # Choices cho type, source, status sẽ được lấy từ model enum values trong route
    type = SelectField('Type', validators=[DataRequired(message="Please select a type.")])
    source = SelectField('Source', validators=[Optional()])
    episodes = IntegerField('Episodes', validators=[Optional(), NumberRange(min=0, message="Episodes cannot be negative.")]) # Cho phép 0 tập (ví dụ: movie)
    status = SelectField('Status', validators=[DataRequired(message="Please select a status.")])
    aired_from = DateField('Air Date (From) (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    aired_to = DateField('Air Date (To) (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    duration_per_episode = StringField('Duration per Episode (e.g., 24 min)', validators=[Optional(), Length(max=50)])
    age_rating = StringField('Age Rating (e.g., PG-13)', validators=[Optional(), Length(max=50)])
    cover_image_url = URLField('Cover Image URL', validators=[Optional(), URL(message="Invalid URL.")])
    banner_image_url = URLField('Banner Image URL', validators=[Optional(), URL(message="Invalid URL.")])
    youtube_trailer_id = StringField('YouTube Trailer ID', validators=[Optional(), Length(max=50)])
    # average_score, score_count, popularity_rank, members_count, favorites_count thường được tính tự động, không nhập tay
    genres = SelectMultipleField('Genres', coerce=int, validators=[Optional()]) # Có thể không có genre nào
    studios = SelectMultipleField('Studios', coerce=int, validators=[Optional()]) # Có thể không có studio nào
    submit = SubmitField('Save Anime')

class MangaForm(FlaskForm):
    title_romaji = StringField('Title (Romaji)', validators=[DataRequired(), Length(max=255)])
    title_english = StringField('Title (English)', validators=[Optional(), Length(max=255)])
    title_japanese = StringField('Title (Japanese)', validators=[Optional(), Length(max=255)])
    synopsis = TextAreaField('Synopsis', validators=[Optional()])
    # Choices cho type, status sẽ được lấy từ model enum values trong route
    type = SelectField('Type', validators=[DataRequired(message="Please select a type.")])
    chapters = IntegerField('Chapters', validators=[Optional(), NumberRange(min=0, message="Chapters cannot be negative.")])
    volumes = IntegerField('Volumes', validators=[Optional(), NumberRange(min=0, message="Volumes cannot be negative.")])
    status = SelectField('Status', validators=[DataRequired(message="Please select a status.")])
    published_from = DateField('Published (From) (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    published_to = DateField('Published (To) (YYYY-MM-DD)', format='%Y-%m-%d', validators=[Optional()])
    cover_image_url = URLField('Cover Image URL', validators=[Optional(), URL(message="Invalid URL.")])
    banner_image_url = URLField('Banner Image URL', validators=[Optional(), URL(message="Invalid URL.")])
    genres = SelectMultipleField('Genres', coerce=int, validators=[Optional()])
    creators = SelectMultipleField('Creators', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Manga')

class AnimeSongForm(FlaskForm):
    # anime_id sẽ là SelectField, choices được populate trong route
    anime_id = SelectField('Anime', coerce=int, validators=[DataRequired(message="Please select an anime.")])
    title = StringField('Song Title', validators=[DataRequired(), Length(max=255)])
    artist = StringField('Artist', validators=[Optional(), Length(max=255)])
    # Choices cho type sẽ được lấy từ model enum values trong route
    type = SelectField('Type (OP, ED, Insert, etc.)', validators=[DataRequired(message="Please select a song type.")])
    episode_usage = StringField('Episode Usage (e.g., eps 1-12)', validators=[Optional(), Length(max=100)])
    youtube_url = URLField('YouTube URL', validators=[Optional(), URL(message="Invalid URL.")])
    submit = SubmitField('Save Song')

class TagForm(FlaskForm):
    name = StringField('Tag Name', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_spoiler_tag = BooleanField('This is a Spoiler Tag', default=False)
    submit = SubmitField('Save Tag')

class AdminCommentForm(FlaskForm): # Đổi tên để phân biệt với CommentForm của user
    # user_id, content_type, content_id, parent_comment_id thường không được admin sửa trực tiếp qua form này.
    # Admin có thể sửa text hoặc is_spoiler.
    comment_text = TextAreaField('Comment Text', validators=[DataRequired(), Length(min=1, max=5000)])
    is_spoiler = BooleanField('Contains Spoilers', default=False)
    submit = SubmitField('Save Comment')

class AdminSearchForm(FlaskForm): # Form này có vẻ chung chung, có thể không cần thiết nếu mỗi trang list có search riêng
    search_query = StringField('Search Term', validators=[Optional(), Length(max=100)]) # Đổi tên field
    # search_in = SelectField('Search In', choices=[ # Ví dụ
    #     ('users', 'Users'),
    #     ('anime', 'Anime'),
    #     ('manga', 'Manga'),
    #     # ...
    # ], validators=[Optional()])
    submit = SubmitField('Search')