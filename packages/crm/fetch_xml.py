import logging
from typing import Literal


# Configure logging
logger = logging.getLogger(__name__)


class Entity:
    """Base class for both main entity and linked entities"""

    name: str
    attributes: list[str]
    filters: list[dict[Literal["type", "conditions"], Literal["and", "or"] | list[dict[Literal["attribute", "operator", "value"], str]]]]
    links: list["LinkedEntity"]
    orders: list[dict[str, str]]

    def __init__(self, name):
        self.name = name
        self.attributes = []
        self.filters = []
        self.links = []
        self.orders = []

    def set_attributes(self, attributes: list[str]):
        """Set attributes to fetch from the entity"""
        self.attributes = attributes
        return self

    def set_filters(
        self,
        conditions: list[dict[Literal["attribute", "operator", "value"], str]],
        filter_type: Literal["and", "or"] = "and",
    ):
        """Set filter conditions for the entity"""
        self.filters = [{"type": filter_type, "conditions": conditions}]
        return self

    def set_links(self, links: list["LinkedEntity"]):
        """Set linked entities"""
        self.links = links
        return self

    def set_order(
        self, attribute: str, descending: bool = False, entityname: str | None = None
    ):
        """Set order attribute

        Args:
            attribute: The attribute to order by
            descending: Whether to order in descending order
            entityname: Optional entity name for linked entity ordering
        """
        self.orders = [
            {"attribute": attribute, "descending": descending, "entityname": entityname}
        ]
        return self

    def _build_attributes_xml(self, indent: int = 2):
        """Build XML for attributes"""
        spaces = " " * indent
        xml = [f'{spaces}<attribute name="{attr}" />' for attr in self.attributes]
        return "\n".join(xml)

    def _build_filters_xml(self, indent: int = 2):
        """Build XML for filters"""
        xml = []
        for filter_data in self.filters:
            xml.append(self._build_filter_xml(filter_data, indent))
        return "\n".join(xml)

    def _build_filter_xml(self, filter_data, indent=2):
        """Build XML for a single filter"""
        spaces = " " * indent
        xml = [f'{spaces}<filter type="{filter_data["type"]}">']

        for condition in filter_data["conditions"]:
            condition_xml = [
                f'{spaces}  <condition attribute="{condition["attribute"]}"'
            ]

            if "operator" in condition:
                condition_xml.append(f' operator="{condition["operator"]}"')
            if "value" in condition:
                condition_xml.append(f' value="{condition["value"]}"')

            condition_xml.append(" />")
            xml.append("".join(condition_xml))

        xml.append(f"{spaces}</filter>")
        return "\n".join(xml)

    def _build_orders_xml(self, indent=2):
        """Build XML for order attributes"""
        if not self.orders:
            return ""
        spaces = " " * indent
        xml_lines = []
        for order in self.orders:
            xml_line = f'{spaces}<order attribute="{order["attribute"]}"'
            if order.get("entityname"):
                xml_line += f' entityname="{order["entityname"]}"'
            xml_line += f' descending="{str(order["descending"]).lower()}" />'
            xml_lines.append(xml_line)
        return "\n".join(xml_lines)


class LinkedEntity(Entity):
    """Represents a linked entity in FetchXML"""

    def __init__(
        self, name, from_attribute, to_attribute, link_type="inner", alias: str | None = None
    ):
        super().__init__(name)
        self.from_attribute = from_attribute
        self.to_attribute = to_attribute
        self.link_type = link_type
        self.alias = alias

    def build_xml(self, indent=2):
        """Build XML for this linked entity"""
        spaces = " " * indent
        xml = [
            f'{spaces}<link-entity name="{self.name}" '
            f'from="{self.from_attribute}" '
            f'to="{self.to_attribute}" '
            f'link-type="{self.link_type}"'
        ]

        if self.alias:
            xml.append(f' alias="{self.alias}"')
        xml.append(">")

        # Add attributes
        if self.attributes:
            xml.append(self._build_attributes_xml(indent + 2))

        # Add filters
        if self.filters:
            xml.append(self._build_filters_xml(indent + 2))

        # Add nested links
        for link in self.links:
            xml.append(link.build_xml(indent + 2))

        # Add orders
        if self.orders:
            xml.append(self._build_orders_xml(indent + 2))

        xml.append(f"{spaces}</link-entity>")
        return "\n".join(xml)


class FetchXML:
    """Factory class for creating FetchXML components"""

    def __init__(self, count: int | None = None, page: int | None = None, returntotalrecordcount=False):
        self._entity = None
        self._count = count
        self._page = page
        self._return_total_record_count = returntotalrecordcount
        self._xml = None

    @classmethod
    def fetch(
        cls,
        count: int | None = None,
        page: int | None = None,
        returntotalrecordcount: bool = False,
    ):
        """Create a new fetch query"""
        return cls(count, page, returntotalrecordcount)

    @classmethod
    def entity(cls, name: str):
        """Create a new entity"""
        return Entity(name)

    @classmethod
    def link(
        cls,
        name: str,
        from_attribute: str,
        to_attribute: str,
        link_type: Literal["inner", "outer"] = "inner",
        alias: str | None = None,
    ):
        """Create a new linked entity"""
        return LinkedEntity(name, from_attribute, to_attribute, link_type, alias)

    def set_entity(self, entity: Entity):
        """Set the main entity for the query"""
        self._entity = entity
        return self

    def build(self):
        """Build and return the complete FetchXML query"""
        if not self._entity:
            raise ValueError("Entity must be set before building query")

        xml = [
            '<fetch version="1.0" output-format="xml-platform" mapping="logical" no-lock="false"'
        ]

        if self._page is not None:
            xml.append(f' page="{self._page}"')
        if self._count is not None:
            xml.append(f' count="{self._count}"')
        if self._return_total_record_count:
            xml.append(' returntotalrecordcount="true"')

        xml.append(">")
        xml.append(f'  <entity name="{self._entity.name}">')

        # Add attributes
        if self._entity.attributes:
            xml.append(self._entity._build_attributes_xml(4))

        # Add filters
        if self._entity.filters:
            xml.append(self._entity._build_filters_xml(4))

        # Add links
        for link in self._entity.links:
            xml.append(link.build_xml(4))

        # Add orders
        if self._entity.orders:
            xml.append(self._entity._build_orders_xml(4))

        xml.extend(["  </entity>", "</fetch>"])
        self._xml = "\n".join(xml)
        return self

    def get_query(self):
        """Get the built XML query string"""
        if not self._xml:
            raise ValueError("Query must be built before getting XML")
        return self._xml

    @property
    def entity_name(self):
        """Get the name of the main entity"""
        if not self._entity:
            raise ValueError("Entity must be set before getting entity name")
        return self._entity.name

    @staticmethod
    def parse_response(response_data: dict[str, object]):
        """Parse the response from Dynamics CRM"""
        if not response_data:
            logger.debug("No response data received")
            return None

        # Initialize result with metadata
        metakeys = [f for f in response_data if f.startswith("@")]
        result = {k: response_data[k] for k in metakeys}
        result["value"] = []

        logger.debug(f"Initial result structure: {result}")

        # Get the value array from response, default to empty list if not present
        records: list[dict[str, object]] = response_data.get("value", [])
        logger.debug(f"Number of records to process: {len(records)}")

        # logger.info(records)

        try:
            for record in records:
                parsed_record = {}
                for key, value in record.items():
                    try:
                        # Skip metadata fields
                        if "@" in key:
                            continue

                        # Handle special CRM keys ending with '_value'
                        if key.endswith("_value"):
                            # Remove leading underscore if it exists
                            base_key = key[1:-6] if key.startswith("_") else key[:-6]
                            parsed_record[base_key] = value
                            continue
                        if "." in key:
                            base_key, sub_key = key.split(".", 1)
                            if base_key not in parsed_record:
                                parsed_record[base_key] = {}
                            parsed_record[base_key][sub_key] = value
                            continue

                        parsed_record[key] = value
                    except Exception as e:
                        logger.error(f"Error parsing record field {key}: {e}")
                        parsed_record[key] = value
                result["value"].append(parsed_record)
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None

        logger.debug(f"Final parsed result: {result}")
        return result
