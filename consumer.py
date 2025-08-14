from pika import ConnectionParameters, BlockingConnection, PlainCredentials
from logger_config import logger
import os
from dotenv import load_dotenv
import json
from processor import process_message, ValidationError
from config import load_config
from http_client import HttpClient
from db_client import DatabaseApiClient

load_dotenv()

config = load_config()

credentials = PlainCredentials(config.rmq.username, config.rmq.password)

connection_params = ConnectionParameters(
    host=config.rmq.host,
    port=config.rmq.port,
    credentials=credentials,
)


def _build_db_client() -> DatabaseApiClient:
    http = HttpClient(base_url=config.db.base_url, token=config.db.token, timeout=10.0, max_retries=3)
    return DatabaseApiClient(http)


def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    try:
        db_client = _build_db_client()
        result = process_message(data, db_client)
        logger.info(f"Сообщение обработано: создано {result['created']} из {result['total']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except ValidationError as ve:
        logger.warning(f"Валидация сообщения не пройдена: {ve}. Данные: {data}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"Необработанная ошибка при обработке сообщения: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    with BlockingConnection(connection_params) as conn:
        with conn.channel() as ch:
            ch.queue_declare(queue=config.rmq.queue_name, durable=True)
            ch.basic_qos(prefetch_count=config.rmq.prefetch_count)

            ch.basic_consume(
                queue=config.rmq.queue_name,
                on_message_callback=callback,
            )
            logger.info(f"Старт потребителя очереди: {config.rmq.queue_name} на {config.rmq.host}:{config.rmq.port}")
            ch.start_consuming()


if __name__ == "__main__":
    main()
