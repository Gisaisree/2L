"""Central error handling (C6). Details go to the server log only."""
from flask import render_template, redirect, url_for
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from app import login_manager

_GENERIC = {
    400: "The request could not be processed. Please go back and try again.",
    404: "The page or task you asked for was not found.",
    405: "That action is not allowed.",
    500: "Something went wrong. Please try again later.",
}


def _render(status):
    message = _GENERIC.get(status, _GENERIC[400] if status < 500 else _GENERIC[500])
    return render_template("error.html", status=status, message=message), status


def register_error_handlers(app):
    @login_manager.unauthorized_handler
    def _unauthorized():
        return redirect(url_for("auth.login"))

    @app.errorhandler(CSRFError)
    def _csrf_error(error):
        # Log the category only; never the token value.
        app.logger.warning("CSRF validation failed: %s", type(error).__name__)
        return _render(400)

    @app.errorhandler(HTTPException)
    def _http_error(error):
        status = error.code or 500
        if status >= 500:
            app.logger.error("HTTP error %s", status)
        return _render(status)

    @app.errorhandler(Exception)
    def _unexpected(error):
        # Traceback goes to the server log; parameters are hidden by the engine.
        app.logger.error("Unhandled %s", type(error).__name__, exc_info=error)
        return _render(500)
