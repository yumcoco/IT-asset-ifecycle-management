from flask import Flask
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker
import os
from .models import init_db

# Create application instance
app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')

# Enable CORS
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'lisa'

# 确保数据库目录存在
db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'db'))
if not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "supply_chain.sqlite")}'
app.config['DEBUG'] = True

# Initialize database
engine = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=engine)

# Import routes
from .routes import *

# Register blueprints (if any)