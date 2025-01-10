from dataclasses import asdict, dataclass
from typing import Any, List, Literal, Union
from packages.crm.api import CrmApi
from packages.crm.models import IncidentData
from packages.utils.date import coop_date_today
from app.logger import logger
from collections.abc import MutableMapping
from typing import Literal
import json
from packages.crm.types import RecordType, SubjectType, SubjectKeys
from pydantic import BaseModel
from datetime import datetime
from typing import List
import httpx
import asyncio


@dataclass
class Action:
    name: str
    data: dict[str, Any]


class ActionMap:
    """Handles formatting of CRM API action strings"""

    @staticmethod
    def close_incident(incident_id: str) -> Action:
        return Action(
            name="CloseIncident",
            data={
                "IncidentResolution": {
                    "incidentid@odata.bind": f"/incidents({incident_id})"
                },
                "Status": -1,
            },
        )


# {
#   "Payload": "{\"date\":\"2025-01-10\",\"depositAmount\":100,\"kimCustomerId\":30001911431,\"entryCode\":\"BUTPG\",\"channel\":\"CAP\",\"associationId\":\"5fa45f7dfc2d0f4641f54cb3\",\"creationType\":\"CreateMembershipWithKimCustomerId\",\"storeId\":\"\",\"receiptNumber\":\"\",\"preventHouseholdCreation\":false}",
#   "RelativeUrl": "memberships",
#   "Method": "POST"
# }

assication_id_map = {
    "östra": "5fa45f7dfc2d0f4641f54cb3",
}


def create_member_payload(kim_customer_id: str, channel: str) -> dict[str, Any]:
    """
    Create the payload for member creation request.

    Args:
        kim_customer_id: The KIM customer ID
        channel: The channel through which the membership is being created

    Returns:
        Dictionary containing the properly formatted payload
    """
    payload_data = {
        "date": coop_date_today(),
        "depositAmount": 100,
        "kimCustomerId": kim_customer_id,
        "entryCode": "BUTPG",
        "channel": channel,
        "associationId": assication_id_map["östra"],
        "creationType": "CreateMembershipWithKimCustomerId",
        "storeId": "",
        "receiptNumber": "",
        "preventHouseholdCreation": False,
    }

    payload = {
        "Payload": json.dumps(payload_data),
        "RelativeUrl": "memberships",
        "Method": "POST",
    }

    logger.debug(f"Creating member payload: {json.dumps(payload, indent=2)}")
    return payload


def case_description_wrapper(description: str):
    return f'<div class="ck-content" data-wrapper="true" dir="ltr" style="--ck-image-style-spacing: 1.5em; --ck-inline-image-style-spacing: calc(var(--ck-image-style-spacing) / 2); --ck-color-selector-caption-background: hsl(0, 0%, 97%); --ck-color-selector-caption-text: hsl(0, 0%, 20%); font-family: Segoe UI; font-size: 11pt;"><p style="margin: 0;">{description}</p></div>'


IncidentPatchDataType = MutableMapping[str, Any]


async def update_incident(
    incident_id: str,
    patch_data: IncidentData,
    api: CrmApi,
    # subject: SubjectType | None = None,
):
    """Update an incident with optional subject"""

    if patch_data.description:
        patch_data.description = case_description_wrapper(patch_data.description)

    _patch_data = {k: v for k, v in asdict(patch_data).items() if v is not None}

    if patch_data.subject:
        subject_data = subject_to_subjectid[patch_data.subject]
        for key, value in subject_data.items():
            if key == "subjectid":
                _patch_data["subjectid@odata.bind"] = f"/subjects({value})"
                del _patch_data["subject"]
                continue
            _patch_data[key] = value

    return await update_record(incident_id, "incident", _patch_data, api)


async def close_incident(
    incident_id: str,
    api: CrmApi,
    subject: SubjectType | None = None,
):
    """Close an incident"""

    patch_data: IncidentData = IncidentData(
        coop_resolvedon=coop_date_today(),
        coop_closecasenotification=False,
        subject=subject,
    )

    # if resolution:
    #     patch_data["coop_resolution"] = resolution

    # Use update_incident to handle the patch operation and subject logic
    await update_incident(incident_id, patch_data, api)

    action = ActionMap.close_incident(incident_id)

    try:
        close_response = await api.post(
            endpoint=action.name,
            data=action.data,
        )
        close_response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to post close action for incident {incident_id}: {e}")
        raise

    return close_response


async def close_notification(notification_id: str, api: CrmApi):
    """Close a notification"""

    patch_data = {
        "coop_isread": "true",
    }

    return await update_record(notification_id, "coop_notifications", patch_data, api)


async def update_record(
    record_id: str,
    record_type: RecordType,
    record_data: MutableMapping[str, Any],
    api: CrmApi,
):
    """Update a record"""

    record_str = f"{record_type}s({record_id})"

    logger.debug(f"record_data: {record_data}")

    patch_response = await api.patch(
        endpoint=record_str,
        data=record_data,
    )

    try:
        patch_response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to patch record {record_id}: {e}")
        raise

    return patch_response


# Load subjects from JSON file
with open("app/data/subjects_converted.json", "r", encoding="utf-8") as f:
    subject_to_subjectid: dict[SubjectType, dict[SubjectKeys, str]] = json.load(f)


class ActionDataPayload(BaseModel):
    RelativeUrl: str


class CustomerAddress(BaseModel):
    type: str
    careOf: str | None
    addressRow1: str
    city: str
    countryCode: str
    physicalAddressType: str | None
    flags: List[str]
    addressId: int
    zipCode: str
    typeOfAddress: str


class CustomerSuccessResponse(BaseModel):
    type: Literal["physical-person"]  # This acts as a discriminator
    status: str
    personalIdNumber: str
    firstName: str
    lastName: str
    birthDate: str
    name: str
    addresses: list[CustomerAddress]
    kimCustomerId: int
    role: str
    email: str


class CustomerErrorResponse(BaseModel):
    status: int
    error: str
    message: str
    path: str
    timestamp: str


class ActionDataResponse(BaseModel):
    ResponseStatus: int
    Response: Union[CustomerSuccessResponse, CustomerErrorResponse]

    model_config = {
        "json_schema_extra": {
            "discriminator": {
                "property_name": "type",
                "mapping": {
                    "physical-person": CustomerSuccessResponse,
                },
            }
        }
    }

    def is_customer_without_membership(self) -> bool:
        """Case 1: Customer exists but has no membership (status 200, CustomerSuccessResponse with no mmId)"""
        print(f"\nDEBUG - is_customer_without_membership check:")
        print(f"Response type: {type(self.Response)}")
        print(f"Response data: {self.Response}")
        return (
            self.ResponseStatus == 200
            and isinstance(self.Response, CustomerSuccessResponse)
            and not hasattr(self.Response, "mmId")
        )

    def is_paid_member(self) -> bool:
        """Case 2: Customer exists and has paid (status 200, CustomerSuccessResponse with mmId)"""
        return (
            self.ResponseStatus == 200
            and isinstance(self.Response, CustomerSuccessResponse)
            and hasattr(self.Response, "mmId")
        )

    def is_not_customer(self) -> bool:
        """Case 3: Not a customer (status 404 or CustomerErrorResponse)"""
        return self.ResponseStatus == 404 or isinstance(
            self.Response, CustomerErrorResponse
        )

    def get_kim_customer_id(self) -> int:
        """Get KIM ID for existing customers (Cases 1 & 2)"""
        print(f"\nDEBUG - get_kim_customer_id:")
        print(f"Response type: {type(self.Response)}")
        print(f"Response: {self.Response}")
        print(
            f"Is CustomerSuccessResponse: {isinstance(self.Response, CustomerSuccessResponse)}"
        )
        print(
            f"Response dict: {self.Response.model_dump() if hasattr(self.Response, 'model_dump') else 'No model_dump'}"
        )

        if isinstance(self.Response, CustomerSuccessResponse):
            return self.Response.kimCustomerId
        raise ValueError("No customer found")


async def get_customer_by_personal_number(
    personal_number: str,
    api: CrmApi,
) -> ActionDataResponse:
    """
    Query customer data using personal number through the coop_ActionDataFunction endpoint.

    Args:
        personal_number: Swedish personal number in format YYYYMMDDXXXX
        api: CrmApi instance

    Returns:
        ActionDataResponse with one of three possible Response types:
        - CustomerSuccessResponse: Customer exists and has paid membership
        - CustomerEmptyResponse: Customer exists but hasn't paid membership
        - CustomerErrorResponse: Customer doesn't exist (404)
    """
    payload = ActionDataPayload(
        RelativeUrl=f"customers/personalnumber/{personal_number}"
    )

    response = await api.request(
        path="/api/data/v9.1/coop_ActionDataFunction",
        method="POST",
        data=payload.model_dump(),
    )

    response.raise_for_status()
    raw_response = response.json()

    print(f"\nDEBUG - Initial API Response for {personal_number}:")
    print(json.dumps(raw_response, indent=2))

    # Parse the Response field which is always a JSON string
    response_data = json.loads(raw_response["Response"])

    print("\nDEBUG - Parsed Response data:")
    print(json.dumps(response_data, indent=2))

    # If it's a 404, it should be mapped to CustomerErrorResponse
    if raw_response["ResponseStatus"] == 404:
        raw_response["Response"] = response_data  # Already parsed error response
        print("\nDEBUG - Mapped to CustomerErrorResponse")
    else:
        # For 200 responses, we need to determine if it's a success or empty response
        if isinstance(response_data, dict) and "kimCustomerId" in response_data:
            print("\nDEBUG - Response data type before mapping:", type(response_data))
            print("DEBUG - Response data before mapping:", response_data)
            raw_response["Response"] = response_data  # CustomerSuccessResponse
            print("\nDEBUG - Mapped to CustomerSuccessResponse")
            print(
                "DEBUG - Response type after mapping:", type(raw_response["Response"])
            )
        else:
            raw_response["Response"] = {"items": []}  # CustomerEmptyResponse
            print("\nDEBUG - Mapped to CustomerEmptyResponse")

    print("\nDEBUG - Final data being sent to ActionDataResponse:")
    print(json.dumps(raw_response, indent=2))

    result = ActionDataResponse.model_validate(raw_response)
    print("\nDEBUG - After Pydantic validation:")
    print(f"Response discriminator type: {type(result.Response)}")
    print(f"Response data: {result.Response}")
    print(f"Raw dict: {result.model_dump()}")

    return result


async def create_member(
    kim_customer_id: int,
    channel: str,
    api: CrmApi,
) -> dict[str, Any]:
    """
    Create a new member using the coop_ActionDataFunction endpoint.

    Args:
        kim_customer_id: The KIM customer ID from CustomerSuccessResponse
        channel: The channel through which the membership is being created
        api: CrmApi instance for making the request

    Returns:
        The parsed JSON response from the API

    Raises:
        HTTPError: If the request fails
        ValueError: If response status is not 201
    """
    payload = create_member_payload(str(kim_customer_id), channel)

    logger.debug(
        f"Sending create member request for KIM ID {kim_customer_id}, channel {channel}"
    )

    response = await api.request(
        path="/api/data/v9.1/coop_ActionDataFunction",
        method="POST",
        data=payload,
    )

    try:
        response.raise_for_status()
        response_data = response.json()

        # Check for specific success status code
        if response.status_code != 201:
            error_msg = f"Failed to create member - expected status 201, got {response.status_code}"
            logger.error(f"{error_msg}. Response: {response_data}")
            raise ValueError(error_msg)

        return response_data

    except Exception as e:
        logger.error(f"Failed to create member for KIM ID {kim_customer_id}: {e}")
        raise
