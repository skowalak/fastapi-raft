# Netzwerkprogrammierung SoSe2022 Abschlussprojekt

### Code Style

In this Code Base, the [numpydoc v1.5.dev0 standard][npdoc] for Python
docstrings is applied.

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

### Testing

Tests using [`pytest`](https://docs.pytest.org/en/latest/) are in the `test/`
directory. **The easiest way to run them is using
[`gitlab-runner`](https://docs.gitlab.com/runner/install/) with:**

``` sh
$ gitlab-runner exec docker test
```

If you cannot run `gitlab-runner`, you can run them locally with `pipenv run
test -v`. Please always try to use `gitlab-runner` first. For details on the
test script see `Pipfile`.

### API-Design

A human-readable service documentation is contained in the services' Swagger
Documentation. It is reachable under `https://<service_uri>/docs`

[npdoc]: https://numpydoc.readthedocs.io/en/latest/format.html
