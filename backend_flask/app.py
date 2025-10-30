from flask import Flask
import os
import logging

# Support running as a package (python -m backend_flask.app) and as a script
try:
    from backend_flask.routes.upload_routes import upload_bp
    from backend_flask.routes.flashcard_routes import flashcard_bp
    from backend_flask.config import UPLOAD_DIR, GENERATED_DIR, HOST, PORT, DEBUG
except ModuleNotFoundError:
    # fallback when running `python app.py` from inside backend_flask/
    from routes.upload_routes import upload_bp
    from routes.flashcard_routes import flashcard_bp
    from config import UPLOAD_DIR, GENERATED_DIR, HOST, PORT, DEBUG

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(flashcard_bp, url_prefix='/api')

# ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)


@app.route('/')
def index():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    logger.info(f"Starting backend on {HOST}:{PORT}, uploads={UPLOAD_DIR}, generated={GENERATED_DIR}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
