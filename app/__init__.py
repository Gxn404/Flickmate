from . import login, recommendation, register, movie, admin, api, home, profile, wishlist, settings
from flask import Flask
def create_app():
    app = Flask(__name__)

    SECRET_KEY = 'I AM HIDDEN'
    app.config['SECRET_KEY'] = SECRET_KEY
    app.register_blueprint(api.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(register.bp)
    app.register_blueprint(movie.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(wishlist.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(recommendation.bp)
    
    return app