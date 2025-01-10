from asyncio import Task, create_task, gather
from openpyxl import Workbook
from typing import Tuple

from app.logger import logger
from packages.crm.Query import CRMQuery
from packages.crm.actions import (
    ActionDataResponse,
    close_incident,
    create_member,
    get_customer_by_personal_number,
    CustomerSuccessResponse,
)
from packages.crm.models import (
    CreationFailureIncident,
    ODataResponse,
)
from packages.py_xlsx.core.worksheet import TypedWorkSheet
from packages.utils.extract_data import ExtractedData, extract_key_values
from packages.crm.api import CrmApi


async def handle_creation_failure(api: CrmApi) -> None:
    """
    Process creation failure incidents by checking customer status and taking appropriate actions.
    """
    try:
        q = CRMQuery(api=api)
        mad = await q.call_user_query("incident", "creation_failure")
        parsed = ODataResponse[CreationFailureIncident].model_validate_json(mad.text)

        extracted: list[Tuple[CreationFailureIncident, ExtractedData]] = [
            (incident, extract_key_values(incident.description, incident.ticketnumber))
            for incident in parsed.value
        ]

        cap: list[Tuple[CreationFailureIncident, ExtractedData]] = [
            x for x in extracted if x[1].Kanal == "CAP"
        ]
        all_cases = cap

        user_to_save_to_xlsx: list[Task[ActionDataResponse]] = []
        user_save_task_to_incident = {}

        for incident in all_cases:
            user_task = create_task(
                get_customer_by_personal_number(incident[1].Personnummer, api)
            )
            user_save_task_to_incident[user_task] = incident
            user_to_save_to_xlsx.append(user_task)

        users = await gather(*user_to_save_to_xlsx)

        # Case 1: Customer exists but hasn't paid
        found_customers_not_paid: list[Tuple[CreationFailureIncident, ExtractedData]] = [
            user_save_task_to_incident[user_to_save_to_xlsx[i]]
            for i, response in enumerate(users)
            if response.is_customer_without_membership()
        ]

        logger.debug(
            f"Creating member tasks for {len(found_customers_not_paid)} customers"
        )
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
                    api=api,
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
                logger.error(
                    f"Failed to create member for {customer[1].Personnummer}: {result}"
                )
            else:
                logger.info(
                    f"Successfully created member for {customer[1].Personnummer}"
                )

        # Handle not found customers
        not_found_customers: list[Tuple[CreationFailureIncident, ExtractedData]] = [
            user_save_task_to_incident[user_to_save_to_xlsx[i]]
            for i, response in enumerate(users)
            if response.is_not_customer()
        ]

        # Create workbook and worksheet
        workbook = Workbook()
        worksheet = TypedWorkSheet(workbook, ExtractedData)

        # Add each extracted data to worksheet
        cases_to_close: list[str] = []
        for customer in not_found_customers:
            try:
                worksheet.append(customer[1])
                cases_to_close.append(customer[0].incidentid)
            except Exception as e:
                logger.error(f"Failed to append customer to worksheet: {e}")
                continue

        try:
            # Save the workbook first
            workbook.save("not_found_customers.xlsx")

            # Create tasks for closing incidents
            close_tasks = [
                create_task(
                    close_incident(
                        incident_id=incident_id,
                        api=api,
                        subject="Medlemsservice_Manuella_medlemskap",
                    )
                )
                for incident_id in cases_to_close
            ]

            # Gather all close tasks
            close_results = await gather(*close_tasks, return_exceptions=True)

            # Process results
            for incident_id, result in zip(cases_to_close, close_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to close incident {incident_id}: {result}")
                else:
                    logger.info(f"Successfully closed incident {incident_id}")

        except Exception as e:
            logger.error(f"Failed to save workbook: {e}")

    except Exception as e:
        logger.error(f"Failed to handle creation failure: {e}")
        raise 