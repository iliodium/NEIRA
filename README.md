---

# 📦 NEIRA

### Тестовое задание.

---

## 📂 Структура проекта

```bash
├── /app                              # Приложение
│   ├── /flows/                       
│       ├── /data_processing_deploy/  # Обработка после получения ответа
│       ├── /read_csv_deploy/         # Чтение CSV файла
│       ├── /send_request_deploy/     # Отправка запросов
│       ├── docker-compose.yaml       # Prefect server
│   ├── requirements.txt              # Необходимые библиотеки
├── /envs                             # Переменные для бота и RabbitMQ
├── /rabbitmq                         # RabbitMQ
├── /telegram_bot                     # Телеграм бот
├── .gitignore
├── README.md                         # Документация
└── start_docker_compose_files.sh     # Запуск контейнеров
└── text.txt                          # Команды для настройки prefect
```

---

## 🛠️ Настройка проекта

### 1. Запуск контейнеров:

```bash
docker compose -f rabbitmq/docker-compose.yaml --env-file rabbitmq/.env --env-file envs/.env.rabbitmq_login_data up -d

docker compose -f telegram_bot/docker-compose.yaml --env-file telegram_bot/.env --env-file envs/.env.rabbitmq_login_data up -d

docker compose -f app/docker-compose.yaml --env-file envs/.env.prefect_server --env-file envs/.env.rabbitmq_login_data up -d
```

### 2. Установка зависимостей:

```bash
pip isntall -r .\app\requirements.txt
```

### 3. Создание work pool:

concurrency-limit 1 чтобы каждый worker выполнял только по одному flow\task

```bash
prefect work-pool create --type docker sobes_workers
prefect work-pool update sobes_workers --concurrency-limit 1
```

### 4. Создание work queues:

limit 1 чтобы из очереди бралось по 1 flow\
для того чтобы ограничить кол-во запросов к API

```bash
prefect work-queue create read_csv_queue -p sobes_workers
prefect work-queue create send_request_queue -p sobes_workers --limit 1
prefect work-queue create data_processing_queue -p sobes_workers 
```

### 5. Ограничения:

Ограничение на 1 task в 30 секунд 

```bash
prefect gcl create my_timeout --limit 1 --slot-decay-per-second 0.033
```
### 6. Deployments:

Запустить файлы main.py в app/flows чтобы задеплоить в prefect


## 🧪 Запуск

Поставил ограничение в 20 строк из всего CSV файла \
этого достаточно чтобы проверить работоспособность

Чтобы запустить нам нужны worker \
я запускаю 3 терминал

1 терминал который работает со всеми очередями

```bash
prefect worker start --pool "sobes_workers"
```

1 терминал который работает только с запросами к API

```bash
prefect worker start --pool "sobes_workers" --work-queue "send_request_queue"
```

1 терминал который только обрабатывает данные

```bash
prefect worker start --pool "sobes_workers" --work-queue "data_processing_queue"
```

## 📚 Архитектура

Тк все данные находятся в одном файле, то я решил заполнить этими данными \
очередь, чтобы workerЫ последовательно брали и отправляли запрос на API \
тут использовал ограничение на очередь, чтобы выполнялось не больще 1 задачи \
после получения ответа заполняется новая очередь на обработку данных \
использовал my_timeout чтобы между задачами проходило 30 сек \
а ограничение на work pool заставляет workerА выполнять по 1 задаче \
тут возникла сложность, тк не работал до этого с prefect \
и в документации не удалось найти, как подключить network и volume \
к контейнеру в котором выполняет task\flow \
поэтому не смог монтировать директорию для сохранения результатов \
а также отправлять сообщение в тг \
уточню что бот и rabbitmq работают и сообщения приходят \
проблема с network



как притянуть к имеющимся данным параллельную обработку я не догадался \
но использовать ее довольного легко \
запускаем задачи при помощи submit и если надо ожидаем с wait \
результат смотрим с result \
кол-во потоков определяет в декораторе \
@flow(task_runner=ThreadPoolTaskRunner(max_workers=3))