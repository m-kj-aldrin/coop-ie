from cgitb import html
from html.parser import HTMLParser
import html
import json
import logging

import httpx
from app.config import Config
from packages.crm.api import CrmApi
from packages.crm.auth_async import Authenticate
from packages.crm.odata import OData, compile_odata_params
from packages.crm.protocols import User

logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)

TEAM_ID = "5032CAE1-6394-E711-80F2-3863BB346B18"
COOP_NORRBOTTEN_ID = "7fb8568e-82d1-ee11-9079-6045bd895c47"
PRODUCTION_MACH1_ID = "f7bd5d0e-8460-ee11-8df0-6045bd895243"


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.skip_until_closing_bracket = False

    def handle_data(self, data):
        logging.debug(f"Handling data: {repr(data)}")
        text = data.strip()

        # Check if we should start skipping
        if "[You don't often" in text:
            self.skip_until_closing_bracket = True
            logging.debug("Started skipping until closing bracket")
            return

        # If we're in skip mode and find closing bracket, stop skipping
        if self.skip_until_closing_bracket and "]" in text:
            self.skip_until_closing_bracket = False
            text = text.split("]", 1)[
                1
            ].strip()  # Take only text after the closing bracket
            logging.debug("Found closing bracket, stopped skipping")

        # Skip if we're in skip mode or if it's a comment
        if (
            text
            and not self.skip_until_closing_bracket
            and not text.startswith("<!--")
            and not text.endswith("-->")
        ):
            self.text.append(text)
            logging.debug(f"Added text: {repr(text)}")

    def handle_comment(self, data):
        logging.debug(f"Found comment: {repr(data)}")
        # Skip comments
        pass

    def get_text(self):
        result = " ".join(self.text)
        logging.debug(f"Final text: {repr(result)}")
        return result


def get_text_from_html(html: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


async def setup():
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

    return api


EXCLUDE_STRING = " and ".join(
    f"customerid_contact/contactid ne {id}"
    for id in [COOP_NORRBOTTEN_ID, PRODUCTION_MACH1_ID]
)


async def get_latest_incident_with_contact(api: CrmApi):
    """Fetch the latest incident assigned to the Medlemsservice team with the related contact."""
    params = [
        ("$select", "incidentid,ticketnumber"),
        (
            "$filter",
            f"_owningteam_value eq '{TEAM_ID}' and {EXCLUDE_STRING}",
        ),
        ("$orderby", "createdon desc"),
        ("$top", 2),
        (
            "$expand",
            "customerid_contact($select=contactid,fullname,coop_external_customer_id,coop_personalnumber)",
        ),
    ]
    response = await api.get("incidents", parameters=params)
    data = response.json().get("value", [])
    if not data:
        return None, None
    latest_incident = data[0]
    contact_id = latest_incident.get("customerid_contact", {}).get("contactid")
    return latest_incident, contact_id


async def get_latest_incident_with_contact_2(api: CrmApi):
    """Fetch the latest incident assigned to the Medlemsservice team with the related contact."""
    # print(EXCLUDE_STRING)
    params = [
        ("$select", "incidentid,ticketnumber"),
        (
            "$filter",
            f"_owningteam_value eq '{TEAM_ID}' and {EXCLUDE_STRING}",
        ),
        ("$orderby", "createdon desc"),
        ("$top", 1),
        (
            "$expand",
            "customerid_contact($select=contactid,fullname,coop_external_customer_id,coop_personalnumber)",
        ),
    ]
    response = await api.get("incidents", parameters=params)
    data = response.json().get("value", [])
    if not data:
        return None
    # latest_incident = data[0]
    # contact_id = latest_incident.get("customerid_contact", {}).get("contactid")
    return data


async def get_related_incidents_with_emails(contact_id: str, api: CrmApi):
    """Fetch incidents related to a contact."""
    params = [
        ("$filter", f"customerid_contact/contactid eq '{contact_id}'"),
        ("$select", "incidentid,ticketnumber,title"),
        ("$orderby", "createdon desc"),
        (
            "$expand",
            "Incident_Emails($filter=sender ne 'bekraftelsekundservice@coop.se';$select=subject,description,sender)",
        ),
        ("$top", 16),
    ]
    response = await api.get("incidents", parameters=params)
    # print(response.text)
    data = response.json().get("value", [])
    for incident in data:
        emails = incident.get("Incident_Emails", [])
        for email in emails:
            email["description"] = get_text_from_html(email["description"])
    return data


# async def get_email_messages_by_incident(incident_id: str, api: CrmApi):
#     """Fetch email messages related to an incident."""
#     params = [
#         ("$filter", f"regardingobjectid_incident_email/incidentid eq '{incident_id}'"),
#         ("$select", "subject"),
#         ("$orderby", "createdon desc"),
#     ]
#     response = await api.get("emails", parameters=params)
#     return response.json().get("value", [])


async def main() -> None:
    api = await setup()

    # o_data_params = [
    #     ("$select", "incidentid,ticketnumber"),
    #     (
    #         "$filter",
    #         f"_owningteam_value eq '{TEAM_ID}' and {EXCLUDE_STRING} and statecode eq 0",
    #     ),
    #     ("$top", 1),
    #     ("$orderby", "createdon desc"),
    #     (
    #         "$expand",
    #         "customerid_contact($select=contactid,coop_external_customer_id,fullname),Incident_Emails($filter=sender ne 'bekraftelsekundservice@coop.se';$select=subject,description,sender)",
    #     ),
    # ]
    o_data_params = compile_odata_params(
        OData(
            select=["incidentid", "ticketnumber","description"],
            filter=[
                f"_owningteam_value eq '{TEAM_ID}' and {EXCLUDE_STRING} and statecode eq 0",
            ],
            orderby=["createdon desc"],
            top=1,
            expand=[
                OData(
                    entity="customerid_contact",
                    select=[
                        "contactid",
                        "coop_external_customer_id",
                        "fullname",
                    ],
                ),
                OData(
                    entity="Incident_Emails",
                    select=["subject", "description", "sender"],
                    filter=["sender ne 'bekraftelsekundservice@coop.se'"],
                ),
            ],
        )
    )

    # print(json.dumps(o_data_params, indent=4, ensure_ascii=False))

    response = await api.get(endpoint="incidents", parameters=o_data_params)
    # print(response.text)
    data = response.json()["value"][0]
    # data['description'] = html.unescape(data['description'])
    print(json.dumps(data, indent=4, ensure_ascii=False))

    # print(json.dumps(o_dat_str, indent=4, ensure_ascii=False))

    # incidents = await get_latest_incident_with_contact_2(api=api)

    # print(json.dumps(incidents, indent=4, ensure_ascii=False))

    # for incident in incidents:
    #     contact_id = incident.get("customerid_contact", {}).get("contactid")
    #     # print(contact_id)

    #     related_incidents_emails = await get_related_incidents_with_emails(
    #         contact_id, api=api
    #     )
    #     # print(related_incidents_emails)
    #     # incident["Incident_Emails"] = emails
    #     incident["related_incidents"] = related_incidents_emails

    # print(json.dumps(incidents, indent=4, ensure_ascii=False))

    # # print(json.dumps(related_emails, indent=4, ensure_ascii=False))

    # # start = time.perf_counter()
    # # latest_incident, contact_id = await get_latest_incident_with_contact(api)
    # # end = time.perf_counter()
    # # print(f"get_latest_incident took {end - start:.2f} seconds")
    # # if not latest_incident:
    # #     print("No incidents found for the Medlemsservice team.")
    # #     return

    # # pretty = json.dumps(latest_incident, indent=4, ensure_ascii=False)
    # # print("Latest Incident:\n", pretty)

    # # related_incidents = await get_related_incidents(contact_id, api=api)
    # # related_emails = []
    # # for incident in related_incidents:
    # #     print(f"Processing incident {incident['incidentid']}")
    # #     emails = await get_email_messages_by_incident(incident["incidentid"], api=api)
    # #     related_emails.extend(emails)

    # # pretty = json.dumps(related_incidents, indent=4, ensure_ascii=False)
    # # print(f"Related incidents:\n{pretty}")

    # # data = {
    # #     **latest_incident,
    # #     # "related_incidents": related_incidents,
    # #     # "related_emails": related_emails,
    # # }

    # # pretty = json.dumps(data, indent=4, ensure_ascii=False)
    # # print(f"Data:\n{pretty}")

    # # email_messages = await get_email_messages(contact_id, api=api)
    # # print(f"\nEmail Messages ({len(email_messages)}):")
    # # for email in email_messages:
    # #     print(email)
