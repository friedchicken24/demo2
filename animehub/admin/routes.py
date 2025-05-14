from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify # jsonify có thể không cần nếu không có API endpoint
from flask_login import login_required, current_user # login_required không thực sự cần nếu @admin_bp.before_request đã có
from sqlalchemy import func, desc, and_, or_
# from werkzeug.security import generate_password_hash # Không cần trực tiếp, User model xử lý

from app import db
from models import (
    User, Role, Genre, Studio, Creator, Anime, Manga,
    AnimeSong, Fanart, Fanfiction, Comment, Rating, Tag, ContentTag,
    UserList, ListItem # UserList, ListItem có thể không quản lý trực tiếp ở đây
)
from admin.forms import ( # Đảm bảo import đúng tên form
    UserForm, RoleForm, GenreForm, StudioForm, CreatorForm,
    AnimeForm, MangaForm, AnimeSongForm, TagForm,
    AdminCommentForm, AdminSearchForm # Sử dụng AdminCommentForm
)
from utils import role_required, any_role_required # any_role_required đã dùng

admin_bp = Blueprint('admin', __name__, template_folder='templates') # Chỉ định template_folder nếu khác 'templates/admin'

# Helper function để populate enum choices cho SelectFields
def _populate_enum_choices(field, enum_values_tuple):
    field.choices = [(val, val.replace('_', ' ').title()) for val in enum_values_tuple]

# Require admin role for all admin routes
@admin_bp.before_request
@any_role_required(['admin']) # Đảm bảo Role 'admin' tồn tại trong DB
def restrict_to_admins():
    pass

# Dashboard
@admin_bp.route('/')
def dashboard():
    user_count = User.query.count()
    anime_count = Anime.query.count()
    manga_count = Manga.query.count()
    comment_count = Comment.query.count() # Tổng số comment
    # Thêm các thống kê khác nếu muốn

    latest_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    latest_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    # Cân nhắc join với User để hiển thị username của người comment
    # latest_comments = db.session.query(Comment, User.username).join(User, Comment.user_id == User.user_id).order_by(Comment.created_at.desc()).limit(5).all()


    # Popular content (ví dụ)
    popular_anime = Anime.query.order_by(Anime.members_count.desc().nullslast(), Anime.average_score.desc().nullslast()).limit(5).all()
    popular_manga = Manga.query.order_by(Manga.members_count.desc().nullslast(), Manga.average_score.desc().nullslast()).limit(5).all()

    return render_template('admin/dashboard.html', # Đảm bảo đường dẫn template đúng
                          user_count=user_count,
                          anime_count=anime_count,
                          manga_count=manga_count,
                          comment_count=comment_count,
                          latest_users=latest_users,
                          latest_comments=latest_comments,
                          popular_anime=popular_anime,
                          popular_manga=popular_manga)

# User management
@admin_bp.route('/users')
def users_list(): # Đổi tên hàm để rõ ràng hơn
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term) # Cho search form

    query = User.query.options(db.selectinload(User.roles)) # Tải sẵn roles để tránh N+1

    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(
            or_(
                User.username.ilike(like_pattern),
                User.email.ilike(like_pattern),
                User.display_name.ilike(like_pattern)
            )
        )

    users_pagination = query.order_by(User.username).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/users_list.html', users=users_pagination, search_form=search_form, search_term=search_term)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
def create_user():
    form = UserForm()
    form.roles.choices = [(r.role_id, r.role_name) for r in Role.query.order_by(Role.role_name).all()]

    if form.validate_on_submit():
        existing_user_username = User.query.filter(func.lower(User.username) == func.lower(form.username.data)).first()
        if existing_user_username:
            flash('Username already exists.', 'danger')
            return render_template('admin/user_form.html', form=form, title="Create User")

        existing_user_email = User.query.filter(func.lower(User.email) == func.lower(form.email.data)).first()
        if existing_user_email:
            flash('Email already exists.', 'danger')
            return render_template('admin/user_form.html', form=form, title="Create User")

        if not form.password.data: # Password là bắt buộc khi tạo mới
            flash('Password is required for new users.', 'danger')
            return render_template('admin/user_form.html', form=form, title="Create User")

        new_user = User(
            username=form.username.data, # Model User sẽ tự .lower()
            email=form.email.data,       # Model User sẽ tự .lower()
            password=form.password.data, # Model User sẽ hash
            display_name=form.display_name.data
        )
        new_user.is_active = form.is_active.data
        new_user.is_verified = form.is_verified.data # Admin có thể verify ngay
        new_user.bio = form.bio.data
        new_user.profile_picture_url = form.profile_picture_url.data

        selected_roles = Role.query.filter(Role.role_id.in_(form.roles.data or [])).all()
        new_user.roles = selected_roles

        db.session.add(new_user)
        db.session.commit()
        flash(f'User "{new_user.username}" created successfully.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/user_form.html', form=form, title="Create User")

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.options(db.selectinload(User.roles)).get_or_404(user_id)
    form = UserForm(obj=user) # Populate form with user data
    form.roles.choices = [(r.role_id, r.role_name) for r in Role.query.order_by(Role.role_name).all()]

    if request.method == 'GET':
        form.roles.data = [role.role_id for role in user.roles] # Pre-select current roles

    if form.validate_on_submit():
        # Check for username/email conflicts (excluding current user)
        username_lower = form.username.data.lower()
        email_lower = form.email.data.lower()

        conflicting_user_username = User.query.filter(User.user_id != user_id, func.lower(User.username) == username_lower).first()
        if conflicting_user_username:
            flash(f'Username "{form.username.data}" is already taken by another user.', 'danger')
            return render_template('admin/user_form.html', form=form, title=f"Edit User: {user.username}", user=user)

        conflicting_user_email = User.query.filter(User.user_id != user_id, func.lower(User.email) == email_lower).first()
        if conflicting_user_email:
            flash(f'Email "{form.email.data}" is already used by another user.', 'danger')
            return render_template('admin/user_form.html', form=form, title=f"Edit User: {user.username}", user=user)

        user.username = form.username.data # Model sẽ .lower()
        user.email = form.email.data       # Model sẽ .lower()
        user.display_name = form.display_name.data
        user.is_active = form.is_active.data
        user.is_verified = form.is_verified.data
        user.bio = form.bio.data
        user.profile_picture_url = form.profile_picture_url.data

        if form.password.data: # Only update password if a new one is provided
            user.set_password(form.password.data)

        selected_roles = Role.query.filter(Role.role_id.in_(form.roles.data or [])).all()
        user.roles = selected_roles # SQLAlchemy handles updates to many-to-many

        db.session.commit()
        flash(f'User "{user.username}" updated successfully.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/user_form.html', form=form, title=f"Edit User: {user.username}", user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.user_id == current_user.user_id: # Không cho admin tự xóa mình
        flash('You cannot delete your own account from the admin panel.', 'danger')
        return redirect(url_for('admin.users_list'))

    # Kiểm tra xem user có phải là admin cuối cùng không (nếu có logic này)
    # is_admin = any(role.role_name == 'admin' for role in user.roles)
    # if is_admin:
    #     admin_count = db.session.query(func.count(User.user_id)).join(User.roles).filter(Role.role_name == 'admin').scalar()
    #     if admin_count <= 1:
    #         flash('Cannot delete the last administrator.', 'danger')
    #         return redirect(url_for('admin.users_list'))

    username_deleted = user.username
    db.session.delete(user) # Cascade options trong model User sẽ xử lý các bản ghi liên quan
    db.session.commit()
    flash(f'User "{username_deleted}" and all associated data deleted successfully.', 'success')
    return redirect(url_for('admin.users_list'))

# Role management
@admin_bp.route('/roles')
def roles_list():
    roles = Role.query.order_by(Role.role_name).all()
    return render_template('admin/roles_list.html', roles=roles)

@admin_bp.route('/roles/create', methods=['GET', 'POST'])
def create_role():
    form = RoleForm()
    if form.validate_on_submit():
        existing_role = Role.query.filter(func.lower(Role.role_name) == func.lower(form.role_name.data)).first()
        if existing_role:
            flash(f'Role name "{form.role_name.data}" already exists.', 'danger')
        else:
            new_role = Role(role_name=form.role_name.data, description=form.description.data)
            db.session.add(new_role)
            db.session.commit()
            flash(f'Role "{new_role.role_name}" created successfully.', 'success')
            return redirect(url_for('admin.roles_list'))
    return render_template('admin/role_form.html', form=form, title="Create Role")

@admin_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    form = RoleForm(obj=role)
    if form.validate_on_submit():
        new_role_name_lower = form.role_name.data.lower()
        conflicting_role = Role.query.filter(Role.role_id != role_id, func.lower(Role.role_name) == new_role_name_lower).first()
        if conflicting_role:
            flash(f'Role name "{form.role_name.data}" is already used by another role.', 'danger')
        else:
            role.role_name = form.role_name.data
            role.description = form.description.data
            db.session.commit()
            flash(f'Role "{role.role_name}" updated successfully.', 'success')
            return redirect(url_for('admin.roles_list'))
    return render_template('admin/role_form.html', form=form, title=f"Edit Role: {role.role_name}", role=role)

@admin_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    if role.role_name.lower() == 'admin': # Không cho xóa role 'admin'
        flash('The "admin" role cannot be deleted.', 'danger')
        return redirect(url_for('admin.roles_list'))

    if role.users.count() > 0: # Kiểm tra xem có user nào đang giữ role này không
        flash(f'Cannot delete role "{role.role_name}" as it is currently assigned to {role.users.count()} user(s).', 'danger')
        return redirect(url_for('admin.roles_list'))

    role_name_deleted = role.role_name
    db.session.delete(role)
    db.session.commit()
    flash(f'Role "{role_name_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.roles_list'))

# Anime management
@admin_bp.route('/anime')
def anime_list_admin(): # Đổi tên để tránh xung đột với user.anime_list
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)

    query = Anime.query.options(db.selectinload(Anime.genres), db.selectinload(Anime.studios))

    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(
            or_(
                Anime.title_romaji.ilike(like_pattern),
                Anime.title_english.ilike(like_pattern),
                Anime.title_japanese.ilike(like_pattern)
            )
        )
    anime_pagination = query.order_by(Anime.title_romaji).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/anime_list.html', anime_collection=anime_pagination, search_form=search_form, search_term=search_term) # Đổi tên biến

def _populate_anime_form_choices(form):
    _populate_enum_choices(form.type, Anime.anime_type_enum_values)
    _populate_enum_choices(form.source, Anime.anime_source_enum_values)
    _populate_enum_choices(form.status, Anime.anime_status_enum_values)
    form.genres.choices = [(g.genre_id, g.name) for g in Genre.query.order_by(Genre.name).all()]
    form.studios.choices = [(s.studio_id, s.name) for s in Studio.query.order_by(Studio.name).all()]

@admin_bp.route('/anime/create', methods=['GET', 'POST'])
def create_anime():
    form = AnimeForm()
    _populate_anime_form_choices(form)

    if form.validate_on_submit():
        new_anime = Anime()
        form.populate_obj(new_anime) # Điền dữ liệu từ form vào object (trừ many-to-many)

        selected_genres = Genre.query.filter(Genre.genre_id.in_(form.genres.data or [])).all()
        new_anime.genres = selected_genres
        selected_studios = Studio.query.filter(Studio.studio_id.in_(form.studios.data or [])).all()
        new_anime.studios = selected_studios

        db.session.add(new_anime)
        db.session.commit()
        flash(f'Anime "{new_anime.title_romaji}" created successfully.', 'success')
        return redirect(url_for('admin.anime_list_admin'))
    return render_template('admin/anime_form.html', form=form, title="Create Anime")

@admin_bp.route('/anime/<int:anime_id>/edit', methods=['GET', 'POST'])
def edit_anime(anime_id):
    anime_item = Anime.query.options(db.selectinload(Anime.genres), db.selectinload(Anime.studios)).get_or_404(anime_id)
    form = AnimeForm(obj=anime_item)
    _populate_anime_form_choices(form)

    if request.method == 'GET':
        form.genres.data = [g.genre_id for g in anime_item.genres]
        form.studios.data = [s.studio_id for s in anime_item.studios]

    if form.validate_on_submit():
        form.populate_obj(anime_item) # Cập nhật các trường thường

        selected_genres = Genre.query.filter(Genre.genre_id.in_(form.genres.data or [])).all()
        anime_item.genres = selected_genres
        selected_studios = Studio.query.filter(Studio.studio_id.in_(form.studios.data or [])).all()
        anime_item.studios = selected_studios
        
        db.session.commit()
        # Sau khi commit, có thể gọi update_content_stats nếu các trường như score bị ảnh hưởng bởi admin edit
        # from utils import update_content_stats
        # update_content_stats('anime', anime_item.anime_id)
        flash(f'Anime "{anime_item.title_romaji}" updated successfully.', 'success')
        return redirect(url_for('admin.anime_list_admin'))
    return render_template('admin/anime_form.html', form=form, title=f"Edit Anime: {anime_item.title_romaji}", anime=anime_item)

@admin_bp.route('/anime/<int:anime_id>/delete', methods=['POST'])
def delete_anime(anime_id):
    anime_item = Anime.query.get_or_404(anime_id)
    title_deleted = anime_item.title_romaji
    # Cascade delete cho AnimeSong, anime_genres, anime_studios đã được cấu hình trong model
    # ListItem và Rating cũng sẽ bị ảnh hưởng nếu có ondelete='CASCADE' từ content_id (cần kiểm tra)
    db.session.delete(anime_item)
    db.session.commit()
    flash(f'Anime "{title_deleted}" and associated data deleted successfully.', 'success')
    return redirect(url_for('admin.anime_list_admin'))


# Manga management (Tương tự Anime)
@admin_bp.route('/manga')
def manga_list_admin():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)
    query = Manga.query.options(db.selectinload(Manga.genres), db.selectinload(Manga.creators))
    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(or_(Manga.title_romaji.ilike(like_pattern), Manga.title_english.ilike(like_pattern), Manga.title_japanese.ilike(like_pattern)))
    manga_pagination = query.order_by(Manga.title_romaji).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/manga_list.html', manga_collection=manga_pagination, search_form=search_form, search_term=search_term)

def _populate_manga_form_choices(form):
    _populate_enum_choices(form.type, Manga.manga_type_enum_values)
    _populate_enum_choices(form.status, Manga.manga_status_enum_values)
    form.genres.choices = [(g.genre_id, g.name) for g in Genre.query.order_by(Genre.name).all()]
    form.creators.choices = [(c.creator_id, f"{c.name} ({c.role.replace('_', ' ').title()})") for c in Creator.query.order_by(Creator.name).all()]

@admin_bp.route('/manga/create', methods=['GET', 'POST'])
def create_manga():
    form = MangaForm()
    _populate_manga_form_choices(form)
    if form.validate_on_submit():
        new_manga = Manga()
        form.populate_obj(new_manga)
        selected_genres = Genre.query.filter(Genre.genre_id.in_(form.genres.data or [])).all()
        new_manga.genres = selected_genres
        selected_creators = Creator.query.filter(Creator.creator_id.in_(form.creators.data or [])).all()
        new_manga.creators = selected_creators
        db.session.add(new_manga)
        db.session.commit()
        flash(f'Manga "{new_manga.title_romaji}" created successfully.', 'success')
        return redirect(url_for('admin.manga_list_admin'))
    return render_template('admin/manga_form.html', form=form, title="Create Manga")

@admin_bp.route('/manga/<int:manga_id>/edit', methods=['GET', 'POST'])
def edit_manga(manga_id):
    manga_item = Manga.query.options(db.selectinload(Manga.genres), db.selectinload(Manga.creators)).get_or_404(manga_id)
    form = MangaForm(obj=manga_item)
    _populate_manga_form_choices(form)
    if request.method == 'GET':
        form.genres.data = [g.genre_id for g in manga_item.genres]
        form.creators.data = [c.creator_id for c in manga_item.creators]
    if form.validate_on_submit():
        form.populate_obj(manga_item)
        selected_genres = Genre.query.filter(Genre.genre_id.in_(form.genres.data or [])).all()
        manga_item.genres = selected_genres
        selected_creators = Creator.query.filter(Creator.creator_id.in_(form.creators.data or [])).all()
        manga_item.creators = selected_creators
        db.session.commit()
        # from utils import update_content_stats
        # update_content_stats('manga', manga_item.manga_id)
        flash(f'Manga "{manga_item.title_romaji}" updated successfully.', 'success')
        return redirect(url_for('admin.manga_list_admin'))
    return render_template('admin/manga_form.html', form=form, title=f"Edit Manga: {manga_item.title_romaji}", manga=manga_item)

@admin_bp.route('/manga/<int:manga_id>/delete', methods=['POST'])
def delete_manga(manga_id):
    manga_item = Manga.query.get_or_404(manga_id)
    title_deleted = manga_item.title_romaji
    db.session.delete(manga_item)
    db.session.commit()
    flash(f'Manga "{title_deleted}" and associated data deleted successfully.', 'success')
    return redirect(url_for('admin.manga_list_admin'))

# Genre management
@admin_bp.route('/genres')
def genres_list():
    genres = Genre.query.order_by(Genre.name).all()
    return render_template('admin/genres_list.html', genres=genres)

@admin_bp.route('/genres/create', methods=['GET', 'POST'])
def create_genre():
    form = GenreForm()
    if form.validate_on_submit():
        existing_genre = Genre.query.filter(func.lower(Genre.name) == func.lower(form.name.data)).first()
        if existing_genre:
            flash(f'Genre name "{form.name.data}" already exists.', 'danger')
        else:
            new_genre = Genre(name=form.name.data, description=form.description.data)
            db.session.add(new_genre)
            db.session.commit()
            flash(f'Genre "{new_genre.name}" created successfully.', 'success')
            return redirect(url_for('admin.genres_list'))
    return render_template('admin/genre_form.html', form=form, title="Create Genre")

@admin_bp.route('/genres/<int:genre_id>/edit', methods=['GET', 'POST'])
def edit_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    form = GenreForm(obj=genre)
    if form.validate_on_submit():
        new_name_lower = form.name.data.lower()
        conflicting_genre = Genre.query.filter(Genre.genre_id != genre_id, func.lower(Genre.name) == new_name_lower).first()
        if conflicting_genre:
            flash(f'Genre name "{form.name.data}" is already used by another genre.', 'danger')
        else:
            genre.name = form.name.data
            genre.description = form.description.data
            db.session.commit()
            flash(f'Genre "{genre.name}" updated successfully.', 'success')
            return redirect(url_for('admin.genres_list'))
    return render_template('admin/genre_form.html', form=form, title=f"Edit Genre: {genre.name}", genre=genre)

@admin_bp.route('/genres/<int:genre_id>/delete', methods=['POST'])
def delete_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    # Kiểm tra xem genre có đang được sử dụng bởi Anime hoặc Manga không
    # genre.animes và genre.mangas là lazy='dynamic' collections
    if genre.animes.count() > 0 or genre.mangas.count() > 0:
        flash(f'Cannot delete genre "{genre.name}" as it is currently used by {genre.animes.count()} anime and {genre.mangas.count()} manga entries.', 'danger')
        return redirect(url_for('admin.genres_list'))
    name_deleted = genre.name
    db.session.delete(genre)
    db.session.commit()
    flash(f'Genre "{name_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.genres_list'))

# Studio management (Tương tự Genre)
@admin_bp.route('/studios')
def studios_list():
    studios = Studio.query.order_by(Studio.name).all()
    return render_template('admin/studios_list.html', studios=studios)

@admin_bp.route('/studios/create', methods=['GET', 'POST'])
def create_studio():
    form = StudioForm()
    if form.validate_on_submit():
        existing_studio = Studio.query.filter(func.lower(Studio.name) == func.lower(form.name.data)).first()
        if existing_studio:
            flash(f'Studio name "{form.name.data}" already exists.', 'danger')
        else:
            new_studio = Studio(name=form.name.data, established_date=form.established_date.data, website=form.website.data)
            db.session.add(new_studio)
            db.session.commit()
            flash(f'Studio "{new_studio.name}" created successfully.', 'success')
            return redirect(url_for('admin.studios_list'))
    return render_template('admin/studio_form.html', form=form, title="Create Studio")

@admin_bp.route('/studios/<int:studio_id>/edit', methods=['GET', 'POST'])
def edit_studio(studio_id):
    studio = Studio.query.get_or_404(studio_id)
    form = StudioForm(obj=studio)
    if form.validate_on_submit():
        new_name_lower = form.name.data.lower()
        conflicting_studio = Studio.query.filter(Studio.studio_id != studio_id, func.lower(Studio.name) == new_name_lower).first()
        if conflicting_studio:
            flash(f'Studio name "{form.name.data}" is already used.', 'danger')
        else:
            studio.name = form.name.data
            studio.established_date = form.established_date.data
            studio.website = form.website.data
            db.session.commit()
            flash(f'Studio "{studio.name}" updated successfully.', 'success')
            return redirect(url_for('admin.studios_list'))
    return render_template('admin/studio_form.html', form=form, title=f"Edit Studio: {studio.name}", studio=studio)

@admin_bp.route('/studios/<int:studio_id>/delete', methods=['POST'])
def delete_studio(studio_id):
    studio = Studio.query.get_or_404(studio_id)
    if studio.animes.count() > 0:
        flash(f'Cannot delete studio "{studio.name}" as it is associated with {studio.animes.count()} anime entries.', 'danger')
        return redirect(url_for('admin.studios_list'))
    name_deleted = studio.name
    db.session.delete(studio)
    db.session.commit()
    flash(f'Studio "{name_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.studios_list'))

# Creator management
@admin_bp.route('/creators')
def creators_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)
    query = Creator.query
    if search_term:
        query = query.filter(Creator.name.ilike(f'%{search_term}%'))
    creators_pagination = query.order_by(Creator.name).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/creators_list.html', creators=creators_pagination, search_form=search_form, search_term=search_term)

def _populate_creator_form_choices(form):
    _populate_enum_choices(form.role, Creator.creator_role_enum_values)

@admin_bp.route('/creators/create', methods=['GET', 'POST'])
def create_creator():
    form = CreatorForm()
    _populate_creator_form_choices(form)
    if form.validate_on_submit():
        # Cân nhắc kiểm tra trùng tên + role nếu cần
        new_creator = Creator(name=form.name.data, role=form.role.data, bio=form.bio.data)
        db.session.add(new_creator)
        db.session.commit()
        flash(f'Creator "{new_creator.name}" ({new_creator.role}) created successfully.', 'success')
        return redirect(url_for('admin.creators_list'))
    return render_template('admin/creator_form.html', form=form, title="Create Creator")

@admin_bp.route('/creators/<int:creator_id>/edit', methods=['GET', 'POST'])
def edit_creator(creator_id):
    creator = Creator.query.get_or_404(creator_id)
    form = CreatorForm(obj=creator)
    _populate_creator_form_choices(form)
    if form.validate_on_submit():
        creator.name = form.name.data
        creator.role = form.role.data
        creator.bio = form.bio.data
        db.session.commit()
        flash(f'Creator "{creator.name}" updated successfully.', 'success')
        return redirect(url_for('admin.creators_list'))
    return render_template('admin/creator_form.html', form=form, title=f"Edit Creator: {creator.name}", creator=creator)

@admin_bp.route('/creators/<int:creator_id>/delete', methods=['POST'])
def delete_creator(creator_id):
    creator = Creator.query.get_or_404(creator_id)
    if creator.mangas.count() > 0: # Giả sử creator chỉ liên quan đến manga qua bảng manga_creators
        flash(f'Cannot delete creator "{creator.name}" as they are associated with {creator.mangas.count()} manga entries.', 'danger')
        return redirect(url_for('admin.creators_list'))
    name_deleted = creator.name
    db.session.delete(creator)
    db.session.commit()
    flash(f'Creator "{name_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.creators_list'))

# Comments management
@admin_bp.route('/comments')
def comments_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)

    query = Comment.query.join(User, Comment.user_id == User.user_id).options(db.contains_eager(Comment.author)) # Eager load author

    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(or_(Comment.comment_text.ilike(like_pattern), User.username.ilike(like_pattern)))

    comments_pagination = query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/comments_list.html', comments=comments_pagination, search_form=search_form, search_term=search_term)

@admin_bp.route('/comments/<int:comment_id>/edit', methods=['GET', 'POST'])
def edit_comment_admin(comment_id): # Đổi tên hàm
    comment = Comment.query.get_or_404(comment_id)
    form = AdminCommentForm(obj=comment) # Sử dụng AdminCommentForm
    if form.validate_on_submit():
        comment.comment_text = form.comment_text.data
        comment.is_spoiler = form.is_spoiler.data
        comment.updated_at = datetime.utcnow() # Cập nhật thời gian sửa
        db.session.commit()
        flash('Comment updated successfully.', 'success')
        return redirect(url_for('admin.comments_list'))
    return render_template('admin/comment_form.html', form=form, title=f"Edit Comment ID: {comment.comment_id}", comment=comment)

@admin_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
def delete_comment_admin(comment_id): # Đổi tên hàm
    comment = Comment.query.get_or_404(comment_id)
    # Cascade delete cho replies đã được cấu hình trong model Comment
    db.session.delete(comment)
    db.session.commit()
    flash(f'Comment ID {comment_id} and its replies deleted successfully.', 'success')
    return redirect(url_for('admin.comments_list'))


# Fanart management
@admin_bp.route('/fanart')
def fanart_list_admin():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)

    query = Fanart.query.join(User, Fanart.user_id == User.user_id).options(db.contains_eager(Fanart.author))

    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(or_(Fanart.title.ilike(like_pattern), User.username.ilike(like_pattern)))

    fanart_pagination = query.order_by(Fanart.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/fanart_list.html', fanart_collection=fanart_pagination, search_form=search_form, search_term=search_term)

@admin_bp.route('/fanart/<int:fanart_id>/toggle-publish', methods=['POST'])
def toggle_fanart_publish(fanart_id):
    fanart_item = Fanart.query.get_or_404(fanart_id)
    fanart_item.is_published = not fanart_item.is_published
    db.session.commit()
    status_text = "published" if fanart_item.is_published else "unpublished"
    flash(f'Fanart "{fanart_item.title}" has been {status_text}.', 'success')
    return redirect(url_for('admin.fanart_list_admin'))

@admin_bp.route('/fanart/<int:fanart_id>/delete', methods=['POST'])
def delete_fanart_admin(fanart_id):
    fanart_item = Fanart.query.get_or_404(fanart_id)
    title_deleted = fanart_item.title
    db.session.delete(fanart_item) # Cascade delete cho comments liên quan (nếu có)
    db.session.commit()
    flash(f'Fanart "{title_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.fanart_list_admin'))

# Fanfiction management (Tương tự Fanart)
@admin_bp.route('/fanfiction')
def fanfiction_list_admin():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)
    query = Fanfiction.query.join(User, Fanfiction.user_id == User.user_id).options(db.contains_eager(Fanfiction.author))
    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(or_(Fanfiction.title.ilike(like_pattern), Fanfiction.summary.ilike(like_pattern), User.username.ilike(like_pattern)))
    fanfic_pagination = query.order_by(Fanfiction.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/fanfiction_list.html', fanfic_collection=fanfic_pagination, search_form=search_form, search_term=search_term)

@admin_bp.route('/fanfiction/<int:fanfiction_id>/toggle-publish', methods=['POST'])
def toggle_fanfiction_publish(fanfiction_id):
    fanfic_item = Fanfiction.query.get_or_404(fanfiction_id)
    fanfic_item.is_published = not fanfic_item.is_published
    db.session.commit()
    status_text = "published" if fanfic_item.is_published else "unpublished"
    flash(f'Fanfiction "{fanfic_item.title}" has been {status_text}.', 'success')
    return redirect(url_for('admin.fanfiction_list_admin'))

@admin_bp.route('/fanfiction/<int:fanfiction_id>/delete', methods=['POST'])
def delete_fanfiction_admin(fanfiction_id):
    fanfic_item = Fanfiction.query.get_or_404(fanfiction_id)
    title_deleted = fanfic_item.title
    db.session.delete(fanfic_item)
    db.session.commit()
    flash(f'Fanfiction "{title_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.fanfiction_list_admin'))

# Tags management
@admin_bp.route('/tags')
def tags_list():
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin/tags_list.html', tags=tags)

@admin_bp.route('/tags/create', methods=['GET', 'POST'])
def create_tag():
    form = TagForm()
    if form.validate_on_submit():
        existing_tag = Tag.query.filter(func.lower(Tag.name) == func.lower(form.name.data)).first()
        if existing_tag:
            flash(f'Tag name "{form.name.data}" already exists.', 'danger')
        else:
            new_tag = Tag(name=form.name.data, description=form.description.data, is_spoiler_tag=form.is_spoiler_tag.data)
            db.session.add(new_tag)
            db.session.commit()
            flash(f'Tag "{new_tag.name}" created successfully.', 'success')
            return redirect(url_for('admin.tags_list'))
    return render_template('admin/tag_form.html', form=form, title="Create Tag")

@admin_bp.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(obj=tag)
    if form.validate_on_submit():
        new_name_lower = form.name.data.lower()
        conflicting_tag = Tag.query.filter(Tag.tag_id != tag_id, func.lower(Tag.name) == new_name_lower).first()
        if conflicting_tag:
            flash(f'Tag name "{form.name.data}" is already used.', 'danger')
        else:
            tag.name = form.name.data
            tag.description = form.description.data
            tag.is_spoiler_tag = form.is_spoiler_tag.data
            db.session.commit()
            flash(f'Tag "{tag.name}" updated successfully.', 'success')
            return redirect(url_for('admin.tags_list'))
    return render_template('admin/tag_form.html', form=form, title=f"Edit Tag: {tag.name}", tag=tag)

@admin_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    # ContentTag model có backref 'tagged_items' đến Tag
    if tag.tagged_items.count() > 0:
        flash(f'Cannot delete tag "{tag.name}" as it is currently applied to {tag.tagged_items.count()} content item(s).', 'danger')
        return redirect(url_for('admin.tags_list'))
    name_deleted = tag.name
    db.session.delete(tag)
    db.session.commit()
    flash(f'Tag "{name_deleted}" deleted successfully.', 'success')
    return redirect(url_for('admin.tags_list'))

# AnimeSong Management (Thêm mới)
def _populate_animesong_form_choices(form, selected_anime_id=None):
    form.anime_id.choices = [(a.anime_id, a.title_romaji) for a in Anime.query.order_by(Anime.title_romaji).all()]
    if selected_anime_id: # Pre-select anime if provided (for edit or if coming from anime page)
        form.anime_id.data = selected_anime_id
    _populate_enum_choices(form.type, AnimeSong.song_type_enum_values)

@admin_bp.route('/songs', methods=['GET'])
def songs_list():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search_term = request.args.get('search', '').strip()
    search_form = AdminSearchForm(search_query=search_term)

    query = AnimeSong.query.join(Anime, AnimeSong.anime_id == Anime.anime_id)\
                           .options(db.contains_eager(AnimeSong.anime)) # Eager load anime title

    if search_term:
        like_pattern = f'%{search_term}%'
        query = query.filter(or_(
            AnimeSong.title.ilike(like_pattern),
            AnimeSong.artist.ilike(like_pattern),
            Anime.title_romaji.ilike(like_pattern) # Search by anime title
        ))
    
    songs_pagination = query.order_by(Anime.title_romaji, AnimeSong.type, AnimeSong.title)\
                            .paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/songs_list.html', songs=songs_pagination, search_form=search_form, search_term=search_term)


@admin_bp.route('/songs/create', methods=['GET', 'POST'])
@admin_bp.route('/anime/<int:for_anime_id>/songs/create', methods=['GET', 'POST']) # Route để tạo song cho anime cụ thể
def create_song(for_anime_id=None):
    form = AnimeSongForm()
    _populate_animesong_form_choices(form, selected_anime_id=for_anime_id)

    if form.validate_on_submit():
        new_song = AnimeSong()
        form.populate_obj(new_song)
        db.session.add(new_song)
        db.session.commit()
        flash(f'Song "{new_song.title}" for anime "{new_song.anime.title_romaji}" created successfully.', 'success')
        return redirect(url_for('admin.songs_list')) # Hoặc redirect về trang chi tiết anime
    
    title = "Create New Song"
    if for_anime_id:
        anime_for_song = Anime.query.get(for_anime_id)
        if anime_for_song:
            title = f"Create New Song for {anime_for_song.title_romaji}"

    return render_template('admin/song_form.html', form=form, title=title)

@admin_bp.route('/songs/<int:song_id>/edit', methods=['GET', 'POST'])
def edit_song(song_id):
    song = AnimeSong.query.get_or_404(song_id)
    form = AnimeSongForm(obj=song)
    _populate_animesong_form_choices(form) # anime_id sẽ được pre-select bởi obj=song

    if form.validate_on_submit():
        form.populate_obj(song)
        db.session.commit()
        flash(f'Song "{song.title}" updated successfully.', 'success')
        return redirect(url_for('admin.songs_list'))
    return render_template('admin/song_form.html', form=form, title=f"Edit Song: {song.title}", song=song)

@admin_bp.route('/songs/<int:song_id>/delete', methods=['POST'])
def delete_song(song_id):
    song = AnimeSong.query.get_or_404(song_id)
    title_deleted = song.title
    anime_title = song.anime.title_romaji # Lấy tên anime trước khi xóa
    db.session.delete(song)
    db.session.commit()
    flash(f'Song "{title_deleted}" for anime "{anime_title}" deleted successfully.', 'success')
    return redirect(url_for('admin.songs_list'))