
import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'kunci_default_untuk_tes_saja'
    )

    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL:
        # Normalisasi URL PostgreSQL bila disediakan sebagai postgres://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace(
                'postgres://',
                'postgresql://',
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
            basedir, 'sekolah.db'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if os.environ.get('ENV') == 'production':
        UPLOAD_FOLDER = '/app/static/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(
            basedir, 'static', 'uploads'
        )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
