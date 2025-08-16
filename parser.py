import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import re
import json

import requests


@dataclass
class OlympRecord:
    code: int
    description: str
    name: str
    form: int
    hashed: str


BASE_STATIC_PATH = "/files/rsosh-diplomas-static"
PATTERN = r"^№\d+\. '(.+?)' \('(.+?)'\), (\d+) уровень\. Диплом (\d+) степени\.$"


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


def build_url(base_url: str, year: int, person_hash: str) -> str:
    return f"{base_url.rstrip('/')}{BASE_STATIC_PATH}/compiled-storage-{year}/by-person-released/{person_hash}/codes.js"


def head_exists(url: str, timeout: float = 5.0) -> bool:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "TeamSearchBot/1.0"})
        if r.status_code == 405:
            r = requests.get(url, timeout=timeout, headers={"Range": "bytes=0-0", "User-Agent": "TeamSearchBot/1.0"})
        return 200 <= r.status_code < 400
    except requests.RequestException:
        return False


def parse_js_array(js_str):
    js_str = re.sub(r"^diplomaCodes\s*=", "", js_str.strip())
    js_str = js_str.rstrip(";")
    js_str = js_str.replace("\n", '')
    js_str = js_str.replace(",]", "]")
    
    js_str = js_str.replace('"', '#')
    
    js_str = js_str.replace("'", '"')
    js_str = js_str.replace("oa", '"oa"')
    js_str = js_str.replace("code", '"code"')
    js_str = js_str.replace("name", '"name"')
    js_str = js_str.replace("form", '"form"')
    js_str = js_str.replace("hashed", '"hashed"')
    js_str = js_str.replace('#', "'")
    return json.loads(js_str)


def fetch_codes(url: str, timeout: float = 10.0) -> Optional[List[Dict]]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "TeamSearchBot/1.0"})
        if r.status_code != 200:
            return None
        data_str = r.text
        arr = parse_js_array(data_str)
        return arr
    except Exception as e:
        print(e)
        return None


def find_olymps(fio: str, birthdate_dd_mm_yyyy: str, base_url: str = "https://diploma.olimpiada.ru", years_back: int = 10) -> List[OlympRecord]:
    birth_dt = validate_birthdate(birthdate_dd_mm_yyyy)
    iso_date = birth_dt.strftime("%Y-%m-%d")
    person = person_hash(fio, iso_date)
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

    results = []
    for year in years:
        url = build_url(base_url, year, person)
        if not head_exists(url):
            continue
        payload = fetch_codes(url)
        
        if not payload:
            continue
        for entry in payload:
            match = re.match(PATTERN, entry.get('oa', ''))
            if match:
                olymp_name, profile, level, result = match.groups()
                entry['olymp_name'] = olymp_name
                entry['profile'] = profile
                entry['level'] = int(level)
                result = int(result)
                entry['result'] = 0 if result == 1 else 1
            results.append({
                'name': entry.get('name'),
                'year': year,
                'olymp_name': entry.get('olymp_name'),
                'profile': entry.get('profile'),
                'level': entry.get('level'),
                'result': entry.get('result')
            })
    return results


if __name__ == "__main__":
    fio = "Альбещенко Максимилиан Андреевич"
    dob = "28-11-2008"
    base_url = "https://diploma.olimpiada.ru"
    found_olymps = find_olymps(fio, dob, base_url=base_url)
    for olymp in found_olymps:
        print(olymp)
