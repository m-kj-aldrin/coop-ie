import json
import logging
import time
from app.config import Config
from packages.crm.api import CrmApi
from packages.crm.auth import Authenticate
from packages.crm.fetch_xml import Attribute, FetchXML, FilterCondition
from packages.crm.protocols import User

# logging.basicConfig(level=logging.ERROR)


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
        .set_attributes(
            Attribute("ticketnumber"),
            Attribute("title"),
            Attribute("createdon"),
            Attribute("ownerid"),
        )
        .set_filters(
            FilterCondition("ownerid", "eq-userid"),
            FilterCondition("statecode", "eq", "0"),
            type="and",
        )
    )

    contact_link = (
        FetchXML.link(
            name="contact",
            from_attribute=Attribute("contactid"),
            to_attribute=Attribute("customerid"),
            link_type="inner",
            alias="contact",
        )
        .set_order("fullname", descending=False)
        .set_attributes(
            Attribute("coop_external_customer_id"),
            Attribute("contactid"),
            Attribute("fullname"),
            Attribute("emailaddress1"),
        )
    )

    related_incidents_link = FetchXML.link(
        name="incident",
        from_attribute=Attribute("customerid"),
        to_attribute=Attribute("contactid"),
        link_type="inner",
        alias="related_incidents",
    ).set_attributes(
        Attribute("ticketnumber"),
        Attribute("title"),
        Attribute("createdon"),
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

        dump = json.dumps(result, indent=4)
        print(dump)
