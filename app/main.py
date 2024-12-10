import logging
import time
from app.config import Config
from packages.crm.api import CrmApi
from packages.crm.auth import Authenticate
from packages.crm.fetch_xml import FetchXML
from packages.crm.protocols import User

logging.basicConfig(level=logging.INFO)


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

    fetch = FetchXML.fetch(count=10, page=1, returntotalrecordcount=True)

    entity = (
        FetchXML.entity("incident")
        .set_attributes(["ticketnumber", "title", "createdon", "ownerid"])
        .set_filters(
            [
                {"attribute": "ownerid", "operator": "eq-userid"},
                {"attribute": "statecode", "operator": "eq", "value": "0"},
            ],
            filter_type="and",
        )
    )

    contact_link = (
        FetchXML.link(
            name="contact",
            from_attribute="contactid",
            to_attribute="customerid",
            link_type="inner",
            alias="contact",
        )
        .set_order("fullname", descending=False)
        .set_attributes(
            [
                "coop_external_customer_id",
                "contactid",
                "fullname",
                "emailaddress1",
            ]
        )
    )

    related_incidents_link = FetchXML.link(
        name="incident",
        from_attribute="customerid",
        to_attribute="contactid",
        link_type="inner",
        alias="related_incidents",
    ).set_attributes(
        [
            "ticketnumber",
            "title",
            "createdon",
        ]
    )

    _ = contact_link.set_links([related_incidents_link])
    _ = entity.set_links([contact_link])
    _ = fetch.set_entity(entity)

    _ = fetch.build()

    # result = await api.fetch_xml_request(fetch)

    # print(result)

    while True:
        y_n = input("Do you want to continue? (y/n): ")
        if y_n.lower() == "n":
            break

        start = time.time()
        result = await api.fetch_xml_request(fetch)
        end = time.time()

        print(f"Total time for request: {end - start}")

        # print(result)
