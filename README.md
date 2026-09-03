# AI Food Ordering Agent

A local, assessment-ready AI food ordering application that allows users to interact with a restaurant ordering assistant through a Streamlit UI.

The application supports:

* Natural-language food ordering
* Multiple food items in a single request
* Quantity extraction from numbers and number words
* Menu-item matching and typo-tolerant input
* Menu-related questions
* Order creation and persistence
* RAG-based menu responses
* LangChain tool-calling agent
* Custom database tools
* FastAPI backend
* Streamlit frontend
* SQLite database
* Sales and order dashboard
* Automated tests
* Fully local LLM inference using Ollama

---

# 1. Project Overview

The application follows this architecture:

```text
User
  |
  v
Streamlit Frontend
  |
  v
FastAPI Backend
  |
  v
Order / Intent Processing
  |
  +--------------------------+
  |                          |
  v                          v
Direct Order Parser       LangChain Agent
  |                          |
  |                          +------------------+
  |                                             |
  v                                             v
Custom Order Tool                         RAG / Menu Tools
  |                                             |
  v                                             v
Order Service                              FAISS Index
  |                                             |
  v                                             v
SQLite Database                         Local Embeddings
```

The application does not expose raw SQL access to the LLM.

Database operations are performed through application-owned tools and services.

---

# 2. Main Features

## Natural Language Ordering

The user can enter requests such as:

```text
I want 2 Margherita Pizza, 1 Chicken Burger and 3 Coke
```

The system extracts every requested item and quantity.

It also supports number words:

```text
two Margherita Pizza and one Coke
```

and natural variations such as:

```text
marg pizza
2 pizzas and 3 coke
please give me one chicken burger and two fries
```

The ordering layer is designed to identify multiple items instead of processing only the last item in the request.

---

## Multiple Items in One Order

Example:

```text
2 Margherita Pizza
3 Chicken Burger
2 Coke
```

The complete request is passed to the order tool as one order.

The system validates all requested items before creating the order.

---

## Menu Matching

The system uses the current menu stored in the database.

It can handle common variations and minor spelling mistakes.

For example:

```text
marg pizza
margi pizza
margherita pizza
```

can resolve to:

```text
Margherita Pizza
```

The parser also handles quantities such as:

```text
1
2
3
one
two
three
```

If a request is ambiguous, the system asks the user for clarification instead of guessing.

For example, if the menu contains:

```text
Veg Burger
Chicken Burger
```

and the user enters:

```text
2 burgers
```

the application should ask which burger the user wants.

---

# 3. Technology Stack

## Backend

* Python 3.9+
* FastAPI
* Uvicorn
* SQLAlchemy
* SQLite
* Pydantic
* Pydantic Settings

## AI / Agent

* LangChain
* LangChain Core
* LangChain Ollama
* Ollama
* Local LLM

## RAG

* Sentence Transformers
* Hugging Face embeddings
* FAISS
* LangChain Community

## Frontend

* Streamlit
* Requests

## Testing

* Pytest
* HTTPX

---

# 4. Project Structure

```text
food_order/
│
├── backend/
│   ├── agent/
│   │   ├── agent.py
│   │   ├── prompts.py
│   │   ├── tools.py
│   │   └── __init__.py
│   │
│   ├── api/
│   │   ├── chat.py
│   │   ├── dashboard.py
│   │   ├── menu.py
│   │   ├── orders.py
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── database_in.py
│   │   ├── models.py
│   │   ├── seed.py
│   │   └── __init__.py
│   │
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── menu.py
│   │   ├── order.py
│   │   └── __init__.py
│   │
│   ├── services/
│   │   └── order_service.py
│   │
│   ├── config.py
│   ├── main.py
│   └── __init__.py
│
├── data/
│   ├── menu.json
│   ├── menu_documents/
│   └── faiss_index/
│
├── docs/
│   ├── ACCEPTANCE_CHECKLIST.md
│   ├── AGENT.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── RAG.md
│   └── TESTING.md
│
├── frontend/
│   └── app.py
│
├── scripts/
│   ├── init_db.py
│   └── ingest_data.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_dashboard.py
│   ├── test_menu_resolution.py
│   └── test_orders.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 5. Prerequisites

Before running the application, install the following:

* Python 3.9 or higher
* Ollama
* Git (optional, but recommended)

Python 3.11+ is recommended.

---

# 6. Install Ollama

Download and install Ollama from the official website:

https://ollama.com/

After installation, make sure Ollama is running.

You can verify that Ollama is available by running:

```bash
ollama --version
```

You should see the installed Ollama version.

---

# 7. Download / Pull the Ollama Model

This project is configured by default to use:

```text
llama3.2:3b
```

Pull the model:

```bash
ollama pull llama3.2:3b
```

This may take some time depending on your internet connection.

After the model has been downloaded, you can verify that it exists locally:

```bash
ollama list
```

You should see something similar to:

```text
NAME            ID              SIZE
llama3.2:3b     ...             ...
```

---

# 8. Verify the Ollama API

This step is important.

Before starting the FastAPI application, verify that the Ollama server is running.

Open a terminal and run:

```bash
curl http://localhost:11434/api/tags
```

If Ollama is running correctly, the API should return JSON containing the locally available models.

For example:

```json
{
  "models": [
    {
      "name": "llama3.2:3b"
    }
  ]
}
```

The exact response may contain additional fields.

The important point is that the response should be successful and the pulled model should appear in the list.

---

## If the Ollama API Does Not Respond

If you receive an error such as:

```text
Could not connect to server
```

make sure Ollama is running.

You can also start Ollama manually:

```bash
ollama serve
```

Keep that terminal running.

Then open another terminal and run:

```bash
curl http://localhost:11434/api/tags
```

If the model appears in the response, Ollama is ready.

---

# 9. Clone / Open the Project

If you received the project as a ZIP file, extract it.

Then open a terminal inside the project directory:

```bash
cd food_order
```

You should see files such as:

```text
README.md
requirements.txt
backend/
frontend/
scripts/
tests/
data/
```

---

# 10. Create a Python Virtual Environment

## Windows

Run:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

After activation, your terminal should show something similar to:

```text
(.venv)
```

---

## Linux / macOS

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

# 11. Install Python Dependencies

Make sure the virtual environment is activated.

Then run:

```bash
pip install -r requirements.txt
```

This installs the required packages including:

* FastAPI
* Uvicorn
* Streamlit
* LangChain
* LangChain Ollama
* SQLAlchemy
* Sentence Transformers
* FAISS
* Pytest
* HTTPX

---

# 12. Configure Environment Variables

The project contains:

```text
.env.example
```

Create your local `.env` file from it.

## Windows CMD

```bash
copy .env.example .env
```

## Windows PowerShell

```powershell
Copy-Item .env.example .env
```

## Linux / macOS

```bash
cp .env.example .env
```

The default configuration is:

```env
APP_NAME=Local AI Food Ordering Agent
DATABASE_URL=sqlite:///./food_orders.db

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

FAISS_INDEX_DIR=data/faiss_index

API_URL=http://127.0.0.1:8000
```

The default configuration uses Ollama locally and does not require a paid LLM API.

---

# 13. Initialize the Database

Run:

```bash
python scripts/init_db.py
```

This initializes the SQLite database and required database structures.

The database file is:

```text
food_orders.db
```

The database initialization is designed to be safe to run again.

---

# 14. Load / Seed the Menu

Run:

```bash
python scripts/ingest_data.py
```

This prepares the menu data and the RAG index.

The menu source is:

```text
data/menu.json
```

The FAISS index is stored under:

```text
data/faiss_index/
```

---

# 15. Run the FastAPI Backend

Start the backend:

```bash
uvicorn backend.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

---

# 16. Check Backend Health

Open:

```text
http://127.0.0.1:8000/health
```

You should receive a successful health response.

You can also open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

The Swagger UI allows you to inspect and test the available API endpoints.

---

# 17. Run the Streamlit Frontend

Keep the FastAPI terminal running.

Open a second terminal.

Activate the virtual environment again if required.

Then run:

```bash
streamlit run frontend/app.py
```

Streamlit will display a local URL in the terminal.

Open that URL in your browser.

---

# 18. Recommended Startup Order

For a fresh setup, the recommended order is:

## Terminal 1 — Ollama

Make sure Ollama is running.

If required:

```bash
ollama serve
```

---

## Terminal 2 — Verify Ollama

Run:

```bash
curl http://localhost:11434/api/tags
```

Confirm that:

```text
llama3.2:3b
```

is present.

---

## Terminal 3 — FastAPI

From the project root:

```bash
uvicorn backend.main:app --reload
```

---

## Terminal 4 — Streamlit

From the project root:

```bash
streamlit run frontend/app.py
```

---

# 19. Example Conversations

---

## Multiple Items

```text
I want 2 Margherita Pizza, 1 Chicken Burger and 3 Coke
```

The system should preserve all requested items and quantities.

---

## Multiple Items With Natural Language

```text
Please give me three chicken burgers, two pizzas and one coke.
```

The application attempts to identify each item and quantity.

---

# 20. API Endpoints

The backend exposes the following main endpoints:

```text
GET  /health
GET  /menu
POST /chat
POST /orders
GET  /orders/{order_id}
GET  /dashboard/summary
```

Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# 21. Database

The project uses SQLite with SQLAlchemy.

The default database is:

```text
food_orders.db
```

The database contains the menu and order-related information required by the application.

The application uses application-owned services for database operations.

The LLM does not receive direct SQL access.

---

# 22. Custom Database Tools

The agent uses explicit application-owned tools instead of exposing a raw SQL agent.

Examples include:

```text
search_menu
get_menu
create_food_order
get_order
get_sales_summary
```

The tools are implemented in:

```text
backend/agent/tools.py
```

They delegate database operations to the application services.

This keeps the database access controlled and predictable.

---

# 23. Order Validation

Orders are validated before being persisted.

The order flow is approximately:

```text
User Request
     |
     v
Extract all items and quantities
     |
     v
Resolve items against menu
     |
     v
Validate requested items
     |
     v
Create order
     |
     v
Persist order in SQLite
```

If an item cannot be confidently resolved or validated, the system should not create a partial order.

This prevents a request such as:

```text
2 burger
3 pizza
2 coke
```

from becoming an order containing only:

```text
2 coke
```

---

# 24. RAG

The project uses Retrieval-Augmented Generation for menu-grounded responses.

The RAG pipeline is:

```text
Menu Data
   |
   v
Documents
   |
   v
Local Embeddings
   |
   v
FAISS
   |
   v
Relevant Menu Context
   |
   v
LLM Response
```

The embedding model is:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The FAISS index is stored in:

```text
data/faiss_index/
```

RAG-related implementation can be found in:

```text
backend/rag/
```

Additional documentation is available in:

```text
docs/RAG.md
```

---

# 25. Agent

The LangChain agent is implemented under:

```text
backend/agent/
```

Important files:

```text
backend/agent/agent.py
backend/agent/prompts.py
backend/agent/tools.py
```

The agent can call application-owned tools rather than directly interacting with SQL.

The system prompt and agent behavior are defined in:

```text
backend/agent/prompts.py
```

---

# 26. Natural Language Order Processing

The order-processing layer is designed to handle variations in user input.

Examples include:

```text
2 coke
two coke
2 cokes
two cokes
```

and:

```text
marg pizza
margi pizza
margherita pizza
```

The system attempts to normalize:

* Number words
* Numeric quantities
* Basic plurals
* Minor spelling variations
* Menu aliases
* Multiple items in one request

The parser uses the current database menu rather than maintaining a completely hard-coded list of products.

This allows new menu items to be discovered without rewriting the entire order parser.

---

# 27. Dashboard

The project includes a Streamlit dashboard for sales/order information.

The backend dashboard endpoint is:

```text
GET /dashboard/summary
```

The dashboard can provide:

* Overall sales
* User-wise information
* Individual order breakdown
* Best-selling information

---

# 28. Troubleshooting

## Ollama Connection Error

If you see an error indicating that Ollama cannot be reached:

```text
Connection refused
```

check:

```bash
curl http://localhost:11434/api/tags
```

If it fails, start Ollama:

```bash
ollama serve
```

Then retry:

```bash
curl http://localhost:11434/api/tags
```

---

## Model Not Found

If the application cannot find:

```text
llama3.2:3b
```

run:

```bash
ollama list
```

If it is not present, run:

```bash
ollama pull llama3.2:3b
```

Then verify again:

```bash
curl http://localhost:11434/api/tags
```

---

## FastAPI Does Not Start

Make sure the virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

Then run:

```bash
uvicorn backend.main:app --reload
```

Make sure you execute the command from the project root:

```text
food_order/
```

---

## Streamlit Does Not Start

Make sure Streamlit is installed:

```bash
pip install -r requirements.txt
```

Then:

```bash
streamlit run frontend/app.py
```

---

## FAISS / Embedding Error

Run the data ingestion process again:

```bash
python scripts/ingest_data.py
```

This recreates/prepares the menu retrieval data.

---

## Database Issues

Re-run:

```bash
python scripts/init_db.py
```

Then:

```bash
python scripts/ingest_data.py
```

If you are intentionally starting from a completely fresh local environment, remove the local SQLite database before reinitializing it.

---

# 29. Important Notes About Local LLM Usage

This project is designed to run the primary LLM locally through Ollama.

Default configuration:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

No paid LLM API is required for the default Ollama configuration.

The model must be downloaded separately:

```bash
ollama pull llama3.2:3b
```

and Ollama must be running before using the AI functionality.

Always verify the Ollama API before troubleshooting the application itself:

```bash
curl http://localhost:11434/api/tags
```

---

# 30. Security / Environment Variables

Do not commit secrets or local environment files.

Do not commit:

```text
.env
```

Do not put API keys directly into Python source code.

The `.gitignore` should be used to prevent accidental commits of local configuration and generated files.

---

# 31. GitHub Setup

Initialize Git:

```bash
git init
```

Add files:

```bash
git add .
```

Commit:

```bash
git commit -m "Build local AI food ordering agent"
```

Rename the branch:

```bash
git branch -M main
```

Add your GitHub repository:

```bash
git remote add origin https://github.com/YOUR_USERNAME/food-ordering-agent.git
```

Push:

```bash
git push -u origin main
```

Do not commit:

```text
.env
food_orders.db
generated FAISS files
.venv/
__pycache__/
```

---

# 32. Assessment Requirements

The implementation is designed to satisfy the following requirements:

* AI chatbot for food ordering
* Multiple items in a single order
* Natural-language input
* Quantity extraction
* Menu validation
* Order persistence
* RAG for menu-grounded responses
* LangChain agent
* Custom database tools
* FastAPI backend
* Streamlit frontend
* Dashboard
* Automated tests
* Documentation
* Local LLM inference

The project does not use the directly provided SQL agent for database interaction.

Database operations are implemented through application-owned tools and services.

---

# 33. Recommended Complete Setup

For a new machine, the shortest complete setup is:

## Step 1 — Install Ollama

Install Ollama from:

```text
https://ollama.com/
```

---

## Step 2 — Pull the model

```bash
ollama pull llama3.2:3b
```

---

## Step 3 — Verify the model

```bash
ollama list
```

---

## Step 4 — Verify Ollama API

```bash
curl http://localhost:11434/api/tags
```

Make sure the response contains:

```text
llama3.2:3b
```

---

## Step 5 — Open the project

```bash
cd food_order
```

---

## Step 6 — Create virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Step 7 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 8 — Create `.env`

Windows:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

---

## Step 9 — Initialize database

```bash
python scripts/init_db.py
```

---

## Step 10 — Build / update RAG data

```bash
python scripts/ingest_data.py
```

---

## Step 11 — Start FastAPI

```bash
uvicorn backend.main:app --reload
```

---

## Step 12 — Start Streamlit

Open another terminal:

```bash
streamlit run frontend/app.py
```

---

## Step 13 — Open the application

Open the Streamlit URL shown in the terminal.

---

# 34. Quick Verification Checklist

Before considering the application ready, verify:

```text
[ ] Python installed
[ ] Virtual environment created
[ ] requirements.txt installed
[ ] Ollama installed
[ ] llama3.2:3b pulled
[ ] ollama list shows llama3.2:3b
[ ] curl http://localhost:11434/api/tags works
[ ] .env created
[ ] Database initialized
[ ] RAG index generated
[ ] FastAPI starts successfully
[ ] /health works
[ ] /docs opens
[ ] Streamlit starts
[ ] Menu loads
[ ] Single-item order works
[ ] Multiple-item order works
[ ] Number words work
[ ] Basic typos work
[ ] Ambiguous products request clarification
[ ] Order is persisted
[ ] Dashboard works
[ ] pytest passes
```

---

# 35. Useful Commands Summary

### Activate environment — Windows

```bash
.venv\Scripts\activate
```

### Activate environment — Linux/macOS

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Pull Ollama model

```bash
ollama pull llama3.2:3b
```

### Check Ollama models

```bash
ollama list
```

### Check Ollama API

```bash
curl http://localhost:11434/api/tags
```

### Start Ollama manually

```bash
ollama serve
```

### Initialize database

```bash
python scripts/init_db.py
```

### Build RAG index

```bash
python scripts/ingest_data.py
```

### Start FastAPI

```bash
uvicorn backend.main:app --reload
```

### Start Streamlit

```bash
streamlit run frontend/app.py
```

### Run tests

```bash
pytest -v
```

---

# 36. Additional Documentation

More detailed technical documentation is available in:

```text
docs/ACCEPTANCE_CHECKLIST.md
docs/AGENT.md
docs/ARCHITECTURE.md
docs/DATABASE.md
docs/RAG.md
docs/TESTING.md
```

These documents provide additional information about the implementation and design decisions.

---

# 37. Final Application Flow

The complete application flow is:

```text
                    USER
                      |
                      v
              STREAMLIT FRONTEND
                      |
                      v
                 FASTAPI API
                      |
                      v
             REQUEST PROCESSING
                      |
             +--------+--------+
             |                 |
             v                 v
      DIRECT ORDER         LANGCHAIN
        PARSER              AGENT
             |                 |
             |                 +--------+
             |                          |
             v                          v
       MENU MATCHING                RAG / TOOLS
             |                          |
             v                          v
       ORDER VALIDATION          MENU / DATABASE
             |                          |
             +------------+-------------+
                          |
                          v
                    CREATE ORDER
                          |
                          v
                    SQLITE DATABASE
                          |
                          v
                   USER RESPONSE
```

The system is designed so that a user's complete request is understood before an order is created, helping prevent partial or incorrect orders.

---
