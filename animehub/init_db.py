# init_db.py
import os
from app import create_app, db # Import hàm factory và đối tượng db
# Models sẽ được import bên trong app_context

# Lấy cấu hình từ biến môi trường FLASK_ENV hoặc mặc định là 'development'
# Điều này đảm bảo script sử dụng đúng cấu hình khi chạy độc lập.
# config_name = os.environ.get('FLASK_ENV') or 'development'
# app_instance = create_app(config_name)
# create_app() trong app.py đã tự động xử lý việc chọn config dựa trên FLASK_ENV

app_instance = create_app() # create_app sẽ tự load current_config

def initialize_database(app_context_instance):
    """Initializes the database tables and optionally seeds initial data."""
    with app_context_instance.app_context(): # Rất quan trọng: cần app_context
        print(f"INFO [init_db.py]: Using database URI: {app_context_instance.config.get('SQLALCHEMY_DATABASE_URI')}")
        if not app_context_instance.config.get('SQLALCHEMY_DATABASE_URI'):
            print("ERROR [init_db.py]: SQLALCHEMY_DATABASE_URI is NOT SET in app config. Aborting.")
            return

        print("INFO [init_db.py]: Attempting to import models...")
        try:
            import models # Import models ở đây để đảm bảo chúng được SQLAlchemy biết đến
            print("INFO [init_db.py]: Models imported successfully.")
        except ImportError as e:
            print(f"ERROR [init_db.py]: Could not import models: {e}. Make sure models.py is accessible.")
            return
        except Exception as e:
            print(f"ERROR [init_db.py]: An unexpected error occurred during model import: {e}")
            return


        # Cân nhắc drop_all() chỉ khi trong môi trường development và có cờ đặc biệt
        # Ví dụ: if app_context_instance.config.get('DEBUG') and os.environ.get('FORCE_DB_RESET'):
        #     print("WARNING [init_db.py]: Dropping all tables...")
        #     db.drop_all()
        #     print("INFO [init_db.py]: All tables dropped.")

        print("INFO [init_db.py]: Attempting to create all database tables...")
        try:
            db.create_all()
            print("INFO [init_db.py]: Database tables created successfully (or already existed).")
        except Exception as e:
            print(f"ERROR [init_db.py]: Failed to create database tables: {e}")
            # In ra traceback để debug nếu cần
            # import traceback
            # traceback.print_exc()
            return # Dừng lại nếu không tạo được bảng

        # Seed dữ liệu ban đầu (ví dụ: Roles)
        seed_initial_data(db) # Gọi hàm seed riêng

def seed_initial_data(db_session):
    """Seeds initial data like roles, default admin user, etc."""
    print("INFO [init_db.py]: Seeding initial data...")

    # Seed Roles
    from models import Role
    default_roles = [
        {'role_name': 'admin', 'description': 'Administrator with full access.'},
        {'role_name': 'moderator', 'description': 'Moderator for content and comments.'},
        {'role_name': 'editor', 'description': 'Editor for anime/manga data.'},
        {'role_name': 'user', 'description': 'Regular registered user.'}
    ]
    roles_added_count = 0
    for role_data in default_roles:
        if not Role.query.filter_by(role_name=role_data['role_name']).first():
            role = Role(role_name=role_data['role_name'], description=role_data['description'])
            db_session.session.add(role)
            roles_added_count += 1
    if roles_added_count > 0:
        try:
            db_session.session.commit()
            print(f"INFO [init_db.py]: Added {roles_added_count} initial roles.")
        except Exception as e:
            db_session.session.rollback()
            print(f"ERROR [init_db.py]: Failed to seed roles: {e}")
    else:
        print("INFO [init_db.py]: Roles already seeded or no default roles defined.")

    # Seed Default Admin User (Cẩn thận với thông tin nhạy cảm)
    from models import User
    admin_username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'SecurePassword123!') # Lấy từ env

    if not User.query.filter_by(username=admin_username).first():
        admin_role = Role.query.filter_by(role_name='admin').first()
        if not admin_role:
            print("WARNING [init_db.py]: 'admin' role not found. Cannot create default admin user.")
        else:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password=admin_password, # Model User sẽ hash
                display_name="Site Administrator",
                is_active=True,
                is_verified=True # Admin được verify ngay
            )
            admin_user.roles.append(admin_role)
            db_session.session.add(admin_user)
            try:
                db_session.session.commit()
                print(f"INFO [init_db.py]: Default admin user '{admin_username}' created.")
                # Tạo default lists cho admin user
                from utils import get_or_create_default_user_lists
                get_or_create_default_user_lists(admin_user.user_id) # utils function tự commit
                print(f"INFO [init_db.py]: Created default lists for admin user '{admin_username}'.")

            except Exception as e:
                db_session.session.rollback()
                print(f"ERROR [init_db.py]: Failed to create default admin user: {e}")
    else:
        print(f"INFO [init_db.py]: Admin user '{admin_username}' already exists.")

    print("INFO [init_db.py]: Initial data seeding process complete.")


if __name__ == '__main__':
    print("--- Initializing Database ---")
    initialize_database(app_instance)
    print("--- Database Initialization Script Finished ---")