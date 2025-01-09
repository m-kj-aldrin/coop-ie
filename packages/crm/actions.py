from dataclasses import asdict, dataclass
from typing import Any
from packages.crm.api import CrmApi
from packages.crm.models import IncidentData
from packages.utils.date import coop_date_today
from app.logger import logger
from collections.abc import MutableMapping
from typing import Literal
import json
from packages.crm.types import RecordType, SubjectType, SubjectKeys


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
    resolution: str | None = None,
    subject: SubjectType | None = None,
):
    """Close an incident"""

    patch_data = {
        "coop_resolvedon": coop_date_today(),
        "coop_closecasenotification": False,
    }

    if resolution:
        patch_data["coop_resolution"] = resolution

    # Use update_incident to handle the patch operation and subject logic
    await update_incident(incident_id, patch_data, api, subject)

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
