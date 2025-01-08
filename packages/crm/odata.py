from __future__ import annotations
from dataclasses import dataclass
from httpx._types import PrimitiveData


@dataclass
class OData:
    entity: str
    id: str | None = None
    select: list[str] | None = None
    filter: list[str] | None = None
    orderby: list[str] | None = None
    expand: list[OData] | None = None
    top: int | None = None


def compile_odata_params(odata: OData) -> list[tuple[str, PrimitiveData]]:
    """Compile OData parameters into a list of tuples for httpx."""
    params: list[tuple[str, PrimitiveData]] = []

    if odata.select:
        params.append(("$select", ",".join(odata.select)))

    if odata.filter:
        params.append(("$filter", " and ".join(odata.filter)))

    if odata.orderby:
        params.append(("$orderby", ",".join(odata.orderby)))

    if odata.top and odata.top > 0:
        params.append(("$top", str(odata.top)))

    if odata.expand:
        expand_parts: list[str] = []

        for expand in odata.expand:
            nested_params = compile_odata_params(expand)
            # Convert nested params to OData format
            nested_str = ";".join(f"{k}={v}" for k, v in dict(nested_params).items())
            if expand.entity:
                expand_parts.append(f"{expand.entity}({nested_str})")

        if expand_parts:
            params.append(("$expand", ",".join(expand_parts)))

    return params
