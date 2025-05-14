# app.py
import os
import logging
import traceback
# from models import User # User sẽ được import bên trong user_loader và create_app nếu cần
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Import cấu hình ĐÚNG
from config import current_config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    # Create Flask application
    app = Flask(__name__)

    # Load configuration TỪ INSTANCE ĐÃ CHỌN
    app.config.from_object(current_config)

    # In ra để kiểm tra (có thể giữ lại trong dev, xóa/comment trong prod)
    print(f"DEBUG [app.py - create_app]: Loaded config type: {type(current_config).__name__}")
    print(f"DEBUG [app.py - create_app]: SQLALCHEMY_DATABASE_URI from app.config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"DEBUG [app.py - create_app]: SECRET_KEY from app.config: {'********' if app.config.get('SECRET_KEY') else None}")

    # SECRET_KEY đã được đặt bởi app.config.from_object(current_config)
    # Dòng app.secret_key = os.environ.get(...) là không cần thiết nữa.

    # Configure proxy settings
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login
    login_manager.login_view = 'user.login' # Đảm bảo blueprint 'user' và route 'login' tồn tại
    login_manager.login_message_category = 'info'

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', # Giả sử bạn có template error.html
                              error_title="Page Not Found",
                              error_message="The requested page does not exist."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        # Sửa lại: chỉ hiển thị traceback chi tiết nếu app.debug là True
        error_details = traceback.format_exc() if app.debug else "Details hidden in production."
        return render_template('error.html', # Giả sử bạn có template error.html
                              error_title="Server Error",
                              error_message="An internal server error occurred. Please try again later.",
                              error_details=error_details), 500

    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        # Chỉ cần User cho user_loader, các model khác sẽ được Flask-Migrate tự tìm
        # Tuy nhiên, để chắc chắn, có thể import các model chính ở đây nếu cần.
        from models import User

        # Register blueprints
        # --- BỎ COMMENT VÀ SỬA ĐƯỜNG DẪN IMPORT NẾU CẦN ---
        from users.routes import user_bp  # Giả sử thư mục là 'users'
        from admin.routes import admin_bp  # Giả sử thư mục là 'admin'

        app.register_blueprint(user_bp)
        app.register_blueprint(admin_bp, url_prefix='/admin')
        # --- KẾT THÚC PHẦN BỎ COMMENT ---

    return app

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User # Import User ở đây để tránh circular import
    return User.query.get(int(user_id))

# Dòng này nên được đặt trong file chạy chính (ví dụ main.py hoặc wsgi.py)
# Nếu bạn dùng `flask run`, Flask sẽ tự tìm `create_app` hoặc `app`.
# app = create_app() # Không nên gọi ở đây nếu đây là file thư viện