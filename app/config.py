import os
from typing import override
from dotenv import load_dotenv
from packages.utils.singleton import Singleton
from app.logger import logger


class Config(metaclass=Singleton):
    base_url: str
    api_data_endpoint: str
    username: str
    password: str

    def __init__(
        self,
        base_url: str,
        api_data_endpoint: str,
        username: str,
        password: str,
    ) -> None:
        self.base_url = base_url
        self.api_data_endpoint = api_data_endpoint
        self.username = username
        self.password = password

    @classmethod
    def load(cls):
        _ = load_dotenv()

        required_vars = {
            "base_url": os.getenv("BASE_URL", ""),
            "api_data_endpoint": os.getenv("API_DATA_ENDPOINT", "").lstrip("/"),
            "username": os.getenv("COOPCRM_USERNAME", ""),
            "password": os.getenv("COOPCRM_PASSWORD", ""),
        }

        missing_vars = [
            key.upper() for key, value in required_vars.items() if not value
        ]

        if missing_vars:
            raise ValueError(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

        logger.debug(f"Config loaded: {required_vars}")

        return cls(**required_vars)

    @override
    def __repr__(self) -> str:
        return f"Config(base_url={self.base_url}, api_data_endpoint={self.api_data_endpoint})"
