
from app import create_app, db # Import create_app và db từ app.py

# Tạo instance ứng dụng. create_app() sẽ tự động dùng current_config từ config.py
app = create_app() 

if __name__ == '__main__':
  
    app.run(host='0.0.0.0', port=5000)