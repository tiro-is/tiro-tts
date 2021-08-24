import copy

import flask


def clean_request(kwargs):
    kwargs = copy.copy(kwargs)
    if "Text" in kwargs and flask.current_app.get("STRIP_TEXT"):
        kwargs["Text"] = "... {} characters ...".format(len(kwargs["Text"]))
    return kwargs
