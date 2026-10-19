import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("KRAVFANGST_SECRET_KEY", "dev"),
        DATABASE=os.environ.get("KRAVFANGST_DATABASE",
                                os.path.join(app.instance_path, "kravfangst.sqlite")),
    )
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(db.close_db)
    with app.app_context():
        db.init_db()

    from .views import bp
    app.register_blueprint(bp)
    return app
