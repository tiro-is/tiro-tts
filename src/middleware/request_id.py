class RequestIdWrapper:
    """WSGI Middleware for a passthrough header

    Example usage:
    >>> app = init_app()
    >>> request_id = RequestIdWrapper(app, header="X-Request-ID")
    >>> app.run()

    Any request with a X-Request-ID header will get the same header back in the
    response.

    """

    _header: str
    _env_header: str

    def __init__(self, app, header: str = "X-Request-ID"):
        self._header = header
        self._env_header = header.upper().replace("-", "_")
        self.app = app.wsgi_app
        app.wsgi_app = self

    def __call__(self, environ, start_response):
        req_id = environ.get("HTTP_" + self._env_header)

        def new_start_response(status, response_headers, exc_info=None):
            if req_id:
                response_headers.append((self._header, req_id))
            return start_response(status, response_headers, exc_info)

        return self.app(environ, new_start_response)
