import json
import os
import time
from datetime import datetime

import pandas as pd
import pika
from prefect import flow, task
from prefect.concurrency.sync import rate_limit
from prefect.docker import DockerImage
from prefect.logging import get_run_logger

RABBITMQ_USERNAME = 'rabbitmq_admin'
RABBITMQ_PASSWORD = 'Dsbh4328Dn21'
RABBITMQ_DNS = 'rabbitmq'


def send_message_to_queue(message):
    credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(RABBITMQ_DNS,
                                           5672,
                                           '/',
                                           credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.basic_publish(exchange='', routing_key='messages', body=message)

    connection.close()


@task
def data_processing(data: dict) -> dict:
    logger = get_run_logger()
    logger.info('Начинается обработка ответа')
    df = pd.DataFrame(data["Time Series (Daily)"])
    df.iloc[4] = df.iloc[4].astype(float) + 1000
    time.sleep(1)
    data = df.to_dict()
    logger.info('Обработка ответа завершена успешно')

    return data


@task
def save_json(data: dict):
    logger = get_run_logger()
    logger.info('Начинается сохранение данных')
    date_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
    with open(os.path.join("json_data", f"data_{date_time}.json"), "w") as json_file:
        json.dump(data, json_file, indent=4)
    logger.info('Сохранение данных прошло успешно')


@flow
def main(data: dict):
    rate_limit("my_timeout")
    data = data_processing(data)
    save_json(data)
    send_message_to_queue('Готово !!!')


if __name__ == "__main__":
    main.deploy(
        name="data_processing_deploy",
        work_pool_name="sobes_workers",
        image=DockerImage(
            name="data_processing_image",
            dockerfile="Dockerfile",
        ),
        push=False
    )
