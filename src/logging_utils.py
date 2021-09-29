import copy

import flask


def clean_request(kwargs):
    kwargs = copy.copy(kwargs)
    if (
        not flask.current_app.debug
        and "Text" in kwargs
        and flask.current_app.config.get("STRIP_TEXT")
    ):
        kwargs["Text"] = "... {} characters ...".format(len(kwargs["Text"]))
    return kwargs
