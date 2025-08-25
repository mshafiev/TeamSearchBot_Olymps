from pika import ConnectionParameters, BlockingConnection, PlainCredentials
from logger_config import logger
import os
from dotenv import load_dotenv
import json
from parser import find_olymps
import requests
from producer import send_olymps_success

load_dotenv()

RMQ_USER = os.getenv("RMQ_USER")
RMQ_PASS = os.getenv("RMQ_PASS")
RMQ_HOST = os.getenv("RMQ_HOST")
RMQ_PORT = int(os.getenv("RMQ_PORT", 5672))
DB_HOST = os.getenv("DB_SERVER_HOST")
DB_PORT = os.getenv("DB_SERVER_PORT")

credentials = PlainCredentials(RMQ_USER, RMQ_PASS)

connection_params = ConnectionParameters(
    host=RMQ_HOST,
    port=RMQ_PORT,
    credentials=credentials,
)

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        middle_name = data.get("middle_name", "")
        date_of_birth = data.get("date_of_birth", "")
        user_tg_id = data.get("user_tg_id", "")

        full_name = f"{last_name} {first_name} {middle_name}"
        olympiads = find_olymps(full_name, date_of_birth)

        for index, olymp in enumerate(olympiads):
            try:
                olymp_data = {
                    'name': olymp['olymp_name'],
                    'profile': olymp['profile'],
                    'level': olymp['level'],  
                    'user_tg_id': user_tg_id,
                    'result': olymp['result'],  
                    'year': str(olymp['year']),
                    'is_approved': True,
                    'is_displayed': True if index < 3 else False
                }
                response = requests.post(f"http://{DB_HOST}:{DB_PORT}/olymp/create/", json=olymp_data)
                if response.status_code == 200:
                    logger.info(f"Олимпиада успешно добавлена: {olymp_data}")
                else:
                    logger.warning(f"Ошибка при добавлении олимпиады (от запроса): {response.text}")
            except Exception as e:
                logger.error(f"Ошибка при добавлении олимпиады: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        message_data = {"user_id": str(user_tg_id)}
        send_olymps_success(message_data)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

def main():
    with BlockingConnection(connection_params) as conn:
        with conn.channel() as ch:
            ch.queue_declare(queue="olymps")

            ch.basic_consume(
                queue="olymps",
                on_message_callback=callback,
            )
            ch.start_consuming()

if __name__ == "__main__":
    main()
