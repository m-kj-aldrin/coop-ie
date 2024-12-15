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

# Extract first 4 functions
functions = root.findall(".//edm:Function", namespace)
first_four_functions = []

for function in functions:
    function_name = function.get("Name")
    is_bound = function.get("IsBound", "false")

    # Extract parameters
    parameters = [
        {
            "Name": param.get("Name"),
            "Type": param.get("Type"),
            "Nullable": param.get("Nullable"),
            "MaxLength": param.get("MaxLength"),
        }
        for param in function.findall(".//edm:Parameter", namespace)
    ]

    # Extract return type
    return_type = function.find(".//edm:ReturnType", namespace)
    return_type_details = {
        "Type": return_type.get("Type") if return_type is not None else None,
        "Nullable": return_type.get("Nullable") if return_type is not None else None,
    }

    # Add details to list
    first_four_functions.append(
        {
            "Function Name": function_name,
            "Is Bound": is_bound,
            "Parameters": parameters,
            "Return Type": return_type_details,
        }
    )

# Print the result
data = ""
for func in first_four_functions:
    data += f"Function Name: {func['Function Name']}\n"
    data += f"Is Bound: {func['Is Bound']}\n"
    data += "Parameters:\n"
    for param in func["Parameters"]:
        data += f"  - {param['Name']} ({param['Type']}) Nullable: {param['Nullable']}, MaxLength: {param['MaxLength']}\n"
    data += "Return Type:\n"
    data += f"  Type: {func['Return Type']['Type']} Nullable: {func['Return Type']['Nullable']}\n"
    data += "\n"

with open("function_data.txt", "w") as file:
    file.write(data)
