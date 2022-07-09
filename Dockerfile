FROM docker.io/library/python:3.10-slim

ENV WORKERS=8

# change working directory
WORKDIR /app

# install requirements
COPY requirements.txt requirements.txt
RUN python -m pip install pip wheel --upgrade && \
    python -m pip install -r requirements.txt

# add gunicorn
RUN python -m pip install gunicorn

# copy everything else in
COPY . .

# run server
EXPOSE 80
ENTRYPOINT ["python", "./docker-entrypoint.py"]