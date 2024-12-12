from dataclasses import dataclass
import logging
from httpx import Headers
from typing import Any

from packages.crm.api import CrmApi
from packages.utils.date import coop_date_today
from packages.crm.api import o_data_headers

logger = logging.getLogger(__name__)


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


async def close_incident(incident_id: str, api: CrmApi):
    """Close an incident"""

    incident_str = f"incidents({incident_id})"
    incident_url = f"{api.base_url}/{api.api_data_endpoint}/{incident_str}"

    headers = Headers(headers=o_data_headers)

    patch_data = {
        "coop_resolvedon": coop_date_today(),
        "coop_closecasenotification": False,
    }

    logger.debug(f"Patch data: {patch_data}")

    patch_res = await api.request(
        url=incident_url,
        method="PATCH",
        data=patch_data,
        headers=headers,
    )

    if patch_res.status_code not in (200, 201, 204):
        raise Exception(
            f"Failed to update incident: {patch_res.status_code} {patch_res.text}"
        )

    action = ActionMap.close_incident(incident_id)

    action_url = f"{api.base_url}/{api.api_data_endpoint}/{action.name}"

    logger.debug(f"Action URL: {action_url}")

    close_res = await api.request(
        url=action_url,
        method="POST",
        data=action.data,
        headers=headers,
    )

    if close_res.status_code not in (200, 201, 204):
        raise Exception(
            f"Failed to close incident: {close_res.status_code} {close_res.text}"
        )

    return close_res
