# Netzwerkprogrammierung SoSe2022 Abschlussprojekt

This project is an implementation of the `Raft` Consensus Algorithm, originally
described in [this paper][raft-paper]. Raft creates a consensus about the state
of a replicated _state machine_ using so-called _replicated logs_. This means, a
new state is accepted as the state of a cluster of state machines, once a
critical mass of particpating state machines have appended the new state to
their logs.

Raft is known for its implementation and usage in [`etcd`][etcd] and `k8s`, but
also for the [`hashicorp` implementation in Go][hashicorp] and the
[`nebulaDB`][nebuladb] project.

## Assignment

* Implementation of a leader election algorithm using a quorum, meaning more
  than half of nodes in the cluster must vote for the same node in order for it
  to become master
* Failover, meaning nodes can disappear and reappear at any given time, or new
  nodes can be added to the group

## Code

The software used is based on ASGI + Starlette + FastAPI + Pydantic.

In this Code Base, the [numpydoc v1.5.dev0 standard][npdoc] for Python
docstrings is applied. Formatting was applied with [black][black].
The code was linted using [pylint][pylint], [mypy][mypy] and [bandit][bandit].
Tests were not linted.

**Disclaimer**: I have worked with FastAPI for the past two years and
**reused some of my own code** for this project.

### License

This projects code is licensed under the MIT License which has a high
compatibility to other open-source licenses. For details see `LICENSE` file.

### API-Design

A human-readable service documentation is contained in the services' Swagger
Documentation. It is reachable under `https://<service_uri>/docs`

## Dependencies

A detailed list of dependencies can be found in `Pipfile`. Dependencies are
managed using [`pipenv`][pipenv].

* dnspython: Tools for use with Docker DNS
* FastAPI: Web framework
* Pydantic: JSON validation
* Pytest: Testing
* requests: HTTP library
* Starlette: ASGI framework
* structlog: Logging
* uvicorn: ASGI web server

## Installation

To run this project please install `docker` and `docker-compose`.

Install dependencies and development dependencies:

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
$ gitlab-runner exec docker test_job
```

If you cannot run `gitlab-runner`, you can run them locally with `pipenv run
test -v`. Please always try to use `gitlab-runner` first. For details on the
test script see `Pipfile`.

The tests cover only raft-related functionality like setting and resetting
terms, state changes and requests and responses.

## Running

The project is designed to be run with [`Docker`][docker], bzw.
`docker-compose`. The reason for this is that the discovery mechanism works with
DNS. All nodes share a service domain name, e.g. `node`. By DNS lookup for
`node` the service receives the IP addresses of all individual replicas of the
service.

Another small FastAPI webservice is contained in the directory `monitor/`. Its
purpose is to collect status data from all replicas of the main `app` and
display it on a webpage.

### Example

The repo contains two `Dockerfiles`. `app.Dockerfile` is the Docker
configuration for the service. `monitor.Dockerfile` is the Dockerfile for the
`monitor/` service.

In the `docker-compose.yaml` the two services are set up:

* The Raft App itself is configured under the section `node`. To find the other
  replicas, the envvar `APP_NAME` is set to the service name `node`. For more
  information on configuration variables see [below](#configuration).
* By default the Raft App is configured to run as 3 replicas. To change that
  number, change it in the `deploy.replicas` section and pass the new value to
  the service via the envvar `NUM_REPLICAS`.
* The Monitor App is configured to open port `8000` and serve the information
  page on document root.
* The Monitor App gets passed the service name of the Raft App via the
  `MAIN_APP_NAME` envvar and its own port and bind address via `ADDRESS`.
  These config options can be reviewed in `monitor/main.py`.

To run the example, `cd` into the project directory and run
`docker-compose up --build`. When all services are started up, visit
[http://localhost:8000/](http://localhost:8000) in a browser to view the status
page.

### Configuration

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
| ROOT_PATH                         | Path where uvicorn will serve the app. | `` |
| APP_NAME                          | Name of the application (will be used in error messages e.g.) | `consensus-cluster-service` |
| LOGGING                           | Logging level | `DEBUG` |
| ELECTION_TIMEOUT_LOWER_MILLIS     | Lower bound for election timeout in milliseconds | 150 |
| ELECTION_TIMEOUT_UPPER_MILLIS     | Upper bound for election timeout in milliseconds | 300 |


[npdoc]: https://numpydoc.readthedocs.io/en/latest/format.html
[raft-paper]: https://raft.github.io/
[black]: https://github.com/psf/black
[etcd]: https://github.com/etcd-io/etcd
[tikv]: https://github.com/tikv/tikv
[rethinkdb]: https://github.com/rethinkdb/rethinkdb
[nebuladb]: https://github.com/vesoft-inc/nebula
[hashicorp]: https://github.com/hashicorp/raft
[pylint]: https://pypi.org/project/pylint/
[mypy]: https://github.com/python/mypy
[bandit]: https://github.com/PyCQA/bandit
[pipenv]: https://pipenv.pypa.io/en/latest/
[docker]: https://www.docker.com/
