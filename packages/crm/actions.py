from dataclasses import dataclass
from typing import Any
from packages.crm.api import CrmApi
from packages.utils.date import coop_date_today
from app.logger import logger
from collections.abc import MutableMapping
from typing import Literal
import json

SubjectType = Literal[
    "Butik",
    "Butik_Bemötande",
    "Butik_CBS-relaterade_frågor",
    "Butik_DDF-relaterade_frågor",
    "Butik_Dubbelreservationer",
    "Butik_Konsumentföreningar",
    "Butik_Kvittofrågor",
    "Butik_Leverantör",
    "Butik_Medlemsrabatter/Förening",
    "Butik_Medlemsskapsfrågor/Förening",
    "Butik_Prisfråga",
    "Butik_Produkt",
    "Butik_ShopExpress",
    "Butik_X:-TRA",
    "Manuella_Medlemskap",
    "Medlemsprogrammet",
    "Medlemsprogrammet_Appen",
    "Medlemsprogrammet_Bedrägeri",
    "Medlemsprogrammet_Coop.se",
    "Medlemsprogrammet_Coop.se/Inloggning",
    "Medlemsprogrammet_Erbjudande_&_reklam",
    "Medlemsprogrammet_Erbjudande_&_reklam_Saknar_DR",
    "Medlemsprogrammet_Erbjudande_&_reklam_Utskick",
    "Medlemsprogrammet_Erbjudande_&_reklam_Vill_INTE_ha_adresserad_DR",
    "Medlemsprogrammet_Erbjudande_&_reklam_Vill_ha_adresserad_DR",
    "Medlemsprogrammet_Ersättningskort",
    "Medlemsprogrammet_Hushållskopplingar/Sammanslagning",
    "Medlemsprogrammet_Hushållskopplingar/Splitt",
    "Medlemsprogrammet_Hushållsskopplingar",
    "Medlemsprogrammet_Hushållsskopplingar/Nytt_hushåll",
    "Medlemsprogrammet_Koppla_kort",
    "Medlemsprogrammet_Koppla_kort/Allmänna_frågor",
    "Medlemsprogrammet_Koppla_kort/Frågeräknaren",
    "Medlemsprogrammet_Koppla_kort/Ta_bort_kort",
    "Medlemsprogrammet_Koppla_kort/Vilka_kort_är_kopplade",
    "Medlemsprogrammet_Kortinformation",
    "Medlemsprogrammet_Kunduppgifter",
    "Medlemsprogrammet_Medlemskapsfrågor",
    "Medlemsprogrammet_Medlemsrabatter",
    "Medlemsprogrammet_Mer_Smak;_Information_&_innehåll",
    "Medlemsprogrammet_Mer_Smak;_Saknar",
    "Medlemsprogrammet_Personliga_erbjudanden",
    "Medlemsprogrammet_Poängexpert",
    "Medlemsprogrammet_Poängfrågor",
    "Medlemsprogrammet_Poängfrågor/Efterregistrering",
    "Medlemsprogrammet_Poängfrågor/Partner",
    "Medlemsprogrammet_Poängfrågor/Poängexpert",
    "Medlemsprogrammet_Poängfrågor/Poängflytt",
    "Medlemsprogrammet_Poängfrågor/Poängförfall",
    "Medlemsprogrammet_Poängfrågor/Ånger_Coop",
    "Medlemsprogrammet_Värdecheckar",
    "Medlemsprogrammet_Ändra_kunduppgifter",
    "Medlemsservice",
    "Medlemsservice_Adressändring",
    "Medlemsservice_Avslut_dödsbon",
    "Medlemsservice_Avslut_och_uttag_",
    "Medlemsservice_Avstämning",
    "Medlemsservice_Bli_medlem",
    "Medlemsservice_Byte_av_konsumentförening",
    "Medlemsservice_Frågor_om_föreningarnas_hemsida",
    "Medlemsservice_GDPR",
    "Medlemsservice_Kapital-_och_räntebesked",
    "Medlemsservice_Konsumentförening",
    "Medlemsservice_Manuella_medlemskap",
    "Medlemsservice_Medlemskap",
    "Medlemsservice_Saldoförfrågan",
    "Medlemsservice_Ägarombud",
    "Medlemsservice_Åter_utbetalning",
    "Medlemsservice_Återbäring",
    "Partnerprogrammet",
    "Partnerprogrammet_Bedrägeri",
    "Partnerprogrammet_Coop.se",
    "Partnerprogrammet_Coop_Mastercard",
    "Partnerprogrammet_Coop_Matkonto",
    "Partnerprogrammet_Efterregistrering",
    "Partnerprogrammet_Erbjudande_&_reklam_Partner",
    "Partnerprogrammet_Erbjudande_&_reklam_Utskick",
    "Partnerprogrammet_Partneruttag",
    "Partnerprogrammet_Poängfrågor/Partner_",
    "Partnerprogrammet_Poängfrågor/Ånger_Partner",
    "Partnerprogrammet_Tjäna_poäng",
    "Paymentsupport",
    "Paymentsupport_Digitala_presentkort",
    "Paymentsupport_Fysiska_presentkort",
    "Paymentsupport_Scan&Pay",
    "Reklamationer",
    "Reklamationer/Främmande_föremål/Glas",
    "Reklamationer/Främmande_föremål/Metall",
    "Reklamationer_Avvikelse_smak,_lukt,_konsistens",
    "Reklamationer_Biverkning_av_kemisk_produkt",
    "Reklamationer_Butik_bäst_före",
    "Reklamationer_Fel_i_tillverkning",
    "Reklamationer_Fel_på_förpackning",
    "Reklamationer_Fel_vikt_eller_mängd",
    "Reklamationer_Felmärkning",
    "Reklamationer_Främmande_föremål",
    "Reklamationer_Färskvarugaranti",
    "Reklamationer_Förekomst_ohyra",
    "Reklamationer_Försäkringsärenden_övrigt",
    "Reklamationer_Misstänkt_matförgiftning_eller_allergisk_reaktion",
    "Reklamationer_Mögel_&_jäst",
    "Reklamationer_Reklamation_bäst_före",
    "Reklamationer_Reklamationsexpert",
    "Reklamationer_Tandskada",
    "Sortiment",
    "Sortiment_Generella_AVM_frågor",
    "Sortiment_Generella_EVM_frågor",
    "Sortiment_Kemikalier",
    "Sortiment_Kvalitet",
    "Sortiment_Produktfråga/Innehåll",
    "Sortiment_Produktfråga/Pris",
    "Sortiment_Produktfråga/Produktförslag",
    "Sortiment_Produktfråga/Produktsynpunkt",
    "Sortiment_Produktfråga/Sortiment",
    "Sortiment_Produktfråga/Ursprung",
    "Tekniska_problem",
    "Tekniska_problem_Appen",
    "Tekniska_problem_Butik",
    "Tekniska_problem_Partners",
    "Tekniska_problem_Poängshoppen",
    "Tekniska_problem_coop.se_hemsidan",
    "Varumärke",
    "Varumärke_Etik_&_omsorg",
    "Varumärke_Hållbarhetsfrågor_",
    "Varumärke_Miljö",
    "Varumärke_Om_Coop_&_KF",
    "Varumärke_Änglamark",
    "Vidarekoppling",
    "Vidarekoppling_Entercard",
    "Vidarekoppling_Inköpstjänst",
    "Vidarekoppling_Kundkontakt",
    "Vidarekoppling_Kundkontakt_",
    "Vidarekoppling_MM_Bank",
    "Vidarekoppling_Medlemsservice",
    "Vidarekoppling_Online",
    "Vidarekoppling_Payex/Matkonto",
    "Vidarekoppling_Payex_&_Matkonto",
    "Vidarekoppling_Poäng",
    "Vidarekoppling_Poäng_",
    "Övrigt",
    "Övrigt_Brev",
    "Övrigt_GDPR",
    "Övrigt_Jobb_&_utbildning",
    "Övrigt_KB-artiklar",
    "Övrigt_Koppla_mail",
    "Övrigt_Medlemspanelen",
    "Övrigt_Personalrabatt",
    "Övrigt_Recept",
    "Övrigt_Reklamspärr",
    "Övrigt_Social_Media",
    "Övrigt_Spam",
    "Övrigt_Sponsring",
    "Övrigt_Övrigt",
]


@dataclass
class Action:
    name: str
    data: dict[str, Any]


class ActionMap:
    """Handles formatting of CRM API action strings"""

    @staticmethod
    def close_incident(incident_id: str) -> Action:
        return Action(
            name="CloseIncident",
            data={
                "IncidentResolution": {
                    "incidentid@odata.bind": f"/incidents({incident_id})"
                },
                "Status": -1,
            },
        )


async def update_incident(
    incident_id: str, 
    patch_data: MutableMapping[str, Any], 
    api: CrmApi,
    subject: SubjectType | None = None
):
    """Update an incident with optional subject"""

    incident_str = f"incidents({incident_id})"

    if subject:
        subject_data = subject_to_subjectid[subject]
        patch_data["subjectid@odata.bind"] = f"/subjects({subject_data['subjectid']})"
        for key, value in subject_data.items():
            if key == "subjectid":
                patch_data["subjectid@odata.bind"] = f"/subjects({value})"
                continue

            patch_data[key] = value

    patch_response = await api.patch(
        endpoint=incident_str,
        data=patch_data,
    )

    _ = patch_response.raise_for_status()

    return patch_response


SubjectKeys = Literal[
    "subjectid",
    "coop_kasearchstring",
    "coop_topparentcategory",
    "coop_categoryautocomplete",
]

# Load subjects from JSON file
with open("app/data/subjects_converted.json", "r", encoding="utf-8") as f:
    subject_to_subjectid: dict[SubjectType,
                               dict[SubjectKeys, str]] = json.load(f)


# packages/crm/actions.py

async def close_incident(
    incident_id: str,
    api: CrmApi,
    resolution: str | None = None,
    subject: SubjectType | None = None,
    title: str | None = None,
):
    """Close an incident"""

    incident_str = f"incidents({incident_id})"

    patch_data = {
        "coop_resolvedon": coop_date_today(),
        "coop_closecasenotification": False,
    }

    if resolution:
        patch_data["coop_resolution"] = resolution
    if subject:
        subject_data = subject_to_subjectid[subject]
        patch_data["subjectid@odata.bind"] = f"/subjects({
            subject_data['subjectid']})"
        for key, value in subject_data.items():
            if key == "subjectid":
                patch_data["subjectid@odata.bind"] = f"/subjects({value})"
                continue

            patch_data[key] = value

    if title:
        patch_data["title"] = title

    logger.debug(f"patch_data: {patch_data}")

    patch_response = await api.patch(
        endpoint=incident_str,
        data=patch_data,
    )

    try:
        patch_response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to patch incident {incident_id}: {e}")
        raise

    action = ActionMap.close_incident(incident_id)

    try:
        close_response = await api.post(
            endpoint=action.name,
            data=action.data,
        )
        close_response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to post close action for incident {
                     incident_id}: {e}")
        raise

    return close_response


async def close_notification(notificiation_id: str, api: CrmApi):
    """Close an incident"""

    notificiation_str = f"coop_notifications({notificiation_id})"

    patch_data = {
        "coop_isread": "true",
    }

    close_notification = await api.patch(
        endpoint=notificiation_str,
        data=patch_data,
    )

    return close_notification
