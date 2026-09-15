# config.py
import os
from dotenv import load_dotenv

# Muat variabel dari file .env
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))  

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kunci_default_untuk_tes_saja')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///sekolah.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, '..', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)