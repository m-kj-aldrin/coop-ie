from app.setup import setup
from packages.crm.Query import CRMQuery
from app.logger import logger
from packages.crm.actions import close_incident


async def main() -> None:
    try:
        api = await setup()
        q = CRMQuery(api=api)

        response = await close_incident(
            "f769bb6b-c9ab-ef11-b8e8-7c1e5211eb8a",
            api=api,
            title="dbo avslut",
            resolution="ok",
            subject="Medlemsservice_Avslut_dödsbon",
        )

        print(response.text)

        # response = await q.get_incident_by_id("f769bb6b-c9ab-ef11-b8e8-7c1e5211eb8a")

        # if not response:
        #     logger.error("No incidents found")
        #     return

        # print(response.model_dump_json(indent=4))

        # response = await q.get_latest_incident()
        # if not response:
        #     logger.error("No incidents found")
        #     return

        # for incident in response.value:
        #     print(incident.model_dump_json(indent=4))
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
