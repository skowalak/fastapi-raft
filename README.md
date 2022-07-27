# Netzwerkprogrammierung SoSe2022 Abschlussprojekt

This project is an implementation of the `Raft` Consensus Algorithm, originally
described in [this paper][raft-paper]. Raft creates a consensus about the state
of a replicated _state machine_ using so-called _replicated logs_. This means, a
new state is accepted as the state of a cluster of state machines, once a
critical mass of particpating state machines have appended the new state to
their logs.

## Architecture

The software used is based on ASGI + Starlette + FastAPI + Pydantic.

### API-Design

A human-readable service documentation is contained in the services' Swagger
Documentation. It is reachable under `https://<service_uri>/docs`

## Dependencies

A detailed list of dependencies can be found in `Pipfile`.

* uvicorn
* Starlette
* FastAPI
* Pydantic
* Pytest
* structlog
* cachetools

## Installation

To run this project please install `docker` and `docker-compose`.

Install dependencies:

``` sh
python -m pip install pipenv
pipenv install --dev
```

You can then run the test suite against the service.

``` sh
pipenv run -v test
```

## Testing

Tests using [`pytest`](https://docs.pytest.org/en/latest/) are in the `test/`
directory. **The easiest way to run them is using
[`gitlab-runner`](https://docs.gitlab.com/runner/install/) with:**

``` sh
$ gitlab-runner exec docker test
```

If you cannot run `gitlab-runner`, you can run them locally with `pipenv run
test -v`. Please always try to use `gitlab-runner` first. For details on the
test script see `Pipfile`.




### Deployment

Available Configuration Variables (as Environment Variables) are listed below.
Note that default values may be subject to change.

| Environment Variable              | Description | Default Value |
|:----------------------------------|:------------|--------------:|
| FASTAPI_TITLE                     | The name of the application. | `Consensus Cluster Service` |
| FASTAPI_MAINT                     | The maintainer name. | `Sebastian Kowalak` |
| FASTAPI_EMAIL                     | Maintainer e-mail address. | `skowalak@techfak.uni-bielefeld.de` |
| FASTAPI_DESCR                     | A description for display in OpenAPI/SwaggerDoc. | `<redacted for brevity>` |
| FASTAPI_SCHEM                     | The path where the OpenAPI schema is available. | `/openapi.json` |
| FASTAPI_DOCS                      | The path where SwaggerDoc is available. | `/docs` |
| API_PREFIX                        | Path prefixed before all API-routes | `/api` |
| ROOT_PATH                         | Path where uvicorn will serve the app. | `/ccs` |
| APP_NAME                          | Name of the application (will be used in error messages e.g.) | `consensus-cluster-service` |
| LOGGING                           | Logging level | `DEBUG` |
| BACKEND_CORS_ORIGINS              | JSON-formatted list of allowed origins. | `[]` |
| SECRET_KEY                        | Key used for JWT encryption | `changeme` |

[raft-paper]: https://raft.github.io/
