from app.setup import setup
from app.logger import logger
from app.processes.handle_creation_failure import handle_creation_failure
from packages.crm.Query import CRMQuery


async def main() -> None:
    try:
        api = await setup()
        q = CRMQuery(api=api)

        latest = await q.get_latest_incident()

        if latest:
            # print(latest.value)
            for incident in latest.value:
                print(incident)
                print("\n\n")

        # await handle_creation_failure(api)

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
