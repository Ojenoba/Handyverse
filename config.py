import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'df7e5c9b844a5f1cd653d520c156c273713aad55d3bdac89')
    # Use DATABASE_URL from environment (Render/Heroku), else fallback to local SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        '7d8b8ca920cc0c3c637d3ed37abfbfc3'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Use /tmp/uploads on Render (writable), else local uploads folder
    UPLOAD_FOLDER = os.getenv(
        'UPLOAD_FOLDER',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    )
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() in ('true', '1', 't')

    @staticmethod
    def warn_if_insecure():
        if Config.SECRET_KEY == 'df7e5c9b844a5f1cd653d520c156c273713aad55d3bdac89':
            print("WARNING: Using default SECRET_KEY. Set a secure SECRET_KEY in your environment for production.")

Config.warn_if_insecure()