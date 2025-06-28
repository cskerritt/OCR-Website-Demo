import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_compress import Compress
from werkzeug.middleware.proxy_fix import ProxyFix
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from config import config

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
compress = Compress()

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Sentry for error tracking in production
    if app.config.get('SENTRY_DSN') and config_name == 'production':
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        )
    
    # Trust proxy headers (for deployment behind reverse proxy)
    if config_name == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    compress.init_app(app)
    
    # Security headers with Talisman (HTTPS enforcer)
    if config_name == 'production':
        Talisman(app, 
                force_https=True,
                strict_transport_security=True,
                content_security_policy={
                    'default-src': "'self'",
                    'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
                    'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
                    'img-src': "'self' data: https:",
                    'font-src': "'self' cdn.jsdelivr.net"
                })
    
    # Rate limiting
    if app.config.get('RATELIMIT_ENABLED'):
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=[app.config.get('RATELIMIT_DEFAULT')],
            storage_uri=app.config.get('RATELIMIT_STORAGE_URL')
        )
    
    # Configure logging
    if not app.debug:
        configure_logging(app)
    
    # Register blueprints
    from app import app as legacy_app
    
    # Import routes and models
    with app.app_context():
        # Import models to register them with SQLAlchemy
        from app import User
        
        # Create tables if they don't exist
        db.create_all()
        
        # Import all routes
        import app as routes_module
        
        # Register all routes from the original app
        for rule in legacy_app.url_map.iter_rules():
            # Skip static endpoint
            if rule.endpoint == 'static':
                continue
                
            # Get the view function
            view_func = legacy_app.view_functions.get(rule.endpoint)
            if view_func:
                # Register the route with all its methods
                app.add_url_rule(
                    rule.rule,
                    endpoint=rule.endpoint,
                    view_func=view_func,
                    methods=rule.methods
                )
    
    # Add custom error handlers
    register_error_handlers(app)
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        for header, value in app.config.get('SECURITY_HEADERS', {}).items():
            response.headers[header] = value
        return response
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'timestamp': os.environ.get('DEPLOY_TIME', 'unknown')}
    
    return app

def configure_logging(app):
    """Configure logging for production"""
    # Remove default handler
    app.logger.handlers = []
    
    # Set up JSON logging for production
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    ))
    
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Log startup
    app.logger.info(f"Application starting in {app.config.get('ENV')} mode")

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        return {'error': 'File too large. Maximum size is 1.5GB'}, 413

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)