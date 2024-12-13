import logging
import pprint
import asyncio

from httpx import Response
from app.config import Config
from packages.crm.actions import close_incident, close_notification, update_incident
from packages.crm.api import CrmApi

# from packages.crm.auth import Authenticate
from packages.crm.auth_async import Authenticate
from packages.crm.fetch_xml import Attribute, FetchXML, FilterCondition
from packages.crm.fetch_xml_recipes import (
    active_incidents_for_user,
    get_membership_creationfailures,
    get_notifications_for_inactive_incidents,
)
from packages.crm.odata import get_incident
from packages.crm.protocols import User
from packages.data_writer.extract_creationfailure_excel import (
    extract_key_values,
    write_to_excel_append,
)

logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)


async def main() -> None:
    config = Config.load()

    user = User(username=config.username, password=config.password)

    authenticator = await Authenticate(
        login_url=config.base_url, redirect_url=config.base_url
    ).login(user=user)

    api = CrmApi(
        base_url=config.base_url,
        api_data_endpoint=config.api_data_endpoint,
        authenticator=authenticator,
    )

    karl_jan_test3_incident_id = "0b29a215-f8b7-ef11-b8e8-7c1e527527f9"

    response = await get_membership_creationfailures(api=api)

    tasks = []
    for incident in response["value"]:
        extracted = extract_key_values(incident["coop_descriptionwithouthtml"])[0]
        extracted["CAS-nummer"] = incident["ticketnumber"]
        # output_file = "C:\\Users\\marald\\Bravedo\\SC Coop - SC Coop Medlemsservice - SC Coop Medlemsservice\\Kundtjänst\\Register (Excel)\\Medlemskap MAD 2021 NY.xlsx"
        output_file = "C:/Users/marald/Bravedo/SC Coop - SC Coop Medlemsservice - SC Coop Medlemsservice/Kundtjänst/Register (Excel)/Medlemskap MAD 2021 NY.xlsx"
        try:
            write_to_excel_append(output_file, extracted)
            # Only close the incident if writing to Excel was successful
            response = asyncio.create_task(close_incident(incident["incidentid"], api=api))
            tasks.append(response)
        except Exception as e:
            print(f"Failed to write to Excel: {e}. Skipping incident closure.")


    responses = await asyncio.gather(*tasks)

    print(responses)
    # print(response)

    # response = await active_incidents_for_user(api=api)

    # print(response)

    # print(len(response["value"]))

    # tasks = []
    # for incident in response["value"]:
    #     id = incident["incidentid"]
    #     print(id)
    #     task = asyncio.create_task(close_incident(id, api=api))
    #     tasks.append(task)

    # responses = await asyncio.gather(*tasks)

    # print(responses)

    # response = await get_notifications_for_inactive_incidents(api=api)

    # for notificiation in response["value"]:
    #     id = notificiation["coop_notificationid"]
    #     print(id)
    # task = asyncio.create_task(close_notification(id, api=api))
    # tasks.append(task)
    # task = asyncio.create_task(close_incident(notificiation["incident1"]["incidentid"], api=api))
    # tasks.append(task)
    # pass

    # Wait for all tasks to complete
    # responses = await asyncio.gather(*tasks)

    # for response in responses:
    #     print(response)

    # response = await get_incident(incident_id=karl_jan_test3_incident_id, api=api)

    # pprint.pprint(response.json())

    # desc = "BLABLABLA"

    # _ = await update_incident(
    #     incident_id=karl_jan_test3_incident_id,
    #     patch_data={
    #         "description": f'<div class="ck-content" data-wrapper="true" dir="ltr" style="--ck-image-style-spacing: 1.5em; --ck-inline-image-style-spacing: calc(var(--ck-image-style-spacing) / 2); --ck-color-selector-caption-background: hsl(0, 0%, 97%); --ck-color-selector-caption-text: hsl(0, 0%, 20%); font-family: Segoe UI; font-size: 11pt;"><p style="margin: 0;">{desc}</div>'
    #     },
    #     api=api,
    # )

    # _ = await close_incident(incident_id=karl_jan_test3_incident_id, api=api)

    # while True:
    #     y_n = input("Do you want to continue? (y/n): ")
    #     if y_n.lower() == "n":
    #         break

    #     start = time.time()
    #     result = await api.fetch_xml_request(fetch)
    #     print(f"Received {len(result['value'])} incidents")
    #     end = time.time()

    #     print(f"Total time for request: {end - start}")

    #     # dump = json.dumps(result, indent=4, ensure_ascii=False)
    #     # print(dump)
