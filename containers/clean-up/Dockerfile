FROM python:3.10.10-slim-bullseye

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION python

CMD [ "python", "./main.py" ]
