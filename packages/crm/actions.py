import json
import logging
from httpx import Headers

from packages.crm.api import CrmApi
from packages.utils.date import coop_date_today

logger = logging.getLogger(__name__)


async def close_incident(incident_id: str, api: CrmApi):
    """Close an incident"""

    incident_str = f"incidents({incident_id})"
    incident_url = f"{api.base_url}/{api.api_data_endpoint}/{incident_str}"

    headers = Headers(
        {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Prefer": "odata.include-annotations=*",
        }
    )

    patch_data = {
        "coop_resolvedon": coop_date_today(),
        "coop_closecasenotification": False,
    }

    logger.debug(f"Patch data: {patch_data}")

    # First request: Update the incident
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

    # Second request: Close the incident
    action_url = f"{api.base_url}/{api.api_data_endpoint}/CloseIncident"

    close_data = {
        "IncidentResolution": {"incidentid@odata.bind": f"/incidents({incident_id})"},
        "Status": -1,
    }

    close_res = await api.request(
        url=action_url,
        method="POST",
        data=json.dumps(close_data),
        headers=headers,
    )

    if close_res.status_code not in (200, 201, 204):
        raise Exception(
            f"Failed to close incident: {close_res.status_code} {close_res.text}"
        )

    return close_res
