import xml.etree.ElementTree as ET

# Path to metadata.xml
metadata_path = "metadata.xml"

# Parse the XML
tree = ET.parse(metadata_path)
root = tree.getroot()

# Namespace for OData metadata
namespace = {
    "edmx": "http://docs.oasis-open.org/odata/ns/edmx",
    "edm": "http://docs.oasis-open.org/odata/ns/edm",
}

# Extract actions
actions = root.findall(".//edm:Action", namespace)
action_details = []

for action in actions:
    action_name = action.get("Name")
    is_bound = action.get("IsBound", "false")

    # Extract parameters
    parameters = [
        {
            "Name": param.get("Name"),
            "Type": param.get("Type"),
            "Nullable": param.get("Nullable"),
            "MaxLength": param.get("MaxLength"),
        }
        for param in action.findall(".//edm:Parameter", namespace)
    ]

    # Extract return type
    return_type = action.find(".//edm:ReturnType", namespace)
    return_type_details = {
        "Type": return_type.get("Type") if return_type is not None else None,
        "Nullable": return_type.get("Nullable") if return_type is not None else None,
    }

    # Add details to list
    action_details.append(
        {
            "Action Name": action_name,
            "Is Bound": is_bound,
            "Parameters": parameters,
            "Return Type": return_type_details,
        }
    )

# Write the results to a file
with open("action_data.txt", "w") as f:
    for action in action_details:
        f.write(f"Action: {action['Action Name']}\n")
        f.write(f"Is Bound: {action['Is Bound']}\n")
        
        f.write("Parameters:\n")
        for param in action['Parameters']:
            f.write(f"  - Name: {param['Name']}\n")
            f.write(f"    Type: {param['Type']}\n")
            if param['Nullable']:
                f.write(f"    Nullable: {param['Nullable']}\n")
            if param['MaxLength']:
                f.write(f"    MaxLength: {param['MaxLength']}\n")
        
        f.write("Return Type:\n")
        f.write(f"  Type: {action['Return Type']['Type']}\n")
        if action['Return Type']['Nullable']:
            f.write(f"  Nullable: {action['Return Type']['Nullable']}\n")
        f.write("\n---\n\n")
