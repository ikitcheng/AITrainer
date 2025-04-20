from authlib.integrations.flask_client import OAuth
from ..config.settings import settings

class GoogleAuth:
    def __init__(self, app):
        oauth = OAuth(app)
        CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

        self.google = oauth.register(
            name='google',
            server_metadata_url=CONF_URL,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            client_kwargs={'scope': 'openid email profile'}
        )
