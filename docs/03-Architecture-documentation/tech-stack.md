# Technology Stack, Libraries and Tools

Every framework, library and tool used, with the version, a link and the reason it was chosen over
alternatives. Versions are pinned in `backend/requirements.txt` and `frontend/package-lock.json`.
The overall decision is recorded in [ADR-0001](adr/0001-technology-stack.md).

## Backend (Python 3.12)

| Library | Version | Purpose | Why this one (alternatives) |
|---|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | 3.1 | Web framework, blueprints per module | Small and explicit (Django: too much built in; FastAPI: async not needed) |
| [Flask-SQLAlchemy](https://flask-sqlalchemy.readthedocs.io/) / [SQLAlchemy](https://www.sqlalchemy.org/) | 3.1 / 2.1 | ORM, typed models, exact `Numeric` | De-facto Python ORM (Peewee, Django ORM: smaller ecosystems or framework-bound) |
| [Alembic](https://alembic.sqlalchemy.org/) via [Flask-Migrate](https://flask-migrate.readthedocs.io/) | 1.20 / 4.1 | Versioned schema migrations | Official SQLAlchemy migration tool |
| [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) | 4.7 | JWT login, expiry, revocation callbacks | Built-in blocklist support (PyJWT alone: more custom code) – ADR-0009 |
| [bcrypt](https://pypi.org/project/bcrypt/) | 5.0 | Password hashing | Adaptive, salted, widely audited (SHA-256: too fast for passwords) |
| [marshmallow](https://marshmallow.readthedocs.io/) | 4.4 | Input validation and serialisation | Mature, explicit field errors → 422 responses (Pydantic: equally good; marshmallow fits Flask without extra adapters) |
| [flask-cors](https://flask-cors.readthedocs.io/) | 6.0 | CORS for the dev server | Only needed when frontend runs on another origin |
| [psycopg 3](https://www.psycopg.org/psycopg3/) | 3.3 | PostgreSQL driver | Current maintained driver (psycopg2: legacy) |
| [requests](https://requests.readthedocs.io/) | 2.34 | Calls to the exchange-rate API | Simple synchronous HTTP (httpx: async not needed) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | 1.2 | Loads `.env` in development | Standard |
| [gunicorn](https://gunicorn.org/) | 26.2 | Production WSGI server | Standard for Flask on Linux (Flask dev server: not for production) |
| [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) | 9.2 / 7.1 | Tests and coverage | Fixtures, readable asserts (unittest: more boilerplate) |
| [Ruff](https://docs.astral.sh/ruff/) | 0.17 | Linter and formatter | One fast tool instead of flake8 + isort + black |

## Frontend

| Library | Version | Purpose | Why this one (alternatives) |
|---|---|---|---|
| [React](https://react.dev/) | 19 | UI components | Ecosystem and testing tools (Angular, Vue) – ADR-0001 |
| [Vite](https://vite.dev/) | 8 | Dev server and build | Fast, simple config (Create React App: deprecated; webpack: more config) |
| [React Router](https://reactrouter.com/) | 7 | Client-side routing | Standard router for React |
| [Axios](https://axios-http.com/) | 1.x | HTTP client with interceptors | Central auth header and error handling (fetch: no interceptors) |
| [Recharts](https://recharts.org/) | 3 | Charts (donut, bars, timelines) | Declarative React components (Chart.js: imperative wrapper needed) |
| [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/) | 5 / 16 | Unit and component tests | Shares Vite config (Jest: separate transform setup) |
| [ESLint](https://eslint.org/) | 10 | Linting incl. React hooks rules | Standard |
| Google Fonts: [Fraunces](https://fonts.google.com/specimen/Fraunces), [Inter](https://fonts.google.com/specimen/Inter), [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | – | Headings, body text, tabular numbers | Free licences (OFL); monospaced digits align money columns |

## Infrastructure and services

| Tool / service | Purpose | Why |
|---|---|---|
| [PostgreSQL 16](https://www.postgresql.org/) | Database | Exact NUMERIC, CHECK constraints, enums – ADR-0001 |
| [Docker](https://www.docker.com/) / [Docker Compose](https://docs.docker.com/compose/) | Containers, one-command start | Same setup locally, in CI and in the cloud – NFR-10 |
| [nginx](https://nginx.org/) | Serves the React build, proxies `/api` | Small, fast static server |
| [GitHub](https://github.com/) + [GitHub Actions](https://docs.github.com/actions) | Version control, CI | Required by the assignment; free CI |
| [ExchangeRate-API open access](https://www.exchangerate-api.com/docs/free) | Daily market rates | Free, no API key, 160+ currencies – ADR-0003 |
| [Azure for Students](https://azure.microsoft.com/free/students) | Cloud VM hosting | Free credit without credit card, always on – ADR-0010 |
| [PlantUML](https://plantuml.com/) | UML diagrams as code | Diagrams versioned with the code |

## AI assistance

Claude (Anthropic) was used as a coding assistant for scaffolding, code generation and
documentation drafts. All generated code was reviewed, tested and adapted by the author.
