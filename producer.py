from pika import ConnectionParameters, BlockingConnection, PlainCredentials
import os
import json
from typing import Optional
from dotenv import load_dotenv
import logging
import asyncio


logging.getLogger("pika").setLevel(logging.WARNING)


load_dotenv()

RMQ_USER = os.getenv("RMQ_USER")
RMQ_PASS = os.getenv("RMQ_PASS")
RMQ_HOST = os.getenv("RMQ_HOST")
RMQ_PORT = int(os.getenv("RMQ_PORT", 5672))

credentials = PlainCredentials(RMQ_USER, RMQ_PASS)

connection_params = ConnectionParameters(
    host=RMQ_HOST,
    port=RMQ_PORT,
    credentials=credentials,
)


def send_olymps_success(message_data: dict) -> bool:
    try:
        with BlockingConnection(connection_params) as conn:
            with conn.channel() as ch:
                ch.queue_declare(queue="olymps_success")
                ch.basic_publish(
                    exchange="",
                    routing_key="olymps_success",
                    body=json.dumps(message_data)
                )
                logging.info("Like message enqueued: %s", message_data)
                return True
    except Exception as exc:
        logging.error("RMQ publish failed: %s", exc)
        return False


if __name__ == "__main__":
    main()