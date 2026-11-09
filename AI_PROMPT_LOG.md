# AI Tool Usage and Prompt Log

## Project: SEC 10-K Data Automation

**AI tool used:** ChatGPT by OpenAI
**Purpose:** Requirements clarification, architecture guidance, implementation assistance, debugging, testing, and documentation.

### About this log

This document records selected AI-assisted interactions during project development.

The initial project requirements originated with the developer. AI assistance was used as a supporting tool throughout development. The developer remained responsible for technical decisions, reviewing suggestions, implementing changes, executing commands, and validating the application.

Some entries below are reconstructed summaries of earlier development discussions rather than verbatim transcripts. Future entries will distinguish exact prompts from summarized prompts.

---

## 1. Initial project requirements

**Type:** Developer requirements

**Original request (as summarized by the developer):**

> I wanted to build an API service for SEC 10-K download. It should have both an API service as well as a CLI. The six companies are the priority.

**Initial company scope:**

1. Apple
2. Meta
3. Alphabet
4. Amazon
5. Netflix
6. Goldman Sachs

**Project objectives:**

- Retrieve SEC 10-K annual reports.
- Support both a REST API and a CLI.
- Download the latest original 10-K filings.
- Convert downloaded filing documents into PDFs.
- Store generated documents locally.
- Maintain company and filing metadata.

**AI assistance:** Helped refine requirements and translate the project idea into an implementation plan.

**Developer responsibility:** Defined the project objectives, initial scope, and priority companies.

## 2. Application architecture

**Type:** Architecture guidance
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me structure a Python application using FastAPI, with both REST API and CLI interfaces. I want the business logic to be reusable rather than duplicated between the two interfaces.

**AI assistance:**

- Discussed modular application architecture.
- Suggested separating routers, services, models, schemas, and CLI functionality.
- Explained how API and CLI interfaces could share application services.

**Developer responsibility:** Reviewed the architecture and implemented the project structure.

## 3. SEC EDGAR integration

**Type:** External API integration
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me integrate SEC EDGAR to identify companies using ticker symbols and CIK identifiers, retrieve filing metadata, and find the latest original 10-K while excluding amended 10-K/A filings.

**AI assistance:**

- Explained SEC company ticker data and filing submissions.
- Provided guidance on identifying original 10-K filings.
- Discussed SEC request identification requirements.

**Developer responsibility:** Implemented and tested the SEC integration.

## 4. PDF generation and document storage

**Type:** Document processing
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me implement a PDF generation and storage workflow for SEC 10-K HTML documents using Python and Playwright. Organize generated PDFs by company and clean up temporary HTML files.

**AI assistance:**

- Provided guidance on Playwright and Chromium.
- Discussed HTML-to-PDF conversion.
- Helped structure document storage and cleanup logic.

**Developer responsibility:** Implemented and validated the PDF generation and storage workflow.

## 5. Database integration

**Type:** Database design
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me design SQLAlchemy models for companies and SEC filings using PostgreSQL. Filing records should be associated with companies and store relevant SEC metadata and generated PDF paths.

**AI assistance:**

- Discussed relational database modelling.
- Provided SQLAlchemy integration guidance.
- Helped review database operations.

**Developer responsibility:** Implemented and tested database functionality.

## 6. Docker and application deployment

**Type:** Containerization
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me containerize the FastAPI application and PostgreSQL using Docker and Docker Compose. The application needs Playwright Chromium for PDF conversion, environment-based configuration, and persistent database storage.

**AI assistance:**

- Provided Dockerfile and Docker Compose guidance.
- Discussed container dependencies and configuration.
- Helped troubleshoot container execution.

**Developer responsibility:** Configured and tested the Docker environment.

## 7. Automated testing and debugging

**Type:** Testing and debugging
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Help me develop and debug Pytest tests for API endpoints, CLI execution, SEC integration, PDF generation, storage, and database functionality. I want comprehensive test coverage.

**AI assistance:**

- Helped investigate test failures.
- Suggested test improvements.
- Assisted with debugging and coverage analysis.

**Developer responsibility:** Ran the tests, reviewed failures, applied changes, and verified results.

**Recorded test result at the time of documentation:**

- 86 tests passed.
- 371 statements measured.
- 100% statement coverage.

## 8. Project documentation

**Type:** Technical documentation
**Prompt status:** Reconstructed summary

**Prompt summary:**

> Review and update the README for the SEC 10-K Data Automation project. Ensure it accurately describes the architecture, technology stack, setup, CLI, REST API, Docker configuration, and testing results.

**AI assistance:**

- Reviewed the existing README.
- Helped align documentation with implemented functionality.
- Suggested improvements to setup instructions and project structure.

**Developer responsibility:** Reviewed the documentation for technical accuracy.

---

## Development transparency

AI tools were used as supporting tools during project development for requirements clarification, technical guidance, implementation assistance, debugging, testing, and documentation.

The developer was responsible for project direction, technical decisions, implementation, code review, and validation of the application.

This log presents selected AI-assisted interactions rather than a complete transcript of all development conversations. Reconstructed prompt summaries are identified as such; they are not presented as verbatim prompts.

## Future updates

This log may be updated to include additional significant AI-assisted development activities as the project evolves.