from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, and_, func, desc, case # Thêm case nếu bạn muốn dùng giải pháp sắp xếp NULL phức tạp hơn

from app import db
from models import (
    User, Anime, Manga, Genre, Studio, Creator,
    Fanart, Fanfiction, Comment, Rating, Tag, ContentTag,
    UserList, ListItem, AnimeSong
)
from users.forms import (
    LoginForm, RegisterForm, ProfileForm, AnimeSearchForm, MangaSearchForm,
    CommentForm, RatingForm, ListForm, ListItemForm, FanartForm, FanfictionForm
)
from utils import (
    generate_token, update_last_login, count_words,
    get_user_lists, get_or_create_default_user_lists, update_content_stats
)

user_bp = Blueprint('user', __name__)

# Auth routes
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('This account is disabled. Please contact an administrator.', 'danger')
                return render_template('user/auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            update_last_login(user)
            db.session.commit() # Commit sau khi update_last_login

            next_page = request.args.get('next')
            flash('You have been logged in successfully!', 'success')
            return redirect(next_page or url_for('user.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('user/auth/login.html', form=form)

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('user.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        existing_user_by_username = User.query.filter_by(username=form.username.data).first()
        if existing_user_by_username:
            flash('Username already exists', 'danger')
            return render_template('user/auth/register.html', form=form)

        existing_user_by_email = User.query.filter_by(email=form.email.data).first()
        if existing_user_by_email:
            flash('Email already exists', 'danger')
            return render_template('user/auth/register.html', form=form)

        verification_token = generate_token()
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            display_name=form.display_name.data or form.username.data
        )
        user.verification_token = verification_token
        db.session.add(user)
        db.session.commit()
        get_or_create_default_user_lists(user.user_id)
        flash('Your account has been created! Please check your email to verify your account.', 'success')
        return redirect(url_for('user.login'))
    return render_template('user/auth/register.html', form=form)

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('user.index'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        if form.new_password.data:
            if not form.current_password.data:
                flash('Please enter your current password to set a new password.', 'warning')
                return render_template('user/auth/profile.html', form=form, user=current_user)
            if not current_user.check_password(form.current_password.data):
                flash('Your current password is incorrect.', 'danger')
                return render_template('user/auth/profile.html', form=form, user=current_user)
            current_user.set_password(form.new_password.data)
        current_user.display_name = form.display_name.data or current_user.username
        current_user.bio = form.bio.data
        current_user.profile_picture_url = form.profile_picture_url.data
        db.session.commit()
        flash('Your profile has been updated', 'success')
        return redirect(url_for('user.profile'))
    return render_template('user/auth/profile.html', form=form, user=current_user)

@user_bp.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_lists_query = UserList.query.filter_by(user_id=user.user_id)
    if not (current_user.is_authenticated and current_user.user_id == user.user_id):
        user_lists_query = user_lists_query.filter_by(is_public=True)
    user_lists = user_lists_query.order_by(UserList.is_main_list.desc(), UserList.list_name).all()
    fanarts = Fanart.query.filter_by(user_id=user.user_id, is_published=True).order_by(Fanart.created_at.desc()).limit(10).all()
    fanfictions = Fanfiction.query.filter_by(user_id=user.user_id, is_published=True).order_by(Fanfiction.created_at.desc()).limit(10).all()
    return render_template('user/auth/public_profile.html',
                           profile_user=user,
                           user_lists=user_lists,
                           fanarts=fanarts,
                           fanfictions=fanfictions)

# Home and search routes
@user_bp.route('/')
def index():
    # SỬA Ở ĐÂY: Bỏ .nullslast()
    latest_anime = Anime.query.order_by(Anime.aired_from.desc(), Anime.created_at.desc()).limit(6).all()
    latest_manga = Manga.query.order_by(Manga.published_from.desc(), Manga.created_at.desc()).limit(6).all()
    popular_anime = Anime.query.order_by(Anime.members_count.desc(), Anime.average_score.desc()).limit(6).all()
    popular_manga = Manga.query.order_by(Manga.members_count.desc(), Manga.average_score.desc()).limit(6).all()
    latest_fanart = Fanart.query.filter_by(is_published=True).order_by(Fanart.created_at.desc()).limit(4).all()
    latest_fanfiction = Fanfiction.query.filter_by(is_published=True).order_by(Fanfiction.created_at.desc()).limit(4).all()

    return render_template('user/index.html',
                           latest_anime=latest_anime,
                           latest_manga=latest_manga,
                           popular_anime=popular_anime,
                           popular_manga=popular_manga,
                           latest_fanart=latest_fanart,
                           latest_fanfiction=latest_fanfiction)

# Anime routes
@user_bp.route('/anime')
def anime_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    form = AnimeSearchForm(request.args)
    genres_for_form = [('', 'All Genres')]
    genres_for_form.extend([(g.genre_id, g.name) for g in Genre.query.order_by(Genre.name).all()])
    form.genre.choices = genres_for_form
    query = Anime.query
    if form.validate():
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(
                or_(
                    Anime.title_romaji.ilike(search_term),
                    Anime.title_english.ilike(search_term),
                    Anime.title_japanese.ilike(search_term)
                )
            )
        if form.type.data:
            query = query.filter(Anime.type == form.type.data)
        if form.status.data:
            query = query.filter(Anime.status == form.status.data)
        if form.genre.data:
            query = query.join(Anime.genres).filter(Genre.genre_id == form.genre.data)

        sort_by = form.sort.data or 'title'
        if sort_by == 'title':
            query = query.order_by(Anime.title_romaji)
        elif sort_by == 'score':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Anime.average_score.desc())
        elif sort_by == 'popularity':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Anime.members_count.desc())
        elif sort_by == 'latest':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Anime.aired_from.desc(), Anime.created_at.desc())
    else:
        query = query.order_by(Anime.title_romaji)
    animes = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('user/content/anime_list.html', animes=animes, form=form)

@user_bp.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    anime = Anime.query.options(
        db.joinedload(Anime.genres),
        db.joinedload(Anime.studios)
    ).get_or_404(anime_id)
    songs = AnimeSong.query.filter_by(anime_id=anime_id).order_by(AnimeSong.type, AnimeSong.title).all()
    user_lists_for_form = []
    user_rating = None
    list_item_details = None
    if current_user.is_authenticated:
        user_lists_for_form = [(ul.list_id, ul.list_name) for ul in UserList.query.filter_by(user_id=current_user.user_id).order_by(UserList.list_name).all()]
        user_rating = Rating.query.filter_by(
            user_id=current_user.user_id,
            content_type='anime',
            content_id=anime_id
        ).first()
        list_item = ListItem.query.join(UserList).filter(
            UserList.user_id == current_user.user_id,
            ListItem.content_type == 'anime',
            ListItem.content_id == anime_id
        ).first()
        if list_item:
            list_item_details = {
                'list_id': list_item.list_id,
                'status': list_item.status_in_list,
                'progress': list_item.progress,
                'score': list_item.user_score
            }
    comments = Comment.query.filter_by(
        content_type='anime',
        content_id=anime_id,
        parent_comment_id=None
    ).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm(content_type='anime', content_id=anime_id)
    rating_form = RatingForm(content_type='anime', content_id=anime_id, score=user_rating.score if user_rating else None)
    list_item_form = ListItemForm(content_type='anime', content_id=anime_id) # Đảm bảo content_type và content_id được truyền
    list_item_form.list_id.choices = user_lists_for_form
    if list_item_details:
        list_item_form.list_id.data = list_item_details['list_id']
        list_item_form.status.data = list_item_details['status']
        list_item_form.progress.data = list_item_details['progress']
        list_item_form.score.data = list_item_details['score']
    return render_template('user/content/anime_detail.html',
                          anime=anime,
                          songs=songs,
                          user_rating=user_rating,
                          comments=comments,
                          comment_form=comment_form,
                          rating_form=rating_form,
                          list_item_form=list_item_form,
                          list_item_details=list_item_details)

# Manga routes
@user_bp.route('/manga')
def manga_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    form = MangaSearchForm(request.args)
    genres_for_form = [('', 'All Genres')]
    genres_for_form.extend([(g.genre_id, g.name) for g in Genre.query.order_by(Genre.name).all()])
    form.genre.choices = genres_for_form
    query = Manga.query
    if form.validate():
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(or_(Manga.title_romaji.ilike(search_term), Manga.title_english.ilike(search_term), Manga.title_japanese.ilike(search_term)))
        if form.type.data:
            query = query.filter(Manga.type == form.type.data)
        if form.status.data:
            query = query.filter(Manga.status == form.status.data)
        if form.genre.data:
            query = query.join(Manga.genres).filter(Genre.genre_id == form.genre.data)
        sort_by = form.sort.data or 'title'
        if sort_by == 'title':
            query = query.order_by(Manga.title_romaji)
        elif sort_by == 'score':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Manga.average_score.desc())
        elif sort_by == 'popularity':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Manga.members_count.desc())
        elif sort_by == 'latest':
            # SỬA Ở ĐÂY: Bỏ .nullslast()
            query = query.order_by(Manga.published_from.desc(), Manga.created_at.desc())
    else:
        query = query.order_by(Manga.title_romaji)
    mangas = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('user/content/manga_list.html', mangas=mangas, form=form)

@user_bp.route('/manga/<int:manga_id>')
def manga_detail(manga_id):
    manga = Manga.query.options(
        db.joinedload(Manga.genres),
        db.joinedload(Manga.creators)
    ).get_or_404(manga_id)
    user_lists_for_form = []
    user_rating = None
    list_item_details = None
    if current_user.is_authenticated:
        user_lists_for_form = [(ul.list_id, ul.list_name) for ul in UserList.query.filter_by(user_id=current_user.user_id).order_by(UserList.list_name).all()]
        user_rating = Rating.query.filter_by(user_id=current_user.user_id, content_type='manga', content_id=manga_id).first()
        list_item = ListItem.query.join(UserList).filter(
            UserList.user_id == current_user.user_id,
            ListItem.content_type == 'manga',
            ListItem.content_id == manga_id
        ).first()
        if list_item:
            list_item_details = {
                'list_id': list_item.list_id,
                'status': list_item.status_in_list,
                'progress': list_item.progress,
                'score': list_item.user_score
            }
    comments = Comment.query.filter_by(content_type='manga', content_id=manga_id, parent_comment_id=None).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm(content_type='manga', content_id=manga_id)
    rating_form = RatingForm(content_type='manga', content_id=manga_id, score=user_rating.score if user_rating else None)
    list_item_form = ListItemForm(content_type='manga', content_id=manga_id) # Đảm bảo content_type và content_id được truyền
    list_item_form.list_id.choices = user_lists_for_form
    if list_item_details:
        list_item_form.list_id.data = list_item_details['list_id']
        list_item_form.status.data = list_item_details['status']
        list_item_form.progress.data = list_item_details['progress']
        list_item_form.score.data = list_item_details['score']
    return render_template('user/content/manga_detail.html',
                          manga=manga,
                          user_rating=user_rating,
                          comments=comments,
                          comment_form=comment_form,
                          rating_form=rating_form,
                          list_item_form=list_item_form,
                          list_item_details=list_item_details)

# User lists routes
@user_bp.route('/lists')
@login_required
def user_lists_page():
    lists = UserList.query.filter_by(user_id=current_user.user_id).order_by(UserList.is_main_list.desc(), UserList.list_name).all()
    form = ListForm()
    return render_template('user/lists/user_lists.html', lists=lists, form=form)

@user_bp.route('/lists/create', methods=['POST'])
@login_required
def create_list():
    form = ListForm()
    if form.validate_on_submit():
        existing_list = UserList.query.filter_by(
            user_id=current_user.user_id,
            list_name=form.list_name.data
        ).first()
        if existing_list:
            flash('A list with this name already exists.', 'danger')
        else:
            new_list = UserList(
                user_id=current_user.user_id,
                list_name=form.list_name.data,
                description=form.description.data,
                is_public=form.is_public.data,
                is_main_list=False
            )
            db.session.add(new_list)
            db.session.commit()
            flash('Your list has been created.', 'success')
    else:
        for field, errors_list in form.errors.items():
            for error in errors_list:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('user.user_lists_page'))

@user_bp.route('/lists/<int:list_id>')
def view_list(list_id):
    user_list = UserList.query.get_or_404(list_id)
    list_owner = User.query.get(user_list.user_id)
    if not user_list.is_public and (not current_user.is_authenticated or user_list.user_id != current_user.user_id):
        flash('This list is private or you do not have permission to view it.', 'warning')
        return redirect(url_for('user.index'))
    items_with_content = []
    list_items = ListItem.query.filter_by(list_id=list_id).order_by(ListItem.updated_at.desc()).all()
    anime_ids = [item.content_id for item in list_items if item.content_type == 'anime']
    manga_ids = [item.content_id for item in list_items if item.content_type == 'manga']
    animes_dict = {a.anime_id: a for a in Anime.query.filter(Anime.anime_id.in_(anime_ids)).all()} if anime_ids else {}
    mangas_dict = {m.manga_id: m for m in Manga.query.filter(Manga.manga_id.in_(manga_ids)).all()} if manga_ids else {}
    for item in list_items:
        content_obj = None
        if item.content_type == 'anime':
            content_obj = animes_dict.get(item.content_id)
        elif item.content_type == 'manga':
            content_obj = mangas_dict.get(item.content_id)
        if content_obj:
            items_with_content.append({'item': item, 'content': content_obj})
    return render_template('user/lists/user_list_detail.html',
                          user_list=user_list,
                          items_with_content=items_with_content,
                          list_owner=list_owner)

@user_bp.route('/list-item/manage', methods=['POST'])
@login_required
def manage_list_item():
    form = ListItemForm(request.form)
    form.list_id.choices = [(ul.list_id, ul.list_name) for ul in UserList.query.filter_by(user_id=current_user.user_id).all()]
    if form.validate_on_submit():
        list_id = form.list_id.data
        content_type = form.content_type.data
        content_id = int(form.content_id.data) # Chuyển content_id sang int
        status = form.status.data
        progress = form.progress.data
        score = form.score.data
        user_list = UserList.query.filter_by(list_id=list_id, user_id=current_user.user_id).first()
        if not user_list:
            flash('List not found or you do not have permission.', 'danger')
            return redirect(request.referrer or url_for('user.index'))
        content_exists = None
        if content_type == 'anime':
            content_exists = Anime.query.get(content_id)
        elif content_type == 'manga':
            content_exists = Manga.query.get(content_id)
        if not content_exists:
            flash(f"Invalid content: {content_type} with ID {content_id}", "danger")
            return redirect(request.referrer or url_for('user.index'))
        existing_item = ListItem.query.filter_by(
            list_id=list_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        action_taken = ""
        if existing_item:
            existing_item.status_in_list = status
            existing_item.progress = progress if progress is not None else existing_item.progress
            existing_item.user_score = score if score is not None else existing_item.user_score
            existing_item.updated_at = datetime.utcnow()
            if status in ['completed', 'completed_manga'] and not existing_item.finished_date:
                existing_item.finished_date = datetime.utcnow().date()
            elif status not in ['completed', 'completed_manga']:
                existing_item.finished_date = None
            action_taken = "updated"
        else:
            new_item = ListItem(
                list_id=list_id,
                content_type=content_type,
                content_id=content_id,
                status_in_list=status,
                progress=progress or 0,
                user_score=score,
                started_date=datetime.utcnow().date(), # Chỉ đặt khi tạo mới
                updated_at=datetime.utcnow()
            )
            if status in ['completed', 'completed_manga']:
                new_item.finished_date = datetime.utcnow().date()
            db.session.add(new_item)
            action_taken = "added"
        db.session.commit()
        update_content_stats(content_type, content_id)
        flash(f'Item {action_taken} successfully.', 'success')
    else:
        for field, errors_list in form.errors.items():
            for error in errors_list:
                flash(f"Error in {getattr(form, field).label.text if hasattr(getattr(form, field), 'label') else field}: {error}", 'danger')
    # Redirect về trang chi tiết của content
    redirect_target = f'user.{content_type}_detail'
    redirect_kwargs = {f'{content_type}_id': content_id}
    return redirect(request.referrer or url_for(redirect_target, **redirect_kwargs))


@user_bp.route('/list-item/<int:list_item_id>/delete', methods=['POST'])
@login_required
def delete_list_item(list_item_id):
    item = ListItem.query.get_or_404(list_item_id)
    user_list = UserList.query.filter_by(list_id=item.list_id, user_id=current_user.user_id).first()
    if not user_list:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(request.referrer or url_for('user.index'))
    content_type = item.content_type
    content_id = item.content_id
    db.session.delete(item)
    db.session.commit()
    update_content_stats(content_type, content_id)
    flash('Item removed from list.', 'success')
    return redirect(request.referrer or url_for('user.view_list', list_id=user_list.list_id))

# Comment routes
@user_bp.route('/comment/add', methods=['POST'])
@login_required
def add_comment():
    form = CommentForm()
    if form.validate_on_submit():
        content_type = form.content_type.data
        content_id = int(form.content_id.data)
        parent_comment_id = int(form.parent_comment_id.data) if form.parent_comment_id.data else None
        content = None
        if content_type == 'anime': content = Anime.query.get(content_id)
        elif content_type == 'manga': content = Manga.query.get(content_id)
        elif content_type == 'fanart': content = Fanart.query.get(content_id)
        elif content_type == 'fanfiction': content = Fanfiction.query.get(content_id)
        elif content_type == 'user_profile': content = User.query.get(content_id)
        elif content_type == 'song': content = AnimeSong.query.get(content_id)
        if not content:
            flash('Cannot comment on non-existent content.', 'danger')
            return redirect(request.referrer or url_for('user.index'))
        comment = Comment(
            user_id=current_user.user_id,
            parent_comment_id=parent_comment_id,
            content_type=content_type,
            content_id=content_id,
            comment_text=form.comment_text.data,
            is_spoiler=form.is_spoiler.data
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.', 'success')
    else:
        for field, errors_list in form.errors.items():
            for error in errors_list:
                flash(f"Error in comment: {error}", 'danger')
    redirect_url = request.referrer
    if not redirect_url:
        if content_type == 'anime': redirect_url = url_for('user.anime_detail', anime_id=content_id)
        elif content_type == 'manga': redirect_url = url_for('user.manga_detail', manga_id=content_id)
        else: redirect_url = url_for('user.index')
    return redirect(redirect_url)

@user_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.user_id:
        flash('You do not have permission to delete this comment.', 'danger')
        return redirect(request.referrer or url_for('user.index'))
    content_type = comment.content_type
    content_id = comment.content_id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    redirect_url = request.referrer
    if not redirect_url:
        if content_type == 'anime': redirect_url = url_for('user.anime_detail', anime_id=content_id)
        elif content_type == 'manga': redirect_url = url_for('user.manga_detail', manga_id=content_id)
        else: redirect_url = url_for('user.index')
    return redirect(redirect_url)

# Rating routes
@user_bp.route('/content/rate', methods=['POST'])
@login_required
def rate_content():
    form = RatingForm()
    if form.validate_on_submit():
        content_type = form.content_type.data
        content_id = int(form.content_id.data)
        score = form.score.data
        content = None
        if content_type == 'anime': content = Anime.query.get(content_id)
        elif content_type == 'manga': content = Manga.query.get(content_id)
        if not content:
            flash('Cannot rate non-existent content.', 'danger')
            return redirect(request.referrer or url_for('user.index'))
        existing_rating = Rating.query.filter_by(
            user_id=current_user.user_id,
            content_type=content_type,
            content_id=content_id
        ).first()
        if existing_rating:
            if score == 0:
                db.session.delete(existing_rating)
                flash('Your rating has been removed.', 'success')
            else:
                existing_rating.score = score
                existing_rating.updated_at = datetime.utcnow()
                flash('Your rating has been updated.', 'success')
        elif score > 0 :
            new_rating = Rating(
                user_id=current_user.user_id,
                content_type=content_type,
                content_id=content_id,
                score=score
            )
            db.session.add(new_rating)
            flash('Your rating has been saved.', 'success')
        db.session.commit()
        update_content_stats(content_type, content_id)
    else:
        for field, errors_list in form.errors.items():
            for error in errors_list:
                flash(f"Error in rating: {error}", 'danger')
    redirect_url = request.referrer
    if not redirect_url:
        if content_type == 'anime': redirect_url = url_for('user.anime_detail', anime_id=content_id)
        elif content_type == 'manga': redirect_url = url_for('user.manga_detail', manga_id=content_id)
        else: redirect_url = url_for('user.index')
    return redirect(redirect_url)

# Fanart routes
@user_bp.route('/fanart')
def fanart_list():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    query = Fanart.query.filter_by(is_published=True).order_by(Fanart.created_at.desc())
    fanarts = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('user/community/fanart_list.html', fanarts=fanarts)

@user_bp.route('/fanart/<int:fanart_id>')
def fanart_detail(fanart_id):
    fanart = Fanart.query.get_or_404(fanart_id)
    if not fanart.is_published and (not current_user.is_authenticated or fanart.user_id != current_user.user_id):
        flash('This fanart is not available or you do not have permission to view it.', 'warning')
        return redirect(url_for('user.fanart_list'))
    comments = Comment.query.filter_by(content_type='fanart', content_id=fanart_id, parent_comment_id=None).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm(content_type='fanart', content_id=fanart_id)
    return render_template('user/community/fanart_detail.html',
                          fanart=fanart, comments=comments, comment_form=comment_form)

@user_bp.route('/fanart/create', methods=['GET', 'POST'])
@login_required
def create_fanart():
    form = FanartForm()
    if form.validate_on_submit():
        fanart = Fanart(
            user_id=current_user.user_id,
            title=form.title.data,
            image_url=form.image_url.data,
            description=form.description.data,
            is_published=form.is_published.data
        )
        db.session.add(fanart)
        db.session.commit()
        flash('Your fanart has been posted!', 'success')
        return redirect(url_for('user.fanart_detail', fanart_id=fanart.fanart_id))
    return render_template('user/community/create_edit_fanart.html', form=form, mode='Create')

@user_bp.route('/fanart/<int:fanart_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_fanart(fanart_id):
    fanart = Fanart.query.filter_by(fanart_id=fanart_id, user_id=current_user.user_id).first_or_404()
    form = FanartForm(obj=fanart)
    if form.validate_on_submit():
        form.populate_obj(fanart)
        db.session.commit()
        flash('Your fanart has been updated!', 'success')
        return redirect(url_for('user.fanart_detail', fanart_id=fanart.fanart_id))
    return render_template('user/community/create_edit_fanart.html', form=form, fanart=fanart, mode='Edit')

@user_bp.route('/fanart/<int:fanart_id>/delete', methods=['POST'])
@login_required
def delete_fanart(fanart_id):
    fanart = Fanart.query.filter_by(fanart_id=fanart_id, user_id=current_user.user_id).first_or_404()
    db.session.delete(fanart)
    db.session.commit()
    flash('Fanart deleted successfully.', 'success')
    return redirect(url_for('user.fanart_list'))

# Fanfiction routes
@user_bp.route('/fanfiction')
def fanfiction_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = Fanfiction.query.filter_by(is_published=True).order_by(Fanfiction.created_at.desc())
    fanfictions = query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('user/community/fanfiction_list.html', fanfictions=fanfictions)

@user_bp.route('/fanfiction/<int:fanfiction_id>')
def fanfiction_detail(fanfiction_id):
    fanfiction = Fanfiction.query.get_or_404(fanfiction_id)
    if not fanfiction.is_published and (not current_user.is_authenticated or fanfiction.user_id != current_user.user_id):
        flash('This fanfiction is not available or you do not have permission to view it.', 'warning')
        return redirect(url_for('user.fanfiction_list'))
    comments = Comment.query.filter_by(content_type='fanfiction', content_id=fanfiction_id, parent_comment_id=None).order_by(Comment.created_at.desc()).all()
    comment_form = CommentForm(content_type='fanfiction', content_id=fanfiction_id)
    return render_template('user/community/fanfiction_detail.html',
                          fanfiction=fanfiction, comments=comments, comment_form=comment_form)

@user_bp.route('/fanfiction/create', methods=['GET', 'POST'])
@login_required
def create_fanfiction():
    form = FanfictionForm()
    if form.validate_on_submit():
        fanfiction = Fanfiction(user_id=current_user.user_id)
        form.populate_obj(fanfiction)
        fanfiction.word_count = count_words(form.content.data)
        db.session.add(fanfiction)
        db.session.commit()
        flash('Your fanfiction has been posted!', 'success')
        return redirect(url_for('user.fanfiction_detail', fanfiction_id=fanfiction.fanfiction_id))
    return render_template('user/community/create_edit_fanfiction.html', form=form, mode='Create')

@user_bp.route('/fanfiction/<int:fanfiction_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_fanfiction(fanfiction_id):
    fanfiction = Fanfiction.query.filter_by(fanfiction_id=fanfiction_id, user_id=current_user.user_id).first_or_404()
    form = FanfictionForm(obj=fanfiction)
    if form.validate_on_submit():
        form.populate_obj(fanfiction)
        fanfiction.word_count = count_words(form.content.data)
        db.session.commit()
        flash('Your fanfiction has been updated!', 'success')
        return redirect(url_for('user.fanfiction_detail', fanfiction_id=fanfiction.fanfiction_id))
    return render_template('user/community/create_edit_fanfiction.html', form=form, fanfiction=fanfiction, mode='Edit')

@user_bp.route('/fanfiction/<int:fanfiction_id>/delete', methods=['POST'])
@login_required
def delete_fanfiction(fanfiction_id):
    fanfiction = Fanfiction.query.filter_by(fanfiction_id=fanfiction_id, user_id=current_user.user_id).first_or_404()
    db.session.delete(fanfiction)
    db.session.commit()
    flash('Fanfiction deleted successfully.', 'success')
    return redirect(url_for('user.fanfiction_list'))