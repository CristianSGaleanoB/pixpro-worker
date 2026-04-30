# Digester Service (Worker)

The Digester is a robust background worker responsible for processing raw images uploaded by the frontend. It consumes tasks from RabbitMQ, applies AI enhancements using MediaPipe, and coordinates the storage and notification flow with the backend.

## Architecture

This project strictly follows a **Layered Architecture**. This approach was chosen over flat scripts or hexagonal architecture because it provides an excellent balance of scalability, organization, and a smooth learning curve, while still ensuring high testability for our CI/CD pipelines (targeting >80% coverage).

### Directory Structure

```text
worker/
├── src/
│   ├── handlers/         # Presentation layer: Entry points and event listeners (e.g., RabbitMQ consumers).
│   ├── services/         # Business logic layer: Orchestrates the task flow (upload original -> process -> upload processed -> DB -> notify).
│   ├── core/             # Pure logic: Machine Learning / pure algorithms (e.g., MediaPipe processing).
│   └── infrastructure/   # Adapters/External: Third-party integrations (CDN clients, DB clients, RabbitMQ publishers).
├── pyproject.toml        # Project dependencies (MediaPipe) and package configurations.
└── README.md             # Technical documentation.
```

### Execution Flow

To ensure the separation of concerns, the layers interact as follows:

1. **Handler (`src/handlers/`)** receives the raw image task (binary/base64 payload) from RabbitMQ. It parses the incoming payload and passes the raw data to the corresponding Service.
2. The **Service (`src/services/`)** takes control and defines the steps:
   - It uses an **Infrastructure** client (CDN) to upload the original raw image.
   - It delegates the image manipulation to the **Core** layer (MediaPipe) using the raw data.
   - Once processed, it uses the **Infrastructure** client to upload the new processed image to the CDN.
   - Finally, it uses the **Infrastructure** clients to store the image URLs in the Database and publish a "task completed" event back to RabbitMQ.

By isolating the business logic in `services` and the algorithms in `core`, we can easily mock external dependencies in the `infrastructure` layer to write fast, reliable unit tests.

---

## Setup and Installation

We use the native Python toolchain (`venv`, `pip`, and `setuptools`) to manage dependencies and avoid heavy third-party package managers.

### 1. Create the Virtual Environment
To maintain dependencies isolated, create a virtual environment in the root folder:

```bash
python -m venv venv
```

### 2. Activate the Environment
Depending on your operative system, run the respective command:

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```
*(If you use Command Prompt, run `.\venv\Scripts\activate.bat`)*

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install the Dependencies
Since our dependencies are explicitly declared in the `pyproject.toml`, you can install the project and its requirements natively with `pip`. 

It is recommended to install it in "editable mode" (`-e`) with development dependencies during development:

```bash
pip install -e ".[dev]"
```

After this, MediaPipe, Aio-pika, Pydantic, and any other necessary dependencies will be ready to use.

### 4. Running the Worker

The application provides a CLI entrypoint. Once installed, simply run:

```bash
digester-worker
```

### 5. Running Tests

We use `pytest` for automated testing. To run the test suite:

```bash
pytest tests/
```

---
