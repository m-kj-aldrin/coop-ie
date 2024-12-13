import logging
from packages.crm.api import CrmApi
from packages.crm.fetch_xml import Attribute, Filter, FilterCondition, FetchXML

logger = logging.getLogger(__name__)


async def get_notifications_for_inactive_incidents(api: CrmApi):
    fetch = FetchXML.fetch()

    _ = (
        fetch.set_entity(FetchXML.entity("coop_notification"))
        .set_attributes(
            Attribute("statecode"),
            Attribute("coop_name"),
            Attribute("createdon"),
            Attribute("coop_relatedcase"),
            Attribute("coop_notificationsubject"),
            Attribute("coop_knowledgearticleid"),
            Attribute("coop_notificationid"),
        )
        .set_filters(
            Filter(
                [
                    FilterCondition("coop_isread", "eq", "0"),
                    FilterCondition("ownerid", "eq-userid"),
                ],
            ),
        )
        .set_order("coop_name", descending=False)
        .set_links(
            FetchXML.link(
                name="incident",
                from_attribute=Attribute("incidentid"),
                to_attribute=Attribute("coop_relatedcase"),
            )
            .set_attributes(
                Attribute("statuscode"),
                Attribute("ticketnumber"),
                Attribute("statecode"),
                Attribute("incidentid"),
            )
            .set_filters(
                Filter([FilterCondition("statecode", "eq", "1")]),
            )
        )
    )

    fetch.build()

    logger.info("FetchXML: %s", fetch.get_query())

    response = await api.fetch_xml_request(fetch)

    return response


async def active_incidents_for_user(api: CrmApi):
    fetch = FetchXML.fetch()
    _ = fetch.set_entity(
        FetchXML.entity("incident")
        .set_filters(
            Filter(
                [
                    FilterCondition("statecode", "eq", "0"),
                    FilterCondition("ownerid", "eq-userid"),
                ]
            )
        )
        .set_attributes(Attribute("incidentid"), Attribute("ticketnumber"))
        .set_order("createdon", descending=True)
    )

    fetch.build()

    response = await api.fetch_xml_request(fetch)

    return response


async def get_membership_creationfailures(api: CrmApi):
    title = "Membership Creation Failure PRODUCTION"

    fetch = FetchXML.fetch()
    _ = fetch.set_entity(
        FetchXML.entity("incident")
        .set_filters(
            Filter(
                [
                    FilterCondition("title", "eq", title),
                    FilterCondition("statecode", "eq", "0"),
                    FilterCondition("ownerid", "eq", "5032CAE1-6394-E711-80F2-3863BB346B18"),
                    FilterCondition("createdon", "on-or-after", "2014-08-01"),
                ]
            )
        )
        .set_attributes(Attribute("incidentid"), Attribute("ticketnumber"),Attribute("coop_descriptionwithouthtml"))
        .set_order("createdon", descending=True)
    )

    fetch.build()

    response = await api.fetch_xml_request(fetch)

    return response
