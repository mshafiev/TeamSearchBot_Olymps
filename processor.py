from typing import Dict, List, Tuple

from logger_config import logger
import parser
from db_client import DatabaseApiClient


class ValidationError(ValueError):
    pass


def _validate_input(data: Dict) -> Tuple[str, str, str]:
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    middle_name = (data.get("middle_name") or "").strip()
    date_of_birth = (data.get("date_of_birth") or "").strip()
    user_tg_id = (data.get("user_tg_id") or "").strip()

    if not first_name or not last_name:
        raise ValidationError("first_name and last_name are required")
    if not date_of_birth:
        raise ValidationError("date_of_birth is required in format dd-mm-yyyy")
    if not user_tg_id:
        raise ValidationError("user_tg_id is required")

    full_name = f"{last_name} {first_name} {middle_name}".strip()
    return full_name, date_of_birth, user_tg_id


def process_message(data: Dict, db: DatabaseApiClient) -> Dict:
    full_name, date_of_birth, user_tg_id = _validate_input(data)

    olympiads = parser.find_olymps(full_name, date_of_birth)

    results: List[Dict] = []
    for index, olymp in enumerate(olympiads):
        payload = {
            "name": olymp["olymp_name"],
            "profile": olymp["profile"],
            "level": olymp["level"],
            "user_tg_id": user_tg_id,
            "result": olymp["result"],
            "year": str(olymp["year"]),
            "is_approved": True,
            "is_displayed": index < 3,
        }

        api_result = db.create_olympiad(payload)
        if api_result.ok:
            logger.info(f"Олимпиада успешно добавлена: {payload}")
        else:
            # Suppress conflict as info, others as warning/error
            if api_result.message == "conflict":
                logger.info(f"Олимпиада уже существует: {payload}")
            elif api_result.message == "rate_limited":
                logger.warning(f"Рейт-лимит БД API. Статус {api_result.status_code}. Данные: {payload}")
            elif api_result.message.startswith("network_error"):
                logger.error(f"Сеть/подключение БД API: {api_result.message}")
            else:
                logger.warning(
                    f"Ошибка при добавлении олимпиады (статус {api_result.status_code}, тип {api_result.message}): {api_result.response_json or ''}"
                )

        results.append({"payload": payload, "status": api_result.message, "ok": api_result.ok})

    return {"created": sum(1 for r in results if r["ok"]), "total": len(results), "details": results}