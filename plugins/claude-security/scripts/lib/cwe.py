"""CWE data the plugin ships: the weaknesses, and the Simplified Mapping entry each belongs to."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from . import strictjson

UNCATEGORIZED = "Uncategorized"


class CategoryNames(TypedDict):
    """One entry's names in cwe-categories.json."""

    name: str
    title: str


class CatalogFile(TypedDict):
    """The shape of cwe-categories.json."""

    cwe_version: str
    categories: dict[str, CategoryNames]
    category_of: dict[str, int | None]


@dataclass(frozen=True)
class Category:
    """One entry of the view: its CWE number, its common name, its full catalog title."""

    number: int
    name: str
    title: str

    @property
    def id(self) -> str:
        """The entry's CWE id, `CWE-<number>`."""
        return f"CWE-{self.number}"


@dataclass(frozen=True)
class Catalog:
    """One CWE release: the view's entries, and for every weakness the entry it rolls up to."""

    version: str
    categories: dict[int, Category]
    category_of: dict[int, int | None]

    @classmethod
    def load(cls, path: Path) -> Catalog:
        """The catalog stored at `path`."""
        raw = cast("CatalogFile", strictjson.load(path))
        return cls(
            raw["cwe_version"],
            {
                int(number): Category(int(number), names["name"], names["title"])
                for number, names in raw["categories"].items()
            },
            {int(number): category for number, category in raw["category_of"].items()},
        )

    def category(self, cwe: int) -> Category | None:
        """The entry `cwe` rolls up to; None when it reaches none or is not a known weakness."""
        number = self.category_of.get(cwe)
        return self.categories[number] if number is not None else None

    def category_name(self, cwe: int) -> str:
        """The name of the entry `cwe` rolls up to; UNCATEGORIZED where category() is None."""
        entry = self.category(cwe)
        return entry.name if entry is not None else UNCATEGORIZED

    def defines(self, cwe: int) -> bool:
        """Whether the release defines weakness `cwe` at all; category() is None either way."""
        return cwe in self.category_of


def id_number(cwe_id: str) -> int:
    """The number of a canonical `CWE-<number>` id, the spelling every validated finding carries."""
    return int(cwe_id.removeprefix("CWE-"))


def page(number: int) -> str:
    """The address of MITRE's page on the CWE entry with this number."""
    return f"https://cwe.mitre.org/data/definitions/{number}.html"


catalog = Catalog.load(Path(__file__).resolve().with_name("cwe-categories.json"))
