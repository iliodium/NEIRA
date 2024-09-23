FROM python:3.12.1-slim

WORKDIR /app
COPY . .


RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
CMD ["python3", "main.py"]