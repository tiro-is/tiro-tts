import logging
from src import init_app

app = init_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
