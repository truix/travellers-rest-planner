"""I2 Localization lookup.

The game ships I2 Localization terms in `resources.assets`. We pre-extract them
to `data/i18n.json` (see scripts/dump_i2l.py) into the shape:
    { "languages": [{name, code}, ...], "terms": { term: [lang0, lang1, ...] } }

Item / Food translation keys observed in the game:
    Items/item_name_<item.id>     ← canonical
    Items/item_description_<item.id>
    item<NameId>                  ← legacy fallback (e.g. "itemBlueberry")

Crops use either their `nameId` directly (e.g. "BlueberryCrop") or fall back
to the harvest item's translation.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_PATH = os.path.join(ROOT, "data", "i18n.json")

DEFAULT_LANG = "English"


@lru_cache(maxsize=1)
def _load() -> dict:
    if not os.path.exists(I18N_PATH):
        return {"languages": [], "terms": {}}
    with open(I18N_PATH, encoding="utf8") as f:
        return json.load(f)


def available_languages() -> list[dict]:
    return _load()["languages"]


def language_index(name: str) -> int:
    langs = available_languages()
    for i, l in enumerate(langs):
        if l["name"] == name or l["code"] == name:
            return i
    return 0  # English fallback


class Translator:
    def __init__(self, language: str = DEFAULT_LANG):
        data = _load()
        self.terms: dict[str, list[str]] = data["terms"]
        self.languages = data["languages"]
        self.lang = language
        self.idx = language_index(language)

    def set_language(self, language: str):
        self.lang = language
        self.idx = language_index(language)

    def get(self, key: str | None) -> str | None:
        if not key:
            return None
        row = self.terms.get(key)
        if not row:
            return None
        if self.idx < len(row):
            v = row[self.idx]
            if v:
                return v
        # fallback to English (slot 0)
        return row[0] if row else None

    # ------- domain helpers -------

    def item(self, item_id: int | None, name_id: str | None = None,
             fallback: str | None = None) -> str:
        if item_id is not None:
            v = self.get(f"Items/item_name_{item_id}")
            if v:
                return v
        if name_id:
            v = self.get(f"item{name_id}") or self.get(name_id)
            if v:
                return v
        return fallback or (f"item{item_id}" if item_id is not None else "?")

    def crop(self, crop_name_id: str | None, harvest_item_id: int | None = None,
             fallback: str | None = None) -> str:
        if crop_name_id:
            v = self.get(crop_name_id) or self.get(f"crop{crop_name_id}")
            if v:
                return v
        if harvest_item_id is not None:
            v = self.item(harvest_item_id)
            if v and not v.startswith("item"):
                return v
        return fallback or (crop_name_id or "?")

    def recipe(self, output_item_id: int | None, fallback: str | None = None,
               output_name_id: str | None = None) -> str:
        if output_item_id is not None:
            v = self.get(f"Items/item_name_{output_item_id}")
            if v:
                return v
        if output_name_id:
            v = self.get(f"item{output_name_id}") or self.get(output_name_id)
            if v:
                return v
        return fallback or "?"
