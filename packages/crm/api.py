from collections.abc import MutableMapping
from typing import Any, Literal

import httpx
from app.constants import USER_AGENT
from app.logger import logger
from packages.crm.auth import Authenticate
from packages.crm.odata import OData, compile_odata_params
from httpx import AsyncClient, QueryParams, Headers
from httpx._types import QueryParamTypes


class CrmApi:
    base_url: str
    api_data_endpoint: str
    authenticator: Authenticate
    _client: AsyncClient

    def __init__(
        self,
        base_url: str,
        api_data_endpoint: str,
        authenticator: Authenticate,
    ) -> None:
        self.base_url = base_url
        self.api_data_endpoint = api_data_endpoint
        self.authenticator = authenticator

        self._client = AsyncClient(
            cookies=self.authenticator.cookies_as_tuples(),
            headers={
                "User-Agent": USER_AGENT,
                "OData-MaxVersion": "4.0",
                "OData-Version": "4.0",
                "Prefer": "odata.include-annotations=OData.Community.Display.V1.FormattedValue",
            },
        )

    async def _ensure_authenticated(self) -> None:
        """Ensure we have valid authentication before making requests."""
        try:
            if not self.authenticator.is_authenticated:
                logger.info("Authentication expired, refreshing...")
                self._client.cookies = (
                    await self.authenticator.login()
                ).cookies_as_tuples()
        except Exception as e:
            logger.error(f"Authentication refresh failed: {e}")
            raise

    async def request(
        self,
        path: str,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET",
        parameters: QueryParamTypes | None = None,
        headers: MutableMapping[str, str] | Headers | None = None,
        data: MutableMapping[str, Any] | None = None,
    ) -> httpx.Response:
        """
        Makes an HTTP request to the CRM API.

        Args:
            path (str): The API endpoint path.
            method (Literal["GET", "POST", "PUT", "DELETE", "PATCH"]): The HTTP method.
            parameters (QueryParamTypes | None): Query parameters.
            headers (MutableMapping[str, str] | Headers | None): HTTP headers.
            data (MutableMapping[str, Any] | None): The request payload.

        Returns:
            httpx.Response: The HTTP response.
        """
        try:
            await self._ensure_authenticated()

            if parameters is None:
                parameters = QueryParams()

            url = f"{self.base_url}/{path}"

            response = await self._client.request(
                method=method,
                url=url,
                params=parameters,
                headers=headers,
                json=data,
            )

            _ = response.raise_for_status()

            return response

        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise

    async def get(
        self,
        endpoint: str,
        parameters: QueryParamTypes,
    ):
        url = f"{self.api_data_endpoint}/{endpoint}"

        return await self.request(method="GET", path=url, parameters=parameters)

    async def patch(
        self,
        endpoint: str,
        data: MutableMapping[str, Any],
    ):
        path = f"{self.api_data_endpoint}/{endpoint}"

        response = await self.request(
            method="PATCH",
            path=path,
            data=data,
            headers={"mscrm.suppressduplicatedetection": "false"},
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
        path = f"{self.api_data_endpoint}/{endpoint}"

        response = await self.request(
            method="POST", path=path, data=data, headers=headers
        )

        if response.status_code not in (200, 201, 204):
            raise Exception(
                f"Post request failed: {response.status_code} {response.text}"
            )

        return response

    async def OData_request(
        self,
        odata: OData,
    ):
        """Make an OData request to the CRM API."""
        try:
            params = compile_odata_params(odata)

            endpoint = odata.entity

            if odata.id:
                endpoint = f"{endpoint}s({odata.id})"

            return await self.get(endpoint=endpoint, parameters=params)
        except Exception as e:
            logger.error(f"OData request failed: {e}")
            raise
