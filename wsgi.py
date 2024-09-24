from app import app


if __name__ == "__main__":
    from os import environ
    from werkzeug.serving import run_simple

    port = int(environ.get("PORT", 5000))
    run_simple('0.0.0.0', port, app)