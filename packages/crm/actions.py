from dataclasses import dataclass
import logging
from httpx import Headers
from typing import Any, MutableMapping

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


async def update_incident(
    incident_id: str, patch_data: MutableMapping[str, Any], api: CrmApi
):
    """Update an incident"""

    incident_str = f"incidents({incident_id})"

    headers = Headers(headers=o_data_headers)

    patch_response = await api.patch(
        endpoint=incident_str,
        data=patch_data,
        headers=headers,
    )

    return patch_response


async def close_incident(incident_id: str, api: CrmApi):
    """Close an incident"""

    incident_str = f"incidents({incident_id})"

    headers = Headers(headers=o_data_headers)

    patch_data = {
        "coop_resolvedon": coop_date_today(),
        "coop_closecasenotification": False,
    }

    _ = await api.patch(
        endpoint=incident_str,
        data=patch_data,
        headers=headers,
    )

    action = ActionMap.close_incident(incident_id)

    close_res = await api.post(
        endpoint=action.name,
        data=action.data,
        headers=headers,
    )

    return close_res


async def close_notification(notificiation_id: str, api: CrmApi):
    """Close an incident"""

    notificiation_str = f"coop_notifications({notificiation_id})"

    headers = Headers(headers=o_data_headers)

    patch_data = {
        "coop_isread": "true",
    }

    close_not = await api.patch(
        endpoint=notificiation_str,
        data=patch_data,
        headers=headers,
    )

    return close_not
