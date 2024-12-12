import logging
import time
from typing import Any, Literal
from packages.crm.fetch_xml import FetchXML
from packages.crm.protocols import AuthenticateProtocol
from httpx import AsyncClient, RequestError, Headers

logger = logging.getLogger(__name__)


# "Accept": "application/json",
# "Content-Type": "application/json; charset=utf-8",

o_data_headers = Headers(
    {
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Prefer": "odata.include-annotations=*",
    }
)


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
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET",
        parameters: list[tuple[str, Any]] | None = None,
        headers: dict[str, str] | Headers | None = None,
        data: dict[str, Any] | None = None,
    ):

        if not self.authenticator:
            raise ValueError("Authenticator not set")

        try:
            self._client.cookies = (
                await self.authenticator.login()
            ).cookies_as_tuples()

        except Exception as e:
            logger.error(f"Failed to login: {e}")

        if parameters is None:
            parameters = []
        if headers is None:
            headers = {}

        return await self._client.request(
            method=method, url=url, params=parameters, json=data, headers=headers
        )

    async def get(self, endpoint: str, parameters: list[tuple[str, Any]]):
        url = f"{self.base_url}/{self.api_data_endpoint}/{endpoint}"

        return await self.request(method="GET", url=url, parameters=parameters)

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any],
        headers: dict[str, str] | Headers | None = None,
    ):
        url = f"{self.base_url}/{self.api_data_endpoint}/{endpoint}"

        response = await self.request(
            method="PATCH", url=url, data=data, headers=headers
        )

        if response.status_code not in (200, 201, 204):
            raise Exception(
                f"Patch request failed: {response.status_code} {response.text}"
            )

        return response

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any],
        headers: dict[str, str] | Headers | None = None,
    ):
        url = f"{self.base_url}/{self.api_data_endpoint}/{endpoint}"

        respone = await self.request(method="POST", url=url, data=data, headers=headers)

        if respone.status_code not in (200, 201, 204):
            raise Exception(
                f"Post request failed: {respone.status_code} {respone.text}"
            )

        return respone

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
        print(f"url: {url}")

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

            # print(response_json)

            return FetchXML.parse_response(response_json)
        except RequestError as e:
            error_msg = f"API request failed: {e}"
            logger.error(error_msg)
            raise
