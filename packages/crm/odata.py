from httpx import Response, head
from packages.crm.api import CrmApi
from packages.crm.api import o_data_headers


o = (
    "incidents(0b29a215-f8b7-ef11-b8e8-7c1e527527f9)"
    "?$select=title,ticketnumber,_customerid_value,coop_hbokfnr,coop_storenumber,"
    "caseorigincode,coop_originatingqueue,casetypecode,coop_newcasenotification,coop_closecasenotification,"
    "coop_handlahemmaordernumber,responseby,_coop_relationproducttocase_value,createdon,coop_resolvedon,"
    "coop_storename,coop_categoryautocomplete,_coop_regardingstoreid_value,coop_alerttrigger,coop_abortallescalations,"
    "description,coop_resolution,coop_kasearchstring,traversedpath,_ownerid_value,coop_reminderrun,coop_newlycreatedfromemail,"
    "routecase,_coop_selectedcategory_value,coop_topparentcategory,_slaid_value,resolveby,_kbarticleid_value,_subjectid_value,"
    "_coop_parentcase_value,followupby,_contractid_value,_contractdetailid_value,prioritycode,_coop_caseteamid_value,statuscode,"
    "incidentid,statecode,entityimage_url,numberofchildincident"
)


async def get_incident(incident_id: str, api: CrmApi):

    select = "title,ticketnumber,description,statuscode"

    response = await api.get(
        endpoint=f"incidents({incident_id})",
        parameters=[("$select", select)],
        headers=o_data_headers,
    )

    return response


q = (
    "GET https://coopcrmprod.crm4.dynamics.com/api/data/v9.0/coop_notifications?"
    "$select=statecode,coop_name,createdon,coop_relatedcase,coop_notificationsubject,coop_knowledgearticleid,coop_notificationid&"
    "$expand=coop_relatedcase($filter=statuscode eq 0)&"
    "$filter=coop_isread eq false&"
    "$orderby=coop_name asc&"
    "$top=8&"
    "$count=true"
)

# <fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false" returntotalrecordcount="true" page="1" count="50" no-lock="false">
#     <entity name="incident">
#         <attribute name="entityimage_url"/>
#         <attribute name="title"/>
#         <attribute name="statecode"/>
#         <attribute name="createdon"/>
#         <order attribute="createdon" descending="true"/>
#         <filter type="and">
#             <condition attribute="coop_caseteamid" operator="ne" uiname="HR_" uitype="team" value="{8E514F58-F272-E911-A84C-000D3A2A75B1}"/>
#         </filter>
#         <attribute name="incidentid"/>
#         <link-entity name="contact" from="contactid" to="customerid" alias="bb">
#             <filter type="and">
#                 <condition attribute="contactid" operator="eq" uitype="contact" value="500a9f4d-c9ab-ef11-b8e8-7c1e5211eb8a"/>
#             </filter>
#         </link-entity>
#     </entity>
# </fetch>


async def get_notifications_for_inactive_incidents(api: CrmApi):
    select = (
        "statecode,coop_name,createdon,coop_notificationsubject,coop_notificationid,coop_relatedcase"
    )
    expand = "incident($filter=statuscode eq 0)"
    # filter = "coop_isread eq false"
    filter = "coop_isread eq false and (Microsoft.Dynamics.CRM.EqualUserId(PropertyName='ownerid') or Microsoft.Dynamics.CRM.EqualUserTeams(PropertyName='ownerid'))"
    order_by = "coop_name asc"
    count = "true"

    response = await api.get(
        endpoint="coop_notifications",
        parameters=[
            ("$select", select),
            # ("$expand", expand),
            ("$filter", filter),
            ("$orderby", order_by),
            ("$count", count),
        ],
        headers=o_data_headers,
    )

    return response
