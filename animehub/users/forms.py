from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, EmailField, BooleanField, TextAreaField,
    SelectField, IntegerField, HiddenField, SubmitField, URLField
)
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, Optional,
    NumberRange, URL, ValidationError
)
# from models import User, Genre, Anime, Manga # Không cần import models trực tiếp vào forms.py trừ khi có custom validator phức tạp

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    display_name = StringField('Display Name', validators=[Optional(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password', message='Passwords must match.')]) # Thêm message
    submit = SubmitField('Register')

    # Custom validator ví dụ (nếu bạn không muốn kiểm tra trong route)
    # def validate_username(self, username):
    #     from models import User # Import ở đây để tránh circular dependency
    #     user = User.query.filter_by(username=username.data).first()
    #     if user:
    #         raise ValidationError('That username is taken. Please choose a different one.')

    # def validate_email(self, email):
    #     from models import User
    #     user = User.query.filter_by(email=email.data).first()
    #     if user:
    #         raise ValidationError('That email is already registered. Please choose a different one.')


class ProfileForm(FlaskForm):
    display_name = StringField('Display Name', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=1000)])
    profile_picture_url = URLField('Profile Picture URL', validators=[Optional(), URL(message="Invalid URL format.")]) # Thêm message
    current_password = PasswordField('Current Password', validators=[Optional()]) # Để trống nếu không đổi pass
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_new_password = PasswordField('Confirm New Password',
                                         validators=[Optional(),
                                                     EqualTo('new_password', message='New passwords must match.')]) # Thêm message
    submit = SubmitField('Update Profile')

    def validate(self, extra_validators=None):
        # Gọi validator mặc định trước
        initial_validation = super(ProfileForm, self).validate(extra_validators)
        if not initial_validation:
            return False

        # Nếu người dùng nhập new_password, thì current_password và confirm_new_password phải được nhập
        if self.new_password.data:
            if not self.current_password.data:
                self.current_password.errors.append('Current password is required to set a new password.')
                return False
            if not self.confirm_new_password.data:
                self.confirm_new_password.errors.append('Please confirm your new password.')
                return False
        return True


class AnimeSearchForm(FlaskForm):
    search = StringField('Search Anime', validators=[Optional(), Length(max=100)])
    type = SelectField('Type', choices=[ # Choices sẽ được populate trong route
        ('', 'All Types'),
        ('TV', 'TV'), ('Movie', 'Movie'), ('OVA', 'OVA'),
        ('ONA', 'ONA'), ('Special', 'Special'), ('Music', 'Music')
    ], validators=[Optional()])
    status = SelectField('Status', choices=[ # Choices sẽ được populate trong route
        ('', 'All Status'),
        ('finished_airing', 'Finished Airing'), ('currently_airing', 'Currently Airing'),
        ('not_yet_aired', 'Not Yet Aired'), ('cancelled', 'Cancelled'), ('on_hiatus', 'On Hiatus')
    ], validators=[Optional()])
    genre = SelectField('Genre', coerce=int, validators=[Optional()]) # Choices sẽ được populate trong route
    sort = SelectField('Sort By', choices=[
        ('title', 'Title (A-Z)'),
        ('score', 'Score (High to Low)'),
        ('popularity', 'Popularity (Most Members)'),
        ('latest', 'Latest Added/Aired')
    ], default='title', validators=[Optional()]) # Thêm default
    submit = SubmitField('Search')


class MangaSearchForm(FlaskForm):
    search = StringField('Search Manga', validators=[Optional(), Length(max=100)])
    type = SelectField('Type', choices=[ # Choices sẽ được populate trong route
        ('', 'All Types'),
        ('Manga', 'Manga'), ('Light Novel', 'Light Novel'), ('Novel', 'Novel'),
        ('One-shot', 'One-shot'), ('Doujinshi', 'Doujinshi'), ('Manhwa', 'Manhwa'), ('Manhua', 'Manhua')
    ], validators=[Optional()])
    status = SelectField('Status', choices=[ # Choices sẽ được populate trong route
        ('', 'All Status'),
        ('finished_publishing', 'Finished Publishing'), ('currently_publishing', 'Currently Publishing'),
        ('not_yet_published', 'Not Yet Published'), ('on_hiatus', 'On Hiatus'), ('discontinued', 'Discontinued')
    ], validators=[Optional()])
    genre = SelectField('Genre', coerce=int, validators=[Optional()]) # Choices sẽ được populate trong route
    sort = SelectField('Sort By', choices=[
        ('title', 'Title (A-Z)'),
        ('score', 'Score (High to Low)'),
        ('popularity', 'Popularity (Most Members)'),
        ('latest', 'Latest Added/Published')
    ], default='title', validators=[Optional()]) # Thêm default
    submit = SubmitField('Search')


class CommentForm(FlaskForm):
    content_type = HiddenField('Content Type', validators=[DataRequired()])
    content_id = HiddenField('Content ID', validators=[DataRequired()]) # Sẽ là IntegerField nếu không phải hidden
    parent_comment_id = HiddenField('Parent Comment ID', validators=[Optional()]) # Sẽ là IntegerField nếu không phải hidden
    comment_text = TextAreaField('Your Comment', validators=[DataRequired(), Length(min=1, max=2000)])
    is_spoiler = BooleanField('Contains Spoilers')
    submit = SubmitField('Post Comment')


class RatingForm(FlaskForm):
    content_type = HiddenField('Content Type', validators=[DataRequired()])
    content_id = HiddenField('Content ID', validators=[DataRequired()]) # Sẽ là IntegerField nếu không phải hidden
    score = IntegerField('Your Score (1-10, 0 to remove)',
                         validators=[DataRequired(), NumberRange(min=0, max=10, message="Score must be between 0 and 10.")]) # Cho phép 0 để xóa
    submit = SubmitField('Rate') # Nút này có thể không cần nếu dùng JS để submit


class ListForm(FlaskForm): # Form để tạo list mới
    list_name = StringField('List Name', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_public = BooleanField('Public List', default=True)
    submit = SubmitField('Create List')


class ListItemForm(FlaskForm): # Form để thêm/sửa item trong list
    # Các hidden field này sẽ được set trong template hoặc route trước khi render
    content_type = HiddenField('Content Type', validators=[DataRequired()])
    content_id = HiddenField('Content ID', validators=[DataRequired()]) # Sẽ là IntegerField nếu không phải hidden

    list_id = SelectField('Add to List', coerce=int, validators=[DataRequired(message="Please select a list.")]) # Choices sẽ được populate trong route
    status = SelectField('Status', choices=[ # Cần cập nhật choices cho phù hợp với content_type (anime/manga)
        # Anime statuses
        ('watching', 'Watching'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('plan_to_watch', 'Plan to Watch'),
        # Manga statuses (có thể tách riêng hoặc dùng JS để thay đổi choices)
        ('reading', 'Reading'),
        ('completed_manga', 'Completed (Manga)'),
        ('on_hold_manga', 'On Hold (Manga)'),
        ('dropped_manga', 'Dropped (Manga)'),
        ('plan_to_read', 'Plan to Read')
    ], validators=[DataRequired(message="Please select a status.")])
    progress = IntegerField('Progress (Episodes/Chapters)', validators=[Optional(), NumberRange(min=0)])
    score = IntegerField('Your Score (1-10)', validators=[Optional(), NumberRange(min=1, max=10, message="Score must be between 1 and 10 if provided.")])
    # Không cần submit button ở đây nếu form này được submit qua JS hoặc là một phần của form lớn hơn
    # submit = SubmitField('Save to List')

    def __init__(self, *args, **kwargs):
        super(ListItemForm, self).__init__(*args, **kwargs)
        # Dynamically set choices for status based on content_type if provided
        # This is a bit more advanced and might be better handled in the route or with JavaScript
        # For now, we keep all statuses.
        # content_type_value = kwargs.get('content_type_value', None) # Example: pass 'anime' or 'manga'
        # if content_type_value == 'anime':
        #     self.status.choices = [
        #         ('watching', 'Watching'), ('completed', 'Completed'), ('on_hold', 'On Hold'),
        #         ('dropped', 'Dropped'), ('plan_to_watch', 'Plan to Watch')
        #     ]
        # elif content_type_value == 'manga':
        #     self.status.choices = [
        #         ('reading', 'Reading'), ('completed_manga', 'Completed (Manga)'),
        #         ('on_hold_manga', 'On Hold (Manga)'), ('dropped_manga', 'Dropped (Manga)'),
        #         ('plan_to_read', 'Plan to Read')
        #     ]


class FanartForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=255)])
    image_url = URLField('Image URL', validators=[DataRequired(), URL(message="Please enter a valid image URL.")])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    is_published = BooleanField('Publish Now', default=True)
    submit = SubmitField('Submit Fanart')


class FanfictionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=3, max=255)])
    summary = TextAreaField('Summary', validators=[Optional(), Length(max=1000)]) # Tăng giới hạn summary
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=50)]) # Giảm min length content một chút
    language = SelectField('Language', choices=[
        ('vi', 'Vietnamese'), ('en', 'English'), ('ja', 'Japanese'),
        ('ko', 'Korean'), ('zh', 'Chinese'), ('other', 'Other') # Thêm 'other'
    ], default='en') # Đổi default sang English
    is_published = BooleanField('Publish Now', default=True)
    submit = SubmitField('Submit Fanfiction')