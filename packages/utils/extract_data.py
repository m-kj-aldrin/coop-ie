from pydantic import BaseModel, Field, field_validator
import re
from typing import Any


class ExtractedData(BaseModel):
    Orsak: str = ""
    Personnummer: str
    Ansökningsdatum: str = ""
    Kanal: str = ""
    Butiksnummer: str = ""
    Kvittonummer: str = ""
    Ordernummer: str = ""
    Cas: str = Field(pattern=r"^CAS-.*")  # Enforce pattern at field level
    Epost: str = ""

    @field_validator("Cas")
    @classmethod
    def validate_cas_format(cls, v: Any) -> str:
        """Validate that cas starts with 'cas-'"""
        if not isinstance(v, str) or not v.startswith("CAS-"):
            raise ValueError("cas field must start with 'CAS-'")
        return v


def extract_key_values(text: str, cas: str) -> ExtractedData:
    """
    Extracts specific key-value pairs from the provided text based on predefined key sets
    and returns a validated ExtractedData model.

    Parameters:
        text (str): The multiline text block containing key-value pairs.
        cas (str): The case number to be included in the extracted data. Must start with 'cas-'.

    Returns:
        ExtractedData: A Pydantic model containing the extracted and validated data.

    Raises:
        ValueError: If cas doesn't start with 'cas-' or if required fields are missing.
    """
    # Define the two sets of keys
    first_type_keys = [
        "Error",
        "Pnr",
        "channel",
        "storeId",
        "Time",
        "receiptNumber",
        "id",
    ]
    second_type_keys = [
        "Till kundservice med beskrivning",
        "Personnummer",
        "Kanal",
        "Store id",
        "Ansökningsdatum",
        "Kvittonummer",
        "Id",
        "Epost",
    ]

    # Define the key indicator regex pattern
    key_indicator = "Till kundservice med beskrivning|Tekniskt fel eller fall som inte hanteras med beskrivning"
    indicator_pattern = f"^({key_indicator}): .*"
    indicator_regex = re.compile(indicator_pattern, re.MULTILINE | re.IGNORECASE)

    # Determine which set of keys to use
    use_second_type_keys = bool(indicator_regex.search(text))
    selected_keys = second_type_keys if use_second_type_keys else first_type_keys

    # Extract key-value pairs
    extracted: dict[str, str] = {}
    for key in selected_keys:
        escaped_key = re.escape(key)
        pattern = f"^{escaped_key}:(.*)$"
        regex = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
        match = regex.search(text)
        value = match.group(1).strip() if match else ""
        extracted[key] = value

    # Handle special case for 'Personnummer' in second_type_keys
    if use_second_type_keys and "Personnummer" in selected_keys:
        personnummer = extracted.get("Personnummer", "")
        if personnummer:
            first_two_digits = personnummer[:2]
            if not personnummer.startswith(("19", "20")):
                if "20" <= first_two_digits <= "99":
                    extracted["Personnummer"] = "19" + personnummer
                elif "00" <= first_two_digits <= "20":
                    extracted["Personnummer"] = "20" + personnummer

    # Mapping to standardized headers
    if use_second_type_keys:
        key_mapping = {
            "Till kundservice med beskrivning": "Orsak",
            "Personnummer": "Personnummer",
            "Kanal": "Kanal",
            "Store id": "Butiksnummer",
            "Ansökningsdatum": "Ansökningsdatum",
            "Kvittonummer": "Kvittonummer",
            "Id": "Ordernummer",
            "Epost": "Epost",
        }
    else:
        key_mapping = {
            "Error": "Orsak",
            "Pnr": "Personnummer",
            "channel": "Kanal",
            "storeId": "Butiksnummer",
            "Time": "Ansökningsdatum",
            "receiptNumber": "Kvittonummer",
            "id": "Ordernummer",
        }

    standardized_data = {
        "Orsak": "",
        "Personnummer": "",
        "Kanal": "",
        "Butiksnummer": "",
        "Ansökningsdatum": "",
        "Kvittonummer": "",
        "Ordernummer": "",
        "Epost": "",
        "Cas": cas,
    }

    for original_key, value in extracted.items():
        standardized_key = key_mapping.get(original_key)
        if standardized_key:
            standardized_data[standardized_key] = value

    # Add the cas number to the standardized data
    # standardized_data["Cas"] = cas

    # Create and return the Pydantic model
    return ExtractedData(**standardized_data)
