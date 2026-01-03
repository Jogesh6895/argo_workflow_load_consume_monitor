FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED=1

WORKDIR /workflows/

COPY  ./workflows/ /workflows/

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

CMD ["sleep", "infinity"]
