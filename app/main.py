import logging
from app.config import Config
from packages.crm.actions import close_incident
from packages.crm.api import CrmApi

# from packages.crm.auth import Authenticate
from packages.crm.auth_async import Authenticate
from packages.crm.fetch_xml import Attribute, FetchXML, FilterCondition
from packages.crm.protocols import User

logging.basicConfig(
    level=logging.INFO,
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

    # fetch = FetchXML.fetch(count=1)
    # _ = fetch.set_entity(
    #     FetchXML.entity("incident")
    #     .set_attributes(
    #         Attribute("ticketnumber"),
    #         Attribute("title"),
    #     )
    #     .set_filters(
    #         FilterCondition("ownerid", "eq-userid"),
    #         FilterCondition("statecode", "eq", "0"),
    #         type="and",
    #     )
    #     .set_order("createdon", descending=False)
    # ).set_links(
    #     [
    #         FetchXML.link(
    #             name="contact",
    #             from_attribute=Attribute("contactid"),
    #             to_attribute=Attribute("customerid"),
    #             link_type="inner",
    #             alias="contact",
    #         )
    #         .set_filters(
    #             FilterCondition(
    #                 "contactid", "neq", "7fb8568e-82d1-ee11-9079-6045bd895c47"
    #             ),
    #             # FilterCondition("emailaddress1", "eq", "production@coop-mach1.com"),
    #             type="and",
    #         )
    #         .set_attributes(
    #             Attribute("contactid"),
    #             Attribute("fullname"),
    #             Attribute("emailaddress1"),
    #         )
    #         # .set_links(
    #         #     [
    #         #         FetchXML.link(
    #         #             name="incident",
    #         #             from_attribute=Attribute("customerid"),
    #         #             to_attribute=Attribute("contactid"),
    #         #             link_type="inner",
    #         #         )
    #         #         .set_attributes(
    #         #             Attribute("ticketnumber"),
    #         #             Attribute("title"),
    #         #             Attribute("createdon"),
    #         #         )
    #         #         .set_filters(
    #         #             FilterCondition("createdon", "on-or-after", "2023-10-01"),
    #         #             type="and",
    #         #         )
    #         #         .set_order("createdon", descending=True)
    #         #     ]
    #         # )
    #     ]
    # )

    # # fetch.build()
    # # result = await api.fetch_xml_request(fetch)

    # # print(fetch._xml)

    _ = await close_incident(
        incident_id="0b29a215-f8b7-ef11-b8e8-7c1e527527f9", api=api
    )

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
