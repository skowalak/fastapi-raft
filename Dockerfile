FROM python:3.10-buster

WORKDIR /app

COPY Pipfile .
COPY Pipfile.lock .
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install --dev --system --deploy --ignore-pipfile

# migrations
COPY migrations .
COPY pyproject.toml .

COPY app/ ./app

