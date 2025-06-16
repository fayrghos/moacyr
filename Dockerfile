FROM python:3.11-alpine

WORKDIR /app
COPY . .

RUN python -m pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
