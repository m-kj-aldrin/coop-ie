from asyncio import Task, create_task, gather
import json
from typing import Literal

from openpyxl import Workbook
from app.setup import setup
from app.logger import logger
from packages.crm.Query import CRMQuery
from packages.crm.actions import (
    ActionDataResponse,
    close_incident,
    create_member,
    get_customer_by_personal_number,
    CustomerSuccessResponse,
    CustomerEmptyResponse,
)
from packages.crm.models import (
    CreationFailureIncident,
    Incident,
    IncidentData,
    ODataResponse,
    creation_failure,
)
from packages.py_xlsx.core.worksheet import TypedWorkSheet
from packages.utils.extract_data import ExtractedData, extract_key_values

# from packages.crm.actions import (
#     update_incident,
# )
# from packages.crm.models import IncidentData


async def main() -> None:
    try:
        api = await setup()
        q = CRMQuery(api=api)

        mad = await q.call_user_query("incident", "creation_failure")
        parsed = ODataResponse[CreationFailureIncident].model_validate_json(mad.text)

        extracted = [
            (incident, extract_key_values(incident.description, incident.ticketnumber))
            for incident in parsed.value
        ]

        cap = [x for x in extracted if x[1].Kanal == "CAP"]
        # mik = [x for x in extracted if x[1].Kanal == "MIK"]

        # Combine CAP and MIK cases into a single list
        # all_cases = cap + mik  # This will put MIK cases after CAP cases
        all_cases = cap


        user_to_save_to_xlsx: list[Task[ActionDataResponse]] = []
        user_save_task_to_incident = {}

        for incident in all_cases:  # Now iterate over the combined list
            user_task = asyncio.create_task(
                get_customer_by_personal_number(incident[1].Personnummer, api)
            )
            user_save_task_to_incident[user_task] = incident
            user_to_save_to_xlsx.append(user_task)

        users = await asyncio.gather(*user_to_save_to_xlsx)


        # Case 3: Customer does not exist (404)
        # not_found_customers = [
        #     user_save_task_to_incident[user_to_save_to_xlsx[i]]
        #     for i, response in enumerate(users)
        #     if response.customer_not_found()
        # ]

        print(users)

        print("Debug - Raw responses:")
        for i, response in enumerate(users):
            print(f"Response {i}:", response.Response)

        print("Debug - All responses:")
        for i, response in enumerate(users):
            print(f"Response {i}:", {
                "Status": response.ResponseStatus,
                "Type": type(response.Response).__name__,
                "Is customer without membership": response.is_customer_without_membership(),
                "Is paid member": response.is_paid_member(),
                "Is not customer": response.is_not_customer(),
                "Raw Response": response.Response
            })

        # Case 1: Customer exists but hasn't paid
        found_customers_not_paid = [
            user_save_task_to_incident[user_to_save_to_xlsx[i]]
            for i, response in enumerate(users)
            if response.is_customer_without_membership()  # These are the ones we want
        ]

        print(f"\nFound {len(found_customers_not_paid)} customers without membership")



        # Create tasks for member creation
        logger.debug(f"Creating member tasks for {len(found_customers_not_paid)} customers")
        for i, customer in enumerate(found_customers_not_paid):
            logger.debug(
                f"Customer {i+1}: KIM ID {users[i].get_kim_customer_id()}, "
                f"Channel {customer[1].Kanal}, "
                f"Personal number {customer[1].Personnummer}"
            )

        member_tasks = [
            create_task(
                create_member(
                    kim_customer_id=users[i].get_kim_customer_id(),
                    channel=customer[1].Kanal,
                    api=api
                )
            )
            for i, customer in enumerate(found_customers_not_paid)
        ]

        # Log skipped customers
        for i, customer in enumerate(found_customers_not_paid):
            if not isinstance(users[i].Response, CustomerSuccessResponse):
                logger.warning(
                    f"Skipping member creation for {customer[1].Personnummer} - no kimCustomerId available"
                )

        if not member_tasks:
            logger.warning("No valid customers found for member creation")
            return

        # Gather results and handle exceptions
        member_results = await gather(*member_tasks, return_exceptions=True)
        
        # Process results
        for customer, result in zip(found_customers_not_paid, member_results):
            if isinstance(result, Exception):
                logger.error(f"Failed to create member for {customer[1].Personnummer}: {result}")
            else:
                logger.info(f"Successfully created member for {customer[1].Personnummer}")

        # print(found_customers_not_paid)

        # Create workbook and worksheet
        # workbook = Workbook()
        # worksheet = TypedWorkSheet(workbook, ExtractedData)

        # # Add each extracted data to worksheet
        # cases_to_close: list[str] = []
        # for customer in not_found_customers:
        #     print(customer[1])
        #     try:
        #         worksheet.append(customer[1])
        #         cases_to_close.append(customer[0].incidentid)
        #     except Exception as e:
        #         logger.error(f"Failed to append customer to worksheet: {e}")
        #         continue

        # try:
        #     # Save the workbook first
        #     workbook.save("not_found_customers.xlsx")

        #     # Only close cases if save was successful
        #     for incident_id in cases_to_close:
        #         try:
        #             await close_incident(
        #                 incident_id=incident_id,
        #                 api=api,
        #                 subject="Medlemsservice_Manuella_medlemskap",
        #             )
        #         except Exception as e:
        #             logger.error(f"Failed to close incident {incident_id}: {e}")

        # except Exception as e:
        #     logger.error(f"Failed to save workbook: {e}")

        print("Debug - All responses:")
        for i, response in enumerate(users):
            print(f"Response {i}:", {
                "Status": response.ResponseStatus,
                "Type": type(response.Response).__name__,
                "Is customer without membership": response.is_customer_without_membership(),
                "Is paid member": response.is_paid_member(),
                "Is not customer": response.is_not_customer(),
                "Raw Response": response.Response
            })

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
