import pandas as pd
from prefect import flow, task
from prefect.deployments import run_deployment
from prefect.docker import DockerImage
from prefect.logging import get_run_logger


@task
def read_csv() -> pd.DataFrame:
    logger = get_run_logger()
    logger.info("Открытие CSV файл")
    csv_file = pd.read_csv('CSV.csv', sep=';')
    logger.info("Открытие CSV файл успешно")
    return csv_file


@flow
def main():
    csv_file = read_csv()
    for _, row in list(csv_file.iterrows())[:20]:
        row_dict = row.to_dict()
        run_deployment("main/send_request_deploy",
                       work_queue_name='send_request_queue',
                       parameters={
                           'data': row_dict
                       },
                       timeout=0)


if __name__ == "__main__":
    main.deploy(
        name="read_csv_deploy",
        work_pool_name="sobes_workers",
        image=DockerImage(
            name="read_csv_image",
            dockerfile="Dockerfile"
        ),
        push=False
    )
