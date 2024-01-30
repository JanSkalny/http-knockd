FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt app.py /app/
COPY templates/form.html /app/templates/

RUN pip install --verbose --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]
