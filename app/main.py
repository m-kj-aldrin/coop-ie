import json
from app.setup import setup
from app.logger import logger
from packages.crm.Query import CRMQuery
from packages.crm.models import CreationFailureIncident, Incident, ODataResponse

# from packages.crm.actions import (
#     update_incident,
# )
# from packages.crm.models import IncidentData


async def main() -> None:
    try:
        pass
        api = await setup()
        q = CRMQuery(api=api)

        # response = await update_incident(
        #     incident_id="0B29A215-F8B7-EF11-B8E8-7C1E527527F9",
        #     api=api,
        #     patch_data=IncidentData(
        #         description="Jag vill adress ändra bla bla",
        #         coop_resolution="ny adress",
        #         coop_closecasenotification=True,
        #         subject="Medlemsservice_Adressändring",
        #     ),
        # )

        # print(response.status_code)
        # print(response.text)
        # Simulate an API response as a JSON string
        # api_response_json = """
        # {
        # 	"ticketnumber": "cas-123",
        #     "description": "<p>This is a sample description</p>",
        #     "incidentid": "123"
        # }
        # """

        # # Use model_validate_json to parse and validate the JSON string
        # incident = CreationFailureIncident.model_validate_json(api_response_json)
        # logger.debug(f"Parsed description: {incident.description}")

        mad = await q.call_user_query("incident", "creation_failure")
        # print(mad.text)

        parsed = ODataResponse[CreationFailureIncident].model_validate_json(mad.text)

        print(json.dumps(parsed.value, indent=4))

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
