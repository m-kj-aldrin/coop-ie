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
