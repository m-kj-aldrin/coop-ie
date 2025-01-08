import json
from typing import Any, Literal
import httpx
import asyncio

from app.logger import logger
from packages.crm.auth import Authenticate
from packages.crm.models import User
from app.config import Config


base_url = "https://coopcrmprod.crm4.dynamics.com"
api_endpoint = "/api/data/v9.0/subjects"


params = {
    # "$select": "title,subjectid,_parentsubject_value,coop_kasearchstring,coop_topparentcategory,coop_categoryautocomplete",
    "$filter": (
        "("
        "contains(description, '39188da9-e6c3-e311-83d5-005056865f8d') or "
        "contains(description, '5032cae1-6394-e711-80f2-3863bb346b18') or "
        "contains(description, '4f188da9-e6c3-e311-83d5-005056865f8d') or "
        "contains(description, '053cebb9-1fd1-e711-80f9-3863bb3600d8')"
        ")"
    ),
}

headers = {
    "Content-Type": "application/json; odata.metadata=minimal",
    "OData-Version": "4.0",
    "Prefer": 'odata.include-annotations="OData.Community.Display.V1.FormattedValue"',
}


_ = {
    "coop_kasearchstring": "*_\\_*",
    "coop_topparentcategory": "_",
    "coop_categoryautocomplete": "_\\_*",
}


def convert_subjects(
    data: list[
        dict[
            Literal[
                "title",
                "subjectid",
            ]
            | str,
            str,
        ]
    ],
) -> dict[str, dict[str, str]]:
    """Convert subjects data to simplified format.

    Args:
        data: Raw response data from CRM API

    Returns:
        Dict mapping normalized titles to subject IDs
    """

    subjects: dict[str, dict[str, str]] = {}

    for item in data:
        normalized_title = item["title"].replace("\\", "_").replace(" ", "_")

        top_category = item["title"].split("\\")[0]

        o = subjects.setdefault(normalized_title, {})

        o["subjectid"] = item["subjectid"]
        o["coop_kasearchstring"] = f"*{item['title']}*"
        o["coop_topparentcategory"] = top_category
        o["coop_categoryautocomplete"] = f"{item['title']}"

    return subjects


def generate_subject_literal(subjects: dict[str, dict[str, str]]) -> str:
    """Generate a Literal type string from normalized subject titles.
    
    Args:
        subjects: Dictionary of subjects with normalized titles as keys
        
    Returns:
        A string representation of a Literal type containing all normalized titles
    """
    titles = sorted(subjects.keys())
    literal_items = ',\n    '.join(f'"{title}"' for title in titles)
    return f'Literal[\n    {literal_items}\n]'


async def main():
    async with httpx.AsyncClient() as client:
        user = User(username="marcus.aldrin@coop.se", password="Yq75nmQe&@i@-m'")

        config = Config.load()

        auth = await Authenticate(
            login_url=config.base_url, redirect_url=config.base_url
        ).login(user=user)

        cookies = auth.cookies_as_tuples()

        response = await client.get(
            f"{base_url}{api_endpoint}", headers=headers, params=params, cookies=cookies
        )

        data = response.json()

        if not (data and data["value"]):
            raise Exception("No subjects found")

        # Save raw data
        with open("app/data/subjects.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # Save converted data
        converted = convert_subjects(data["value"])
        with open("app/data/subjects_converted.json", "w", encoding="utf-8") as f:
            json.dump(converted, f, indent=4, ensure_ascii=False)

        print(generate_subject_literal(converted))


if __name__ == "__main__":
    asyncio.run(main())
