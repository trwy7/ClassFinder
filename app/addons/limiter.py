"""
Implements rate limiting.
"""
from flask_limiter import Limiter
from flask import request
from app import app

if app.config.get("TESTING"):
    class FakeLimiter: # pylint: disable=too-few-public-methods
        """A fake limiter for use when testing, overwrites the limiter.limit function"""
        def limit(self, *args, **kwargs): #pylint: disable=unused-argument
            """Fake limiter function, does nothing"""
            def decorator(f):
                return f
            return decorator
    limiter = FakeLimiter()
else:
    limiter = Limiter(
		app=app,
		key_func=lambda: request.remote_addr,
		storage_uri="memory://",
		# default_limits=["150 per minute", "8 per second"] if not app.config.get("TESTING") else ["1000 per second"]
		default_limits=["150 per minute", "8 per second"]
	)
