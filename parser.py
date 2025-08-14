import hashlib
import json
import re
from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple

import logging
import requests

logger = logging.getLogger("olymps_service")

BASE_STATIC_PATH = "/files/rsosh-diplomas-static"


def normalize_fio(fio: str) -> str:
    fio = re.sub(r"\s+", " ", fio.strip().lower())
    return re.sub(r"(^|[\-\s])[^\s]", lambda match: match.group(0).upper(), fio)


def validate_birthdate(date_str: str) -> datetime:
    if not re.fullmatch(r"\d{2}-\d{2}-\d{4}", date_str):
        raise ValueError("Дата рождения должна быть в формате дд-мм-гггг")
    return datetime.strptime(date_str, "%d-%m-%Y")


def person_hash(fio: str, birthdate: str) -> str:
    namestring = f"{normalize_fio(fio)} {birthdate}"
    return hashlib.sha256(namestring.encode("utf-8")).hexdigest()


def build_codes_url(base_url: str, year: int, person_hash: str) -> str:
    return f"{base_url.rstrip('/')}" f"{BASE_STATIC_PATH}" f"/compiled-storage-{year}/by-person-released/{person_hash}/codes.js"


def head_exists(url: str, timeout: float = 5.0) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "TeamSearchBot/1.0"})
        if r.status_code == 405:
            r = requests.get(url, timeout=timeout, headers={"Range": "bytes=0-0", "User-Agent": "TeamSearchBot/1.0"})
        return 200 <= r.status_code < 400
    except requests.RequestException as exc:
        logger.warning(f"HEAD/GET exists check failed for {url}: {exc}")
        return False


def _parse_oa(oa: str) -> Optional[Tuple[str, str, int, int]]:
    # Extract first two single-quoted segments with escape handling
    parts: List[str] = []
    buf: List[str] = []
    in_str = False
    escaped = False
    for ch in oa:
        if escaped:
            if in_str:
                buf.append(ch)
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == "'":
            if in_str:
                parts.append("".join(buf))
                buf = []
                in_str = False
                if len(parts) >= 2:
                    break
            else:
                in_str = True
            continue
        if in_str:
            buf.append(ch)
    if len(parts) < 2:
        return None
    name, profile = parts[0], parts[1]
    level_m = re.search(r"(\d+)\s+уровень", oa)
    result_m = re.search(r"Диплом\s*(\d+)\s+степени", oa)
    if not (level_m and result_m):
        return None
    try:
        return name, profile, int(level_m.group(1)), int(result_m.group(1))
    except ValueError:
        return None


def parse_js_array(js_str: str) -> List[Dict]:
    s = re.sub(r"^diplomaCodes\s*=\s*", "", js_str.strip())
    s = s.rstrip(";")
    s = s.replace(",]", "]")
    # Extract object bodies between braces at top-level (no nested braces expected)
    objs: List[Dict] = []
    for obj_match in re.finditer(r"\{(.*?)\}(?=,|\]|$)", s, flags=re.DOTALL):
        block = obj_match.group(1)
        obj: Dict[str, object] = {}
        # oa: single-quoted string up to next key or end of object
        m_oa = re.search(r"\boa\s*:\s*'(.*?)'(?=\s*,\s*(name|form|hashed)\s*:|\s*\Z)", block, flags=re.DOTALL)
        if m_oa:
            obj["oa"] = m_oa.group(1)
        m_name = re.search(r"\bname\s*:\s*'(.*?)'", block, flags=re.DOTALL)
        if m_name:
            obj["name"] = m_name.group(1)
        m_form = re.search(r"\bform\s*:\s*(\d+)", block)
        if m_form:
            obj["form"] = int(m_form.group(1))
        m_hashed = re.search(r"\bhashed\s*:\s*'(.*?)'", block, flags=re.DOTALL)
        if m_hashed:
            obj["hashed"] = m_hashed.group(1)
        # Derive human fields from oa
        if "oa" in obj:
            parsed = _parse_oa(str(obj["oa"]))
            if parsed:
                olymp_name, profile, lvl, res = parsed
                obj["olymp_name"] = olymp_name
                obj["profile"] = profile
                obj["level"] = lvl
                obj["result"] = 0 if res == 1 else 1
        if obj:
            objs.append(obj)
    return objs


def fetch_codes(url: str, timeout: float = 10.0) -> Optional[List[Dict]]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "TeamSearchBot/1.0"})
        if r.status_code != 200:
            return None
        data_str = r.text
        arr = parse_js_array(data_str)
        return arr
    except Exception as exc:
        logger.error(f"Failed to fetch or parse codes from {url}: {exc}")
        return None


def _years_window(years_back: int) -> List[int]:
    this_year = datetime.now(UTC).year
    start_year = max(2016, this_year - years_back + 1)
    return list(range(start_year, this_year + 1))


def find_olymps(
    fio: str,
    birthdate_dd_mm_yyyy: str,
    base_url: str = "https://diploma.olimpiada.ru",
    years_back: int = 10,
) -> List[Dict]:
    birth_dt = validate_birthdate(birthdate_dd_mm_yyyy)
    iso_date = birth_dt.strftime("%Y-%m-%d")
    person = person_hash(fio, iso_date)
    years = _years_window(years_back)

    results: List[Dict] = []
    for year in years:
        url = build_codes_url(base_url, year, person)
        if not head_exists(url):
            continue
        payload = fetch_codes(url)
        if not payload:
            continue
        for entry in payload:
            olymp_name = entry.get("olymp_name")
            profile = entry.get("profile")
            level = entry.get("level")
            result = entry.get("result")
            if not olymp_name or profile is None or level is None or result is None:
                parsed = _parse_oa(str(entry.get("oa", "")))
                if parsed:
                    _olymp_name, _profile, _level, _result = parsed
                    olymp_name = _olymp_name
                    profile = _profile
                    level = _level
                    result = 0 if _result == 1 else 1
            results.append(
                {
                    "name": entry.get("name"),
                    "year": year,
                    "olymp_name": olymp_name,
                    "profile": profile,
                    "level": level,
                    "result": result,
                }
            )
    return results


if __name__ == "__main__":
    fio = "Альбещенко Максимилиан Андреевич"
    dob = "28-11-2008"
    base_url = "https://diploma.olimpiada.ru"
    found_olymps = find_olymps(fio, dob, base_url=base_url)
    for olymp in found_olymps:
        print(olymp)