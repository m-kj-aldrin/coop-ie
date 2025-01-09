from typing import Literal
from pydantic import ValidationError
from app.constants import EXCLUDE_STRING, MEDLEMSSERVICE_ID
from packages.crm.api import CrmApi
from packages.crm.models import Incident, ODataResponse
from packages.crm.odata import OData
from app.logger import logger
from packages.crm.types import RecordType


UserQueries = Literal["creation_failure"]
UserQueriesMap: dict[UserQueries, str] = {
    "creation_failure": "da849467-9cce-ef11-b8e8-7c1e524eb8eb"
}


class CRMQuery:
    _api: CrmApi


    def __init__(self, api: CrmApi):
        self._api = api

    async def call_user_query(self, entity: RecordType, userquery: UserQueries):
        query = UserQueriesMap[userquery]
        endpoint = f"{entity}s"

        response = await self._api.get(endpoint, parameters=[("userQuery", query)])
        return response

    async def get_latest_incident(self):
        odata = OData(
            entity="incident",
            select=["title", "incidentid", "ticketnumber", "description"],
            filter=[
                f"_owningteam_value eq '{MEDLEMSSERVICE_ID}' and {EXCLUDE_STRING} and statecode eq 0",
            ],
            orderby=["createdon desc"],
            top=4,
            expand=[
                OData(
                    entity="customerid_contact",
                    select=[
                        "contactid",
                        "coop_external_customer_id",
                        "fullname",
                        "emailaddress1",
                    ],
                ),
            ],
        )

        response = await self._api.OData_request(odata=odata)

        text = response.text

        try:
            return ODataResponse[Incident].model_validate_json(text)
        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            return None

    async def get_incident_by_id(self, incident_id: str):
        odata = OData(
            entity="incident",
            id=incident_id,
            select=[
                "title",
                "incidentid",
                "ticketnumber",
                "description",
                "_subjectid_value",
            ],
            # expand=[
            #     OData(
            #         entity="customerid_contact",
            #         select=[
            #             "contactid",
            #             "coop_external_customer_id",
            #             "fullname",
            #             "emailaddress1",
            #         ],
            #     ),
            # ],
        )

        response = await self._api.OData_request(odata=odata)

        text = response.text

        logger.debug(f"Response text: {text}")

        try:
            return Incident.model_validate_json(text)
        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            return None
