from dataclasses import dataclass
import logging
from typing import Any, Literal


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class FilterCondition:
    attribute: str
    operator: str
    value: str | None = None


@dataclass
class Filter:
    conditions: list[FilterCondition]
    filter_type: Literal["and", "or"] = "and"


@dataclass
class Attribute:
    name: str


EntityNames = Literal["incident", "contact", "coop_notification"]


class Entity:
    """Base class for both main entity and linked entities"""

    attributes: tuple[Attribute, ...]
    filters: tuple[Filter, ...]
    links: tuple["LinkedEntity", ...]
    orders: list[dict[str, str]]
    name: EntityNames

    def __init__(self, name: EntityNames):
        self.name = name
        self.attributes = ()
        self.filters = ()
        self.links = ()
        self.orders = []

    def set_attributes(self, *attributes: Attribute):
        """Set attributes to fetch from the entity"""
        self.attributes = attributes
        return self

    def set_filters(
        self,
        *filters: Filter,
        # filter_type: Literal["and", "or"] = "and",
    ):
        """Set filter conditions for the entity"""
        # filter = Filter(filter_type=filter_type, conditions=conditions)
        # self.filters = [filter]
        self.filters = filters
        return self

    def set_links(self, *links: "LinkedEntity"):
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
        order = {"attribute": attribute, "descending": str(descending)}
        if entityname:
            order["entityname"] = entityname

        self.orders = [order]
        return self

    def build_attributes_xml(self, indent: int = 2):
        """Build XML for attributes"""
        spaces = " " * indent
        xml = [f'{spaces}<attribute name="{attr.name}" />' for attr in self.attributes]
        return "\n".join(xml)

    def build_filters_xml(self, indent: int = 2):
        """Build XML for filters"""
        xml: list[str] = []
        for filter in self.filters:
            xml.append(self._build_filter_xml(filter, indent))
        return "\n".join(xml)

    def _build_filter_xml(self, filter: Filter, indent: int = 2) -> str:
        """Build XML for a single filter"""
        spaces = " " * indent
        xml = [f'{spaces}<filter type="{filter.filter_type}">']

        for condition in filter.conditions:
            print(type(condition))
            condition_xml = [f'{spaces}  <condition attribute="{condition.attribute}"']

            if condition.operator:
                condition_xml.append(f' operator="{condition.operator}"')
            if condition.value:
                condition_xml.append(f' value="{condition.value}"')

            condition_xml.append(" />")
            xml.append("".join(condition_xml))

        xml.append(f"{spaces}</filter>")
        return "\n".join(xml)

    def build_orders_xml(self, indent: int = 2):
        """Build XML for order attributes"""
        if not self.orders:
            return ""
        spaces = " " * indent
        xml_lines: list[str] = []
        for order in self.orders:
            xml_line = f'{spaces}<order attribute="{order["attribute"]}"'
            if order.get("entityname"):
                xml_line += f' entityname="{order["entityname"]}"'
            xml_line += f' descending="{str(order["descending"]).lower()}" />'
            xml_lines.append(xml_line)
        return "\n".join(xml_lines)


class LinkedEntity(Entity):
    """Represents a linked entity in FetchXML"""

    from_attribute: Attribute
    to_attribute: Attribute
    link_type: Literal["inner", "outer"]
    alias: str | None

    def __init__(
        self,
        name: EntityNames,
        from_attribute: Attribute,
        to_attribute: Attribute,
        link_type: Literal["inner", "outer"] = "inner",
        alias: str | None = None,
    ):
        super().__init__(name)
        self.from_attribute = from_attribute
        self.to_attribute = to_attribute
        self.link_type = link_type
        self.alias = alias

    def build_xml(self, indent: int = 2):
        """Build XML for this linked entity"""
        spaces = " " * indent
        xml = [
            f'{spaces}<link-entity name="{self.name}" ',
            f'from="{self.from_attribute.name}" ',
            f'to="{self.to_attribute.name}" ',
            f'link-type="{self.link_type}"',
        ]

        if self.alias:
            xml.append(f' alias="{self.alias}"')
        xml.append(">")

        # Add attributes
        if self.attributes:
            xml.append(self.build_attributes_xml(indent + 2))

        # Add filters
        if self.filters:
            xml.append(self.build_filters_xml(indent + 2))

        # Add nested links
        for link in self.links:
            xml.append(link.build_xml(indent + 2))

        # Add orders
        if self.orders:
            xml.append(self.build_orders_xml(indent + 2))

        xml.append(f"{spaces}</link-entity>")
        return "\n".join(xml)


class FetchXML:
    """Factory class for creating FetchXML components"""

    def __init__(
        self,
        count: int | None = None,
        page: int | None = None,
        returntotalrecordcount: bool = False,
    ):
        self._entity: Entity | None = None
        self._count: int | None = count
        self._page: int | None = page
        self._return_total_record_count: bool = returntotalrecordcount
        self._xml: str | None = None

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
    def entity(cls, name: EntityNames):
        """Create a new entity"""
        return Entity(name)

    @classmethod
    def link(
        cls,
        name: EntityNames,
        from_attribute: Attribute,
        to_attribute: Attribute,
        link_type: Literal["inner", "outer"] = "inner",
        alias: str | None = None,
    ):
        """Create a new linked entity"""
        return LinkedEntity(name, from_attribute, to_attribute, link_type, alias)

    def set_entity(self, entity: Entity):
        """Set the main entity for the query"""
        self._entity = entity
        return entity

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
            xml.append(self._entity.build_attributes_xml(4))

        # Add filters
        if self._entity.filters:
            xml.append(self._entity.build_filters_xml(4))

        # Add links
        for link in self._entity.links:
            xml.append(link.build_xml(4))

        # Add orders
        if self._entity.orders:
            xml.append(self._entity.build_orders_xml(4))

        xml.extend(["  </entity>", "</fetch>"])
        self._xml = "\n".join(xml)
        # return self

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
    def parse_response(response_data: dict[str, Any]):
        """Parse the response from Dynamics CRM"""
        if not response_data:
            logger.debug("No response data received")
            return None

        # print("RAW DATA")
        # raw = json.dumps(response_data, indent=4)
        # print(raw)

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
