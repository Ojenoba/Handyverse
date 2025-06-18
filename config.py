import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'df7e5c9b844a5f1cd653d520c156c273713aad55d3bdac89')  # Default to a fixed key if .env is missing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///C:/Users/Ojenoba/Desktop/handyverse/instance/handyverse.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'True').lower() in ('true', '1', 't')

if not Config.SECRET_KEY or Config.SECRET_KEY == 'df7e5c9b844a5f1cd653d520c156c273713aad55d3bdac89':
    raise ValueError("SECRET_KEY is insecure or not set. Use a secure value via environment variable (e.g., set SECRET_KEY in .env).")