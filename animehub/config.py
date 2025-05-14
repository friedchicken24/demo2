import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')

# --- DEBUG PRINTING ---
DEBUG_CONFIG = True # Tạm thời để True, đổi thành False hoặc lấy từ env cho prod

if DEBUG_CONFIG: print(f"DEBUG [config.py]: basedir = {basedir}")
if DEBUG_CONFIG: print(f"DEBUG [config.py]: Attempting to load .env from: {dotenv_path}")

# Gọi load_dotenv sớm để các biến môi trường có sẵn cho các class Config
# Thêm override=True để biến từ .env có thể ghi đè biến hệ thống nếu trùng tên
if os.path.exists(dotenv_path):
    loaded_successfully = load_dotenv(dotenv_path, verbose=DEBUG_CONFIG, override=True)
    if loaded_successfully:
        if DEBUG_CONFIG: print(f"DEBUG [config.py]: .env file loaded successfully.")
    else:
        if DEBUG_CONFIG: print(f"DEBUG [config.py]: .env file found, but load_dotenv returned False (possibly empty or no assignments).")
else:
    if DEBUG_CONFIG: print(f"DEBUG [config.py]: .env file NOT FOUND at {dotenv_path}.")

# In các giá trị SAU KHI load_dotenv (hoặc từ fallback nếu .env không load được)
if DEBUG_CONFIG:
    print(f"DEBUG [config.py]: FLASK_ENV from os.environ (after dotenv): {os.environ.get('FLASK_ENV')}")
    print(f"DEBUG [config.py]: SECRET_KEY from os.environ (after dotenv): {'********' if os.environ.get('SECRET_KEY') else None}")
    print(f"DEBUG [config.py]: DB_USERNAME from os.environ (after dotenv): {os.environ.get('DB_USERNAME')}")
    print(f"DEBUG [config.py]: DB_PASSWORD from os.environ (after dotenv): {'********' if os.environ.get('DB_PASSWORD') else None}")
    print(f"DEBUG [config.py]: DB_HOST from os.environ (after dotenv): {os.environ.get('DB_HOST')}")
    print(f"DEBUG [config.py]: DB_PORT from os.environ (after dotenv): {os.environ.get('DB_PORT')}")
    print(f"DEBUG [config.py]: DB_NAME from os.environ (after dotenv): {os.environ.get('DB_NAME')}")


class Config:
    # SECRET_KEY sẽ được lấy từ os.environ. Nếu không có, ProductionConfig sẽ raise lỗi.
    # DevelopmentConfig và TestingConfig có thể dùng fallback nếu muốn.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'AlexNguyen1211'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True
    }

    DB_USERNAME = os.environ.get('DB_USERNAME') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'AlexYeuViolet' # Mật khẩu fallback của bạn
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '3306'
    DB_NAME = os.environ.get('DB_NAME') or 'anime_hub' # Tên DB fallback của bạn

    # Sử dụng PyMySQL làm driver mặc định
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'

    if DEBUG_CONFIG:
        print(f"DEBUG [config.py - Config class attributes]: DB_USERNAME = {DB_USERNAME}")
        print(f"DEBUG [config.py - Config class attributes]: DB_PASSWORD = {'********' if DB_PASSWORD else 'None/Empty'}")
        print(f"DEBUG [config.py - Config class attributes]: DB_HOST = {DB_HOST}")
        print(f"DEBUG [config.py - Config class attributes]: DB_PORT = {DB_PORT}")
        print(f"DEBUG [config.py - Config class attributes]: DB_NAME = {DB_NAME}")
        db_uri_to_print_init = SQLALCHEMY_DATABASE_URI
        if DB_PASSWORD:
             db_uri_to_print_init = db_uri_to_print_init.replace(str(DB_PASSWORD), '********')
        print(f"DEBUG [config.py - Config class attributes]: Constructed SQLALCHEMY_DATABASE_URI = {db_uri_to_print_init}")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False # Đặt True nếu muốn xem SQL query
    # SECRET_KEY được kế thừa từ Config, hoặc có thể đặt riêng:
    # SECRET_KEY = os.environ.get('DEV_SECRET_KEY') or 'another_strong_dev_secret'
    if DEBUG_CONFIG: print("DEBUG [config.py]: DevelopmentConfig is being defined.")


class TestingConfig(Config):
    TESTING = True
    # Ghi đè URI cho testing, thường dùng SQLite in-memory
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False # Tắt CSRF cho testing forms
    DEBUG = True # Có thể để True để debug test dễ hơn
    # SECRET_KEY được kế thừa, hoặc đặt riêng cho test
    # SECRET_KEY = 'test_secret_key'
    if DEBUG_CONFIG: print(f"DEBUG [config.py]: TestingConfig is being defined. SQLALCHEMY_DATABASE_URI = {SQLALCHEMY_DATABASE_URI}")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # SECRET_KEY sẽ được kiểm tra trong __init__ của instance ProductionConfig

    def __init__(self):
        super().__init__() # Kế thừa các thuộc tính từ Config
        # Ghi đè và kiểm tra SECRET_KEY CHỈ KHI ProductionConfig được khởi tạo
        self.SECRET_KEY = os.environ.get('SECRET_KEY') # Production PHẢI lấy từ env
        if not self.SECRET_KEY:
            # Ghi log thay vì print trực tiếp nếu có logger sẵn
            print("CRITICAL [config.py - ProductionConfig INSTANCE]: SECRET_KEY is NOT SET from environment for Production!")
            raise ValueError("No SECRET_KEY set for production application. Please set the SECRET_KEY environment variable.")
        if DEBUG_CONFIG: print("DEBUG [config.py]: ProductionConfig instance created and SECRET_KEY checked.")


config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig # Mặc định là Development
)

# Xác định cấu hình nào sẽ được sử dụng dựa trên FLASK_ENV
# FLASK_ENV nên được load từ .env ở đầu file này
flask_env_value = os.environ.get('FLASK_ENV', 'default').lower()
if DEBUG_CONFIG: print(f"DEBUG [config.py]: FLASK_ENV from os.environ (for selection) = '{os.environ.get('FLASK_ENV')}', effective key = '{flask_env_value}'")

current_config_class = config_by_name.get(flask_env_value, DevelopmentConfig)
current_config = current_config_class() # Khởi tạo instance của class config đã chọn

if DEBUG_CONFIG:
    print(f"DEBUG [config.py]: Selected config class = {current_config_class.__name__}")
    # In ra các giá trị cuối cùng của current_config
    final_db_uri = getattr(current_config, 'SQLALCHEMY_DATABASE_URI', 'NOT SET')
    final_db_pass = getattr(current_config, 'DB_PASSWORD', None)
    if final_db_pass and final_db_uri != 'NOT SET':
        final_db_uri = final_db_uri.replace(str(final_db_pass), '********')
    print(f"DEBUG [config.py]: Final current_config.SQLALCHEMY_DATABASE_URI = {final_db_uri}")
    print(f"DEBUG [config.py]: Final current_config.SECRET_KEY = {'********' if getattr(current_config, 'SECRET_KEY', None) else None}")
    print(f"DEBUG [config.py]: Final current_config.DEBUG = {getattr(current_config, 'DEBUG', 'NOT SET')}")