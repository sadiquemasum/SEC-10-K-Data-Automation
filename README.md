# SEC 10-K Data Automation

A Python-based document automation application that retrieves company annual reports (SEC 10-K filings) from the U.S. Securities and Exchange Commission (SEC), converts them into PDF documents, and stores filing metadata in PostgreSQL.

The application provides two interfaces — a command-line interface (CLI) and a REST API — using a shared service layer.

## 1. Project Overview

The application supports:

- Searching publicly listed companies by name or ticker symbol.
- Retrieving company CIK identifiers.
- Caching SEC company ticker information locally.
- Storing company information in PostgreSQL.
- Discovering the latest original SEC 10-K filing, excluding amendments.
- Downloading filing documents from SEC EDGAR.
- Converting SEC HTML documents into PDF files.
- Storing generated PDFs locally, organized by company.
- Recording filing metadata in PostgreSQL.
- Downloading reports through the CLI or REST API.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.14 | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL 17 | Relational database |
| SQLAlchemy 2.x | ORM and database management |
| Psycopg 3 | PostgreSQL driver |
| Pydantic 2 | Data validation and schemas |
| Requests | SEC HTTP integration |
| Playwright / Chromium | HTML-to-PDF conversion |
| Docker | Application containerization |
| Docker Compose | Multi-container orchestration |
| Uvicorn | ASGI server |
| Pytest | Automated testing |

## 3. Architecture

The application follows a modular architecture with a shared business logic layer.

Both the CLI and REST API use the same SEC integration, filing processing, PDF conversion, and storage services.

```text
                 User
                  |
          +-------+-------+
          |               |
         CLI           FastAPI
          |               |
          +-------+-------+
                  |
               Services
                  |
       +----------+----------+
       |          |          |
   SEC Service  Filing    Storage
                Service   Service
                  |
              PDF Service
                  |
              PostgreSQL
                  |
            Local PDF Storage
```

### Project structure

```text
fastapi-docker-app/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   │
│   ├── cli/
│   │   └── main.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   └── filing.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   └── filing.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── companies.py
│   │   └── filings.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── sec_service.py
│       ├── filing_service.py
│       ├── pdf_service.py
│       └── storage_service.py
│
├── tests/
├── downloads/                 # Runtime-generated files
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| `main.py` | FastAPI application entry point and lifecycle |
| `database.py` | Database engine, session factory, and dependencies |
| `models/` | SQLAlchemy database models |
| `schemas/` | Pydantic validation and response schemas |
| `routers/` | REST API endpoints |
| `cli/` | Interactive and command-line application |
| `sec_service.py` | SEC company ticker data and company lookup |
| `filing_service.py` | SEC filing discovery and HTML download |
| `pdf_service.py` | HTML-to-PDF conversion using Playwright |
| `storage_service.py` | PDF file organization and storage |

## 4. SEC Company Lookup

The application uses PostgreSQL as its primary company database and the SEC's `company_tickers.json` as a source for discovering companies.

### Lookup workflow

1. Search for a company in PostgreSQL.
2. If the company is not found, check the local SEC ticker cache.
3. Retrieve the company information and CIK.
4. Save the discovered company in PostgreSQL.
5. Return the company information.

### Cache strategy

- Download SEC company ticker information.
- Store the JSON file locally.
- Refresh the cache after 24 hours.
- Reuse the existing cache when possible.
- Save discovered companies in PostgreSQL.

## 5. Database Design

The application uses PostgreSQL with SQLAlchemy ORM.

### Companies

| Column | Description |
|---|---|
| `id` | Internal company ID |
| `name` | Company name |
| `ticker` | Stock ticker symbol |
| `cik` | SEC Central Index Key |
| `created_at` | Record creation timestamp |

### Filings

| Column | Description |
|---|---|
| `id` | Internal filing ID |
| `company_id` | Reference to the company |
| `accession_number` | SEC filing accession number |
| `form` | Filing type, e.g. 10-K |
| `document` | SEC primary document filename |
| `filing_date` | SEC filing date |
| `report_date` | Financial reporting period end date |
| `pdf_path` | Stored PDF location |
| `created_at` | Record creation timestamp |

The CIK and accession number are stored as strings to preserve their identifiers.

## 6. SEC 10-K Document Workflow

The application retrieves the latest original 10-K filing for a company. Amended filings (`10-K/A`) are excluded.

```text
       Company CIK
            |
            v
     SEC Submissions API
            |
            v
      Find Latest 10-K
            |
            v
      Download SEC HTML
            |
            v
      Convert HTML to PDF
            |
            v
      Store PDF Locally
            |
            v
      Save Metadata in DB
            |
            v
       Return PDF / File Path
```

### PDF storage

Generated documents are organized by company:

```text
downloads/
├── company_tickers.json
└── 10k_reports/
    ├── Apple_Inc/
    │   └── Apple_Inc_2026-11-03_....pdf
    ├── AMAZON_COM_INC/
    │   └── AMAZON_COM_INC_2026-02-06_....pdf
    └── ...
```

The original SEC HTML is temporary and is deleted after PDF conversion.

Existing PDFs are reused when the same filing has already been processed and its stored file is available.

The `downloads/` directory is runtime storage. It is not intended to be committed to the Git repository.

## 7. CLI Usage

The CLI supports interactive selection and direct command-line execution.

### Run the interactive menu

```bash
docker compose exec api python -m app.cli.main
```

Available companies:

1. Apple
2. Meta
3. Alphabet
4. Amazon
5. Netflix
6. Goldman Sachs
7. All companies
0. Quit

### Download one company's report

```bash
docker compose exec api python -m app.cli.main --company 1
```

### Download all reports

```bash
docker compose exec api python -m app.cli.main --company all
```

The CLI also supports `--company 7` for all companies.

The CLI reports successful downloads and failures separately.

## 8. REST API

The application exposes two main endpoints.

### 8.1 Search companies

**Endpoint:** `GET /companies/search`

Search for companies using a name or ticker symbol.

Example:

```bash
curl "http://localhost:8000/companies/search?q=AAPL"
```

Example response:

```json
[
  {
    "name": "Apple Inc.",
    "ticker": "AAPL",
    "cik": "0000320193"
  }
]
```

### 8.2 Download a company's latest 10-K

**Endpoint:** `POST /filings/download/{cik}`

Downloads the latest original 10-K, converts it to PDF, stores the document, and returns the PDF file directly in the HTTP response.

Example:

```bash
curl -X POST \
  "http://localhost:8000/filings/download/0000320193" \
  -o apple_10k.pdf
```

The company must first be available in the company database. Search for it using the company search endpoint if necessary.

The API reuses an existing PDF when the filing has already been processed and the file is available.

### API documentation and health checks

| Resource | URL |
|---|---|
| API root | http://localhost:8000/ |
| Health check | http://localhost:8000/health |
| Database health | http://localhost:8000/db-health |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## 9. Getting Started

### Prerequisites

- Python 3.14
- Docker
- Docker Compose
- Git

### Clone the repository

```bash
git clone <repository-url>
cd fastapi-docker-app
```

### Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

Update `.env` with your PostgreSQL credentials and SEC contact information:

```env
POSTGRES_USER=fastapi_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=fastapi_db

SEC_USER_AGENT_NAME=SEC10K-DataAutomation
SEC_USER_AGENT_EMAIL=your-name@yourdomain.org
```

Replace the example values with your own credentials and a valid contact email address. The SEC user-agent email must not use the `example.com` placeholder.

Never commit `.env` or real credentials to version control.

### Build and start the application

```bash
docker compose up --build -d
```

Docker Compose starts:

- The FastAPI application, built from the project Dockerfile.
- PostgreSQL 17, with a health check before the API starts.

The Dockerfile installs the Python dependencies and Playwright Chromium required for PDF conversion.

### Check containers

```bash
docker compose ps
```

### View application logs

```bash
docker compose logs -f api
```

### Access the API

Open:

```text
http://localhost:8000/docs
```

### Stop the application

```bash
docker compose down
```

PostgreSQL data is stored in the Docker named volume `postgres_data` and is retained when containers are stopped. Removing the volume explicitly will delete the persisted database data.

## 10. Testing

The project includes automated tests using Pytest.

Run the test suite from the project root:

```bash
pytest -v
```

Run tests with coverage reporting (requires `pytest-cov`):

```bash
pytest --cov=app --cov-report=term-missing
```

### Current test results

- **86 tests passed**
- **100% statement coverage**
- **371 statements covered**

Coverage results reflect the current project test run and may change as the code evolves.

## 11. Development Principles

The project follows these principles:

- Separation of concerns and modular architecture.
- Reusable business logic across multiple interfaces.
- Environment-based configuration.
- Database dependency injection.
- Reliable external API integration.
- Efficient caching and duplicate processing prevention.
- Containerized development and deployment.
- Maintainable and extensible service design.

## 12. License

No license has been selected yet.