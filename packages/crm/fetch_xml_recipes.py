import logging
from re import I
from packages.crm.api import CrmApi
from packages.crm.fetch_xml import Attribute, Entity, FilterCondition, FetchXML

logger = logging.getLogger(__name__)

# get_incident = FetchXML.fetch()
# get_incident.entity("incident").set_attributes(
#     Attribute("ticketnumber"),
#     Attribute("title"),
#     Attribute("description"),
#     Attribute("statuscode"),
# ).set_filters(
#     FilterCondition("incidentid", ""), FilterCondition("statecode", "eq", "0")
# )

# <fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false" returntotalrecordcount="true" page="1" count="8" no-lock="false">
#     <entity name="coop_notification">
#         <attribute name="statecode"/>
#         <attribute name="coop_name"/>
#         <attribute name="createdon"/>
#         <attribute name="coop_relatedcase"/>
#         <attribute name="coop_notificationsubject"/>
#         <order attribute="coop_name" descending="false"/>
#         <filter type="and">
#             <condition attribute="coop_isread" operator="eq" value="0"/>
#             <filter type="or">
#                 <condition attribute="ownerid" operator="eq-userid"/>
#                 <condition attribute="ownerid" operator="eq-userteams"/>
#             </filter>
#         </filter>
#         <attribute name="coop_knowledgearticleid"/>
#         <attribute name="coop_notificationid"/>
#     </entity>
# </fetch>


async def get_notifications_for_inactive_incidents(api: CrmApi):
    fetch = FetchXML.fetch()

    fetch.set_entity(FetchXML.entity("coop_notification")).set_attributes(
        Attribute("statecode"),
        Attribute("coop_name"),
        Attribute("createdon"),
        Attribute("coop_relatedcase"),
        Attribute("coop_notificationsubject"),
        Attribute("coop_knowledgearticleid"),
        Attribute("coop_notificationid"),
    ).set_filters(
        FilterCondition("coop_isread", "eq", "0"),
        FilterCondition(
            "ownerid",
            "eq-userid",
        ),
    ).set_order(
        "coop_name", descending=False
    ).set_links(
        FetchXML.link(
            name="incident",
            from_attribute=Attribute("incidentid"),
            to_attribute=Attribute("coop_relatedcase"),
        )
        .set_attributes(
            Attribute("statuscode"), Attribute("ticketnumber"), Attribute("statecode"),Attribute("incidentid")
        )
        .set_filters(
            FilterCondition("statecode", "eq", "1"),
        )
    )
    # FetchXML.link(
    #     name="contact",
    #     from_attribute=Attribute("contactid"),
    #     to_attribute=Attribute("customerid"),
    #     link_type="inner",
    #     alias="contact",
    # )

    fetch.build()

    # print(f"Xml fetch._xml: {fetch._xml}")
    logger.info("FetchXML: %s", fetch.get_query())

    response = await api.fetch_xml_request(fetch)

    return response
