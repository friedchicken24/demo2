from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db # db được import từ app.py nơi nó được khởi tạo
from sqlalchemy.orm import validates # Để thêm custom validation nếu cần

# User-related models
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    # SỬA Ở ĐÂY: Bỏ sparse=True, thêm nullable=True
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_token_expires_at = db.Column(db.DateTime)
    # SỬA Ở ĐÂY: Bỏ sparse=True, thêm nullable=True
    password_reset_token = db.Column(db.String(100), unique=True, nullable=True)
    password_reset_token_expires_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'),
                            lazy='select')

    fanarts = db.relationship('Fanart', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    fanfictions = db.relationship('Fanfiction', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='rater', lazy='dynamic', cascade='all, delete-orphan')
    user_lists = db.relationship('UserList', backref='owner', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, username, email, password, display_name=None, **kwargs):
        super(User, self).__init__(**kwargs)
        self.username = username.lower()
        self.email = email.lower()
        self.set_password(password)
        self.display_name = display_name or self.username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username cannot be empty.")
        if len(username) < 3 or len(username) > 50:
            raise ValueError("Username must be between 3 and 50 characters.")
        return username.lower()

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError("Email cannot be empty.")
        if '@' not in email:
            raise ValueError("Invalid email format.")
        return email.lower()

    def __repr__(self):
        return f'<User {self.username} (ID: {self.user_id})>'


class Role(db.Model):
    __tablename__ = 'roles'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Role {self.role_name}>'

user_roles = db.Table('user_roles', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)


class Genre(db.Model):
    __tablename__ = 'genres'
    genre_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Genre {self.name}>'


class Studio(db.Model):
    __tablename__ = 'studios'
    studio_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    established_date = db.Column(db.Date)
    website = db.Column(db.String(255))

    def __repr__(self):
        return f'<Studio {self.name}>'


class Creator(db.Model):
    __tablename__ = 'creators'
    creator_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    creator_role_enum_values = ('author', 'artist', 'author_artist', 'voice_actor', 'director', 'producer', 'other')
    role = db.Column(db.Enum(*creator_role_enum_values, name='creator_role_enum'), nullable=False)
    bio = db.Column(db.Text)

    def __repr__(self):
        return f'<Creator {self.name}, Role: {self.role}>'


anime_genres = db.Table('anime_genres', db.Model.metadata,
    db.Column('anime_id', db.Integer, db.ForeignKey('anime.anime_id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.genre_id', ondelete='CASCADE'), primary_key=True)
)

anime_studios = db.Table('anime_studios', db.Model.metadata,
    db.Column('anime_id', db.Integer, db.ForeignKey('anime.anime_id', ondelete='CASCADE'), primary_key=True),
    db.Column('studio_id', db.Integer, db.ForeignKey('studios.studio_id', ondelete='CASCADE'), primary_key=True)
)

manga_genres = db.Table('manga_genres', db.Model.metadata,
    db.Column('manga_id', db.Integer, db.ForeignKey('manga.manga_id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.genre_id', ondelete='CASCADE'), primary_key=True)
)

manga_creators = db.Table('manga_creators', db.Model.metadata,
    db.Column('manga_id', db.Integer, db.ForeignKey('manga.manga_id', ondelete='CASCADE'), primary_key=True),
    db.Column('creator_id', db.Integer, db.ForeignKey('creators.creator_id', ondelete='CASCADE'), primary_key=True)
)


class Anime(db.Model):
    __tablename__ = 'anime'
    anime_id = db.Column(db.Integer, primary_key=True)
    title_romaji = db.Column(db.String(255), nullable=False, index=True)
    title_english = db.Column(db.String(255), index=True)
    title_japanese = db.Column(db.String(255), index=True)
    synopsis = db.Column(db.Text)
    anime_type_enum_values = ('TV', 'Movie', 'OVA', 'ONA', 'Special', 'Music', 'Unknown')
    type = db.Column(db.Enum(*anime_type_enum_values, name='anime_type_enum'), default='TV')
    anime_source_enum_values = ('Manga', 'Light Novel', 'Visual Novel', 'Game', 'Original', 'Web Novel', 'Novel', 'Other', 'Unknown')
    source = db.Column(db.Enum(*anime_source_enum_values, name='anime_source_enum'))
    episodes = db.Column(db.Integer)
    anime_status_enum_values = ('finished_airing', 'currently_airing', 'not_yet_aired', 'cancelled', 'on_hiatus', 'unknown')
    status = db.Column(db.Enum(*anime_status_enum_values, name='anime_status_enum'), default='not_yet_aired')
    aired_from = db.Column(db.Date)
    aired_to = db.Column(db.Date)
    duration_per_episode = db.Column(db.String(50))
    age_rating = db.Column(db.String(50))
    cover_image_url = db.Column(db.String(512))
    banner_image_url = db.Column(db.String(512))
    youtube_trailer_id = db.Column(db.String(50))
    average_score = db.Column(db.Numeric(4, 2), default=0.00, index=True)
    score_count = db.Column(db.Integer, default=0)
    popularity_rank = db.Column(db.Integer, index=True)
    members_count = db.Column(db.Integer, default=0, index=True)
    favorites_count = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    genres = db.relationship('Genre', secondary=anime_genres,
                             backref=db.backref('animes', lazy='dynamic'), lazy='select')
    studios = db.relationship('Studio', secondary=anime_studios,
                              backref=db.backref('animes', lazy='dynamic'), lazy='select')
    songs = db.relationship('AnimeSong', backref='anime', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Anime {self.title_romaji}>'


class Manga(db.Model):
    __tablename__ = 'manga'
    manga_id = db.Column(db.Integer, primary_key=True)
    title_romaji = db.Column(db.String(255), nullable=False, index=True)
    title_english = db.Column(db.String(255), index=True)
    title_japanese = db.Column(db.String(255), index=True)
    synopsis = db.Column(db.Text)
    manga_type_enum_values = ('Manga', 'Light Novel', 'Novel', 'One-shot', 'Doujinshi', 'Manhwa', 'Manhua', 'Web Novel', 'Unknown')
    type = db.Column(db.Enum(*manga_type_enum_values, name='manga_type_enum'), default='Manga')
    chapters = db.Column(db.Integer)
    volumes = db.Column(db.Integer)
    manga_status_enum_values = ('finished_publishing', 'currently_publishing', 'not_yet_published', 'on_hiatus', 'discontinued', 'cancelled', 'unknown')
    status = db.Column(db.Enum(*manga_status_enum_values, name='manga_status_enum'), default='not_yet_published')
    published_from = db.Column(db.Date)
    published_to = db.Column(db.Date)
    cover_image_url = db.Column(db.String(512))
    banner_image_url = db.Column(db.String(512))
    average_score = db.Column(db.Numeric(4, 2), default=0.00, index=True)
    score_count = db.Column(db.Integer, default=0)
    popularity_rank = db.Column(db.Integer, index=True)
    members_count = db.Column(db.Integer, default=0, index=True)
    favorites_count = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    genres = db.relationship('Genre', secondary=manga_genres,
                             backref=db.backref('mangas', lazy='dynamic'), lazy='select')
    creators = db.relationship('Creator', secondary=manga_creators,
                               backref=db.backref('mangas', lazy='dynamic'), lazy='select')

    def __repr__(self):
        return f'<Manga {self.title_romaji}>'


class AnimeSong(db.Model):
    __tablename__ = 'anime_songs'
    song_id = db.Column(db.Integer, primary_key=True)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.anime_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255))
    song_type_enum_values = ('OP', 'ED', 'Insert Song', 'Character Song', 'OST', 'Theme Song')
    type = db.Column(db.Enum(*song_type_enum_values, name='song_type_enum'), nullable=False)
    episode_usage = db.Column(db.String(100))
    youtube_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AnimeSong {self.title} - Type: {self.type}>'


class Fanart(db.Model):
    __tablename__ = 'fanart'
    fanart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(512), nullable=False)
    description = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Fanart {self.title} by User ID: {self.user_id}>'


class Fanfiction(db.Model):
    __tablename__ = 'fanfiction'
    fanfiction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en', nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    word_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Fanfiction {self.title} by User ID: {self.user_id}>'


class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments.comment_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    comment_content_type_enum_values = ('anime', 'manga', 'fanart', 'fanfiction', 'user_profile', 'song', 'list', 'review')
    content_type = db.Column(db.Enum(*comment_content_type_enum_values, name='comment_content_type_enum'), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    is_spoiler = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    replies = db.relationship('Comment',
                              backref=db.backref('parent', remote_side=[comment_id]),
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    __table_args__ = (
        db.Index('idx_comment_content', 'content_type', 'content_id', 'parent_comment_id', 'created_at'),
    )

    def __repr__(self):
        return f'<Comment ID: {self.comment_id} by User ID: {self.user_id} on {self.content_type}:{self.content_id}>'


class Rating(db.Model):
    __tablename__ = 'ratings'
    rating_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    rating_content_type_enum_values = ('anime', 'manga')
    content_type = db.Column(db.Enum(*rating_content_type_enum_values, name='rating_content_type_enum'), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_type', 'content_id', name='uq_user_content_rating'),
        db.CheckConstraint('score >= 1 AND score <= 10', name='cc_rating_score_range'),
        db.Index('idx_rating_content_user', 'content_type', 'content_id', 'user_id'),
    )

    @validates('score')
    def validate_score(self, key, score):
        if not (1 <= score <= 10):
            raise ValueError("Score must be between 1 and 10.")
        return score

    def __repr__(self):
        return f'<Rating {self.score}/10 by User ID: {self.user_id} on {self.content_type}:{self.content_id}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    is_spoiler_tag = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


class ContentTag(db.Model):
    __tablename__ = 'content_tags'
    content_tag_id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.tag_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    tag_content_type_enum_values = ('anime', 'manga', 'fanart', 'fanfiction', 'character', 'staff')
    content_type = db.Column(db.Enum(*tag_content_type_enum_values, name='tag_content_type_enum'), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    tagged_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    tag = db.relationship('Tag', backref=db.backref('tagged_items', lazy='dynamic'))
    tagged_by_user = db.relationship('User', backref=db.backref('tags_created', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('tag_id', 'content_type', 'content_id', name='uq_tag_content_item'),
        db.Index('idx_content_tag_lookup', 'content_type', 'content_id', 'tag_id'),
    )

    def __repr__(self):
        return f'<ContentTag: Tag ID {self.tag_id} on {self.content_type}:{self.content_id}>'


class UserList(db.Model):
    __tablename__ = 'user_lists'
    list_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    list_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    is_main_list = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = db.relationship('ListItem', backref='user_list_assoc', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'list_name', name='uq_user_list_name'),
        db.Index('idx_user_list_user', 'user_id', 'is_main_list', 'list_name'),
    )

    def __repr__(self):
        return f'<UserList {self.list_name} (ID: {self.list_id}) by User ID: {self.user_id}>'


class ListItem(db.Model):
    __tablename__ = 'list_items'
    list_item_id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('user_lists.list_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    list_content_type_enum_values = ('anime', 'manga')
    content_type = db.Column(db.Enum(*list_content_type_enum_values, name='list_content_type_enum'), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    list_item_status_enum_values = (
        'watching', 'completed', 'on_hold', 'dropped', 'plan_to_watch',
        'reading', 'completed_manga', 'on_hold_manga', 'dropped_manga', 'plan_to_read'
    )
    status_in_list = db.Column(db.Enum(*list_item_status_enum_values, name='list_item_status_enum'), nullable=True)
    progress = db.Column(db.Integer, default=0)
    user_score = db.Column(db.Integer, nullable=True)
    started_date = db.Column(db.Date, nullable=True)
    finished_date = db.Column(db.Date, nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('list_id', 'content_type', 'content_id', name='uq_list_content_item'),
        db.CheckConstraint('user_score IS NULL OR (user_score >= 1 AND user_score <= 10)', name='cc_list_item_score_range'),
        db.Index('idx_list_item_content', 'content_type', 'content_id'),
    )

    @validates('user_score')
    def validate_user_score(self, key, score):
        if score is not None and not (1 <= score <= 10):
            raise ValueError("User score must be between 1 and 10 if provided.")
        return score

    def __repr__(self):
        return f'<ListItem ID: {self.list_item_id} - {self.content_type}:{self.content_id} in List ID: {self.list_id}>'