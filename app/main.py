import os
from app.config import Config
import json
from app.setup import setup
from app.logger import logger
from app.processes.handle_creation_failure import handle_creation_failure
from packages.agents.categorizer import IncidentCategorizer
from packages.crm.Query import CRMQuery
from packages.crm.models import Incident

# Load configuration and environment variables
# config = Config.load()g

# # Debugging: Check if the API key is loaded
# logger.debug(f"OpenAI API Key: {os.getenv('OPENAI_API_KEY')}")


def empty_categorize_result():
    return {
        "resonemang": "",
        "personer": [],
        "kategorier": [],
        "nasta_steg": ""
    }


async def main() -> None:
    try:
        api = await setup()
        q = CRMQuery(api=api)

        # latest = await q.get_latest_incident(top=10)
        # if latest:
        #     with open("app/data/latest_incidents.json", "w") as f:
        #         logger.debug(f"Latest incidents: {latest}")
        #         json.dump(latest.model_dump(by_alias=False), f, ensure_ascii=False, indent=4)
        #         logger.info("Latest incidents saved to latest_incidents.json")
        # latest = None
        # with open("app/data/latest_incidents.json", "r") as f:
        #     latest = json.load(f)
        #     # logger.debug(f"Loaded latest incidents: {latest}")

        # if latest:
        #     latest = latest["value"]
        #     latest = latest[:1]
        #     # Create the IncidentCategorizer once
        #     categorizer = IncidentCategorizer()
        #     results = []
        #     for _incident in latest:
        #         logger.debug(f"Processing incident: {_incident}")
        #         incident = Incident(**_incident)
        #         # Use model_dump to exclude the nested field
        #         # incident_dict = incident.model_dump(exclude={"contact": {"contactid"}})
        #         # test = json.dumps(incident_dict, ensure_ascii=False)
        #         # logger.debug(f"Processing incident: {test}, type {type(test)}")
        #         logger.debug(f"Processing incident: {incident}")
        #         result = await categorizer.categorize(incident)
        #         # data = result.data.model_dump()

        #     #     # Add the correct_answer key with an empty structure
        #     #     data["correct_answer"] = empty_categorize_result()

        #     #     results.append(data)
        #     #     # print(result.data)

        #     # with open("app/data/results.json", "w") as f:
        #     #     json.dump(results, f, ensure_ascii=False, indent=4)

        #     # Uncomment to print the incidents
        #     # print(latest.value)
        #     # for incident in latest.value:
        #     #     print(incident)
        #     #     print("\n\n")

        # # await handle_creation_failure(api)

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
