import json
from pathlib import Path
from typing import TypedDict, List

class UserQuery(TypedDict):
    userqueryid: str
    name: str

def extract_userqueries() -> None:
    # Get paths relative to script location
    script_dir = Path(__file__).parent
    input_file = script_dir.parent / 'userqueries.json'
    output_file = script_dir.parent / 'userqueries_extracted.json'

    # Read the original JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract userqueryid and name pairs
    extracted: List[UserQuery] = []
    for query in data['value']:  # Access the 'value' array in the JSON
        if 'userqueryid' in query and 'name' in query:
            extracted.append({
                'userqueryid': query['userqueryid'],
                'name': query['name']
            })

    # Save to new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(extracted)} userqueries to userqueries_extracted.json")

if __name__ == "__main__":
    extract_userqueries() 