from typing import Any, Literal
from packages.crm.protocols import AuthenticateProtocol
from httpx import AsyncClient, Response


class CrmApi:
    base_url: str
    api_data_endpoint: str
    authenticator: AuthenticateProtocol
    _client: AsyncClient

    def __init__(
        self,
        base_url: str,
        api_data_endpoint: str,
        authenticator: AuthenticateProtocol,
    ) -> None:
        self.base_url = base_url
        self.api_data_endpoint = api_data_endpoint
        self.authenticator = authenticator

        self._client = AsyncClient(cookies=self.authenticator.cookies_as_tuples())

    async def request(
        self,
        url: str,
        method: Literal["GET", "POST", "PUT", "DELETE"] = "GET",
        parameters: list[tuple[str, Any]] = [],
        data: Any = None,
    ):
        if not self.authenticator:
            raise ValueError("Authenticator not set")

        if not self.authenticator.is_authenticated:
            if not self.authenticator.login().is_authenticated:
                raise ValueError("Authentication failed")
            self._client.cookies = self.authenticator.cookies_as_tuples()

        return await self._client.request(
            method=method, url=url, params=parameters, data=data
        )

    async def get(self, endpoint: str, parameters: list[tuple[str, Any]]):
        url = f"{self.base_url}/{self.api_data_endpoint}/{endpoint}"

        return await self.request(method="GET", url=url, parameters=parameters)
