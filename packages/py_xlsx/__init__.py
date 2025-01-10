"""py_xlsx - A type-safe Excel worksheet wrapper using dataclasses.

This package provides a type-safe wrapper around openpyxl's Worksheet class,
allowing you to work with Excel worksheets using your own dataclasses for
type safety and data validation.

Example:
    from dataclasses import dataclass
    from openpyxl import Workbook
    from py_xlsx import TypedWorkSheet

    @dataclass
    class Person:
        name: str
        age: int

    wb = Workbook()
    sheet = TypedWorkSheet(wb, Person)
    sheet.append(Person("John", 30))
"""

from .core.worksheet import TypedWorkSheet
# from .core.mail_merge import mail_merge_prelinked as mail_merge
# from .core.mail_merge_vba import mail_merge_using_vba

__version__ = "0.1.0"
__all__ = ["TypedWorkSheet"]
