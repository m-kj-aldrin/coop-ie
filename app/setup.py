from app.config import Config
from packages.crm.api import CrmApi
from packages.crm.auth import Authenticate
from packages.crm.models import User
from app.logger import logger


async def setup():
    try:
        config = Config.load()

        user = User(username=config.username, password=config.password)

        authenticator = await Authenticate(
            login_url=config.base_url, redirect_url=config.base_url
        ).login(user=user)

        if not authenticator.is_authenticated:
            raise Exception("Failed to authenticate user")

        api = CrmApi(
            base_url=config.base_url,
            api_data_endpoint=config.api_data_endpoint,
            authenticator=authenticator,
        )

        logger.info(f"Setup successful")
        return api
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise
