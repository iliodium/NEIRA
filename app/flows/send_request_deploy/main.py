import requests
from prefect import flow, task, get_run_logger
from prefect.deployments import run_deployment
from prefect.docker import DockerImage


@task(retries=2, retry_delay_seconds=5)
def send_request(data: dict) -> dict:
    logger = get_run_logger()
    logger.info('Отправляю запрос')
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo'
    response = requests.get(url)
    if response.status_code >= 300:
        logger.error(f'Что-то пошло не так, код {response.status_code}')
        raise requests.ConnectionError

    try:
        data = response.json()
    except Exception as e:
        logger.error(e)
        raise e

    logger.info('Ответ получен успешно')

    return data


@flow
def main(data: dict):
    response = send_request(data)
    run_deployment("main/data_processing_deploy",
                   work_queue_name='data_processing_queue',
                   parameters={
                       'data': response
                   },
                   timeout=0)


if __name__ == "__main__":
    main.deploy(
        name="send_request_deploy",
        work_pool_name="sobes_workers",
        image=DockerImage(
            name="send_request_image",
            dockerfile="Dockerfile"
        ),
        push=False
    )
