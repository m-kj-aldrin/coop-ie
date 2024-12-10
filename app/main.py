import json
from dataclasses import asdict
from app.config import Config
from packages.crm.api import CrmApi
from packages.crm.auth import Authenticate
from packages.crm.protocols import Cookie, User


async def main() -> None:

    config = Config.load()

    user = User(username=config.username, password=config.password)

    authenticator = await Authenticate(login_url=config.base_url).login(user=user)

    api = CrmApi(
        base_url=config.base_url,
        api_data_endpoint=config.api_data_endpoint,
        authenticator=authenticator,
    )

    result = await api.get("/", [])

    print(result.text)
