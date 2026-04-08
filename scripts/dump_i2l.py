"""Extract I2 Localization strings from the Travellers Rest I2Languages asset.

We can't use a generated typetree (it goes out of bounds, schema mismatch),
so we walk the raw MonoBehaviour bytes by hand using the known layout:

LanguageSourceAsset {
  base MonoBehaviour header (m_GameObject, m_Enabled, m_Script, m_Name)
  LanguageSourceData mSource {
    bool UserAgreesToHaveItOnTheScene
    bool UserAgreesToHaveItInsideThePluginsFolder
    bool GoogleLiveSyncIsUptoDate
    List<TermData> mTerms {
      string Term
      int    TermType
      string[] Languages
      byte[]   Flags
      string[] Languages_Touch
    }
    bool   CaseInsensitiveTerms
    int    OnMissingTranslation
    string mTerm_AppName
    List<LanguageData> mLanguages { string Name, string Code, byte Flags }
    ...
  }
}

Unity binary serialization rules with align flag:
  string = int32 length + UTF-8 bytes + align(4)
  array  = int32 size + per element
  int    = 4 bytes
  bool   = 1 byte + align(4) (because parent has align flag)

Output: data/i18n.json with shape:
  {
    "languages": ["Spanish", "English", ...],
    "terms": { "Items/item_name_15": ["Cultivo de Arándano", "Blueberry Crop", ...], ... }
  }
"""
from __future__ import annotations

import json
import os
import struct
import sys

import UnityPy
UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.0"

import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from planner.gamepath import find_game_data_dir; GAME = find_game_data_dir()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "i18n.json")


def find_asset_bytes() -> bytes:
    env = UnityPy.load(os.path.join(GAME, "resources.assets"))
    for o in env.objects:
        if o.type.name != "MonoBehaviour":
            continue
        try:
            d = o.read(check_read=False)
            cn = d.m_Script.read().m_ClassName
        except Exception:
            continue
        if cn == "LanguageSourceAsset":
            return o.get_raw_data()
    raise RuntimeError("LanguageSourceAsset not found in resources.assets")


def align4(pos: int) -> int:
    return (pos + 3) & ~3


def read_i32(buf: bytes, pos: int) -> tuple[int, int]:
    return struct.unpack_from("<i", buf, pos)[0], pos + 4


def read_string(buf: bytes, pos: int) -> tuple[str, int]:
    length, pos = read_i32(buf, pos)
    if length < 0 or length > 1 << 24:
        raise ValueError(f"insane string length {length} at {pos-4}")
    s = buf[pos:pos+length].decode("utf-8", errors="replace")
    pos += length
    pos = align4(pos)
    return s, pos


def read_string_array(buf: bytes, pos: int) -> tuple[list[str], int]:
    count, pos = read_i32(buf, pos)
    if count < 0 or count > 1 << 20:
        raise ValueError(f"insane array len {count}")
    out = []
    for _ in range(count):
        s, pos = read_string(buf, pos)
        out.append(s)
    return out, pos


def read_byte_array(buf: bytes, pos: int) -> tuple[bytes, int]:
    count, pos = read_i32(buf, pos)
    data = buf[pos:pos+count]
    pos += count
    pos = align4(pos)
    return data, pos


def parse(raw: bytes) -> dict:
    """Walk the asset and pull out languages + terms."""
    pos = 0

    # ----- standard MonoBehaviour base -----
    # m_GameObject PPtr  (int + int64)
    pos += 12
    # m_Enabled byte + align4
    pos += 1
    pos = align4(pos)
    # m_Script PPtr
    pos += 12
    # m_Name string
    name, pos = read_string(raw, pos)

    # ----- LanguageSourceData -----
    # 3 bools each followed by align4 (because the children align)
    pos += 1; pos = align4(pos)
    pos += 1; pos = align4(pos)
    pos += 1; pos = align4(pos)

    # mTerms: int size + each TermData
    n_terms, pos = read_i32(raw, pos)
    if n_terms < 0 or n_terms > 1 << 20:
        raise ValueError(f"insane mTerms count {n_terms} at {pos-4}")

    print(f"  asset name={name!r}  mTerms count={n_terms}", file=sys.stderr)

    terms: dict[str, list[str]] = {}
    for i in range(n_terms):
        try:
            term, pos = read_string(raw, pos)
            term_type, pos = read_i32(raw, pos)
            languages, pos = read_string_array(raw, pos)
            flags, pos = read_byte_array(raw, pos)
            languages_touch, pos = read_string_array(raw, pos)
        except Exception as e:
            print(f"  parse failed at term {i}/{n_terms}, pos={pos}: {e}", file=sys.stderr)
            break
        terms[term] = languages

    # After mTerms: bool, int, string, then mLanguages
    # bool CaseInsensitiveTerms + align4
    pos += 1; pos = align4(pos)
    # int OnMissingTranslation
    _, pos = read_i32(raw, pos)
    # string mTerm_AppName
    _, pos = read_string(raw, pos)

    # mLanguages: int size + each LanguageData{Name string, Code string, Flags byte+align}
    n_lang, pos = read_i32(raw, pos)
    languages_meta = []
    if 0 <= n_lang <= 64:
        for _ in range(n_lang):
            try:
                lang_name, pos = read_string(raw, pos)
                lang_code, pos = read_string(raw, pos)
                pos += 1; pos = align4(pos)
                languages_meta.append({"name": lang_name, "code": lang_code})
            except Exception as e:
                print(f"  language parse failed: {e}", file=sys.stderr)
                break

    print(f"  parsed {len(terms)} terms, {len(languages_meta)} languages", file=sys.stderr)
    return {
        "languages": languages_meta,
        "terms": terms,
    }


def main():
    print("loading asset...", file=sys.stderr)
    raw = find_asset_bytes()
    print(f"raw size = {len(raw):,} bytes", file=sys.stderr)
    result = parse(raw)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"wrote {OUT}", file=sys.stderr)
    # spot-check a few items
    print("--- sample ---", file=sys.stderr)
    for k in list(result["terms"])[:5]:
        print(f"  {k!r} -> {result['terms'][k]}", file=sys.stderr)
    print("languages:", [l['name'] for l in result['languages']], file=sys.stderr)


if __name__ == "__main__":
    main()
