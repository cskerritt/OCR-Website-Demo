import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/users.db')
    
    # Fix for SQLAlchemy with PostgreSQL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Session configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 1610612736))  # 1.5GB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    CACHE_FOLDER = os.environ.get('CACHE_FOLDER', 'ocr_cache')
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # OCR configuration
    OCR_THREADS = int(os.environ.get('OCR_THREADS', 4))
    OCR_TIMEOUT = int(os.environ.get('OCR_TIMEOUT', 1800))  # 30 minutes
    OCR_OPTIMIZE_SIZE_MB = int(os.environ.get('OCR_OPTIMIZE_SIZE_MB', 100))
    
    # Cache configuration
    CACHE_MAX_AGE_DAYS = int(os.environ.get('CACHE_MAX_AGE_DAYS', 7))
    CACHE_MAX_SIZE_MB = int(os.environ.get('CACHE_MAX_SIZE_MB', 5000))
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # Require HTTPS in production
    SESSION_COOKIE_SECURE = True
    
    # Stronger session protection
    SESSION_PROTECTION = 'strong'
    
    # Production logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}