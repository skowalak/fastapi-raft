FROM python:3.10-buster

WORKDIR /app

COPY Pipfile .
COPY Pipfile.lock .
RUN apt-get update
RUN apt-get install -y dnsutils
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --dev --system --deploy --ignore-pipfile

# scripts
COPY script_leader.sh .
COPY script_follower.sh .

COPY app/ ./app

