FROM python:3

RUN mkdir -p /opt/src/owner
WORKDIR /opt/src/owner

COPY applications/owner/application.py ./application.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/owner"

ENTRYPOINT ["python", "./application.py"]
