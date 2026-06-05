FROM python:3.14.5-slim 

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/ 

CMD ["python", "src/main.py"]