import logging
from typing import Any, Literal
from packages.crm.fetch_xml import FetchXML
from packages.crm.protocols import AuthenticateProtocol
from httpx import AsyncClient, RequestError, Headers

logger = logging.getLogger(__name__)


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
        headers: dict[str, str] | Headers = {},
        data: None | dict[str, Any] = None,
    ):
        if not self.authenticator:
            raise ValueError("Authenticator not set")

        if not self.authenticator.is_authenticated:
            if not (await self.authenticator.login()).is_authenticated:
                raise ValueError("Authentication failed")
            self._client.cookies = self.authenticator.cookies_as_tuples()

        # print(f"Requesting {method} {url} with parameters {parameters}")

        return await self._client.request(
            method=method, url=url, params=parameters, data=data, headers=headers
        )

    async def get(self, endpoint: str, parameters: list[tuple[str, Any]]):
        url = f"{self.base_url}/{self.api_data_endpoint}/{endpoint}"

        return await self.request(method="GET", url=url, parameters=parameters)

    async def fetch_xml_request(self, query: FetchXML):
        """Make a FetchXML request to the CRM API

        Args:
            query (FetchXML): The FetchXML query object

        Returns:
            dict: The response from the CRM API
        """
        if not hasattr(query, "entity_name") or not hasattr(query, "get_query"):
            raise ValueError("Query must be a built FetchXML object")

        entity_name = f"{query.entity_name}s"
        xml_query = query.get_query()

        url = f"{self.base_url}/{self.api_data_endpoint}/{entity_name}"

        headers = Headers(
            {
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                "Prefer": "odata.include-annotations=*",
            }
        )

        try:
            response = await self.request(
                method="GET",
                url=url,
                headers=headers,
                parameters=[("fetchXml", xml_query)],
            )

            response_json: dict[str, object] = response.json()

            return FetchXML.parse_response(response_json)
        except RequestError as e:
            error_msg = f"API request failed: {e}"
            logger.error(error_msg)
            raise
