<div align="center">

# 🚀 EasyRAG - A Lightweight Local Knowledge Base Enhancement System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Stars](https://img.shields.io/github/stars/BetaStreetOmnis/EasyRAG?style=social)](https://github.com/BetaStreetOmnis/EasyRAG)

[中文](README.md) | [English](README_EN.md)

**🎯 One-Click Deployment · 🔒 Local & Private · 🚀 High-Performance Retrieval · 🤖 Multi-Model Support**

</div>

---

## 📖 Introduction

**EasyRAG** is a professional local knowledge base construction and retrieval system, focused on providing high-performance knowledge retrieval services for AI applications. It integrates advanced hybrid retrieval technology and a variety of Embedding models, helping developers quickly build and manage local knowledge bases and provide accurate knowledge retrieval APIs for various AI applications.

### ✨ Core Features
- 🔒 **Fully Local Deployment** - Ensures data security and privacy, no need to worry about data leaks.
- 🎯 **Hybrid Search Technology** - Vector retrieval + keyword retrieval, improving retrieval accuracy by 40%.
- 🤖 **Multi-Model Support** - Supports 20+ Embedding models, offering flexibility to choose the optimal solution.
- 📚 **Multiple Document Formats** - Supports 10+ formats including PDF, Word, Markdown, TXT, etc.
- 🖥️ **Integrated Web Interface** - No extra startup needed, accessible through the API service port.
- ⚡ **High-Performance API** - Millisecond-level retrieval response, supporting knowledge bases with millions of documents.
- 🔗 **Ecosystem Integration** - Provides knowledge retrieval services for AI applications like [DocuGen](https://github.com/BetaStreetOmnis/DocuGen).

### 🏆 Performance Comparison

| Feature | EasyRAG | Traditional RAG | Online Services |
|---|---|---|---|
| 🔒 Data Security | ✅ Fully Local | ✅ Local | ❌ Cloud-based |
| 🚀 Retrieval Speed | ⚡ <100ms | 🐌 >500ms | 🌐 Network Latency |
| 💰 Cost of Use | 💚 Free | 💚 Free | 💸 Pay-as-you-go |
| 🎯 Retrieval Accuracy | 🎯 95%+ | 📊 80%+ | 📊 85%+ |
| 🔧 Customization | ✅ Fully Controllable | ✅ Controllable | ❌ Limited |
| 📚 Document Support | 📄 10+ Formats | 📄 Basic Formats | 📄 Limited Formats |

---

## 🌟 Ecosystem

<div align="center">

```mermaid
graph LR
    A[📚 EasyRAG<br/>Knowledge Base System] --> B[🖋️ DocuGen<br/>Document Generation]
    A --> C[💬 Chatbot]
    A --> D[🔍 Search Engine]
    A --> E[📊 Data Analytics]
    
    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
```

</div>

### 🔗 Related Projects

| Project | Description | Link | Status |
|---|---|---|---|
| 🖋️ **DocuGen** | AI-powered document generation system that automatically creates professional documents based on the EasyRAG knowledge base. | [GitHub](https://github.com/BetaStreetOmnis/DocuGen) | ✅ Available |
| 💬 **ChatBot** | Intelligent conversational robot (planned). | - | 🚧 In Development |
| 📊 **Analytics** | Knowledge base analysis tool (planned). | - | 📋 Planned |

---

## 🖼️ Interface Preview

<table>
<tr>
<td width="50%">

### 🏠 Main Interface
![Main Interface](images/main_interface.png)
*A clean and intuitive user interface.*

</td>
<td width="50%">

### 📤 File Upload
![File Upload](images/file_upload.png)
*Supports drag-and-drop for batch uploads.*

</td>
</tr>
<tr>
<td width="50%">

### 🔍 Knowledge Base Retrieval
![Knowledge Base Retrieval](images/search_interface.png)
*Real-time search result preview.*

</td>
<td width="50%">

<!-- ### 📊 API Documentation
![API Documentation](images/api_docs.png)
*Complete RESTful API documentation.* -->

</td>
</tr>
</table>

---

## 🎯 Main Features

<table>
<tr>
<td width="50%">

### 📚 Knowledge Base Management
- ✅ **CRUD Operations** - Create, update, and delete knowledge bases.
- 📄 **Multi-Format Support** - PDF, Word, Markdown, TXT, etc.
- 🖼️ **OCR Recognition** - Extracts text from images, supporting Chinese and English.
- 🔄 **Smart Chunking** - 4 chunking strategies to adapt to different document types.
- 📊 **Statistical Analysis** - Document count, character statistics, retrieval popularity.

</td>
<td width="50%">

### 🔍 Advanced Retrieval Strategies
- 🎯 **Hybrid Search** - Vector + BM25, improving accuracy by 40%.
- 🏆 **Intelligent Reranking** - Secondary sorting to optimize relevance.
- 📊 **Parameter Tuning** - Adjustable Top-K and similarity thresholds.
- 🎛️ **Strategy Switching** - Semantic/keyword/hybrid modes.
- 📈 **Retrieval Analysis** - Result scoring, time consumption statistics.

</td>
</tr>
<tr>
<td width="50%">

### 🤖 Flexible Model Support
- 🏠 **Local Models** - bge-m3, bge-large-zh, etc.
- 🌐 **API Models** - OpenAI, Azure, and other Embedding services.
- ⚙️ **Parameter Adjustment** - Dimensions, batch size, etc.
- 🔄 **Hot-Swapping** - Switch models without restarting.
- 💾 **Model Management** - Automatic download, caching, and updates.

</td>
<td width="50%">

### 🔗 API Service
- 🚀 **RESTful API** - Standardized HTTP interface.
- 📊 **Batch Retrieval** - Supports batch queries to optimize performance.
- 🔍 **Multiple Retrieval Modes** - Semantic/keyword/hybrid retrieval.
- 📈 **Performance Monitoring** - Real-time monitoring of retrieval performance metrics.
- 🔧 **Flexible Configuration** - Supports dynamic adjustment of retrieval parameters.

</td>
</tr>
</table>

### 🕸️ Knowledge Graph API (Experimental)

Performs LLM-based entity and relation extraction on text already stored in a knowledge base, then builds and queries a persistent knowledge graph in SQLite.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/kb/graph/{kb_name}/extract` | Build a graph from knowledge base text; `max_chunks` defaults to `0` (all chunks); returns `404` if the knowledge base does not exist and `400` if no vector collection exists |
| `GET` | `/kb/graph/{kb_name}` | Get the complete graph; returns `404` if the graph does not exist |
| `GET` | `/kb/graph/{kb_name}/entities` | Query entities with pagination; supports `type`, `name`, `limit` (`1-500`, default `100`), and `offset` |
| `GET` | `/kb/graph/{kb_name}/entities/{entity_id}` | Get entity details and its one-degree relationships; supports `direction=in|out|both` (default `both`) |
| `GET` | `/kb/graph/{kb_name}/relations` | Query relations with pagination; supports `entity_id`, `type`, `limit`, and `offset` |
| `DELETE` | `/kb/graph/{kb_name}` | Delete the complete graph; returns `404` if the graph does not exist |

> 💡 When deleting a knowledge base, `DELETE /kb/delete/{kb_name}` makes a best-effort attempt to clean up the graph, and its response includes the `graph_deleted` field.

```bash
# 1️⃣ Build the knowledge graph (max_chunks=0 means full)
curl -X POST "http://localhost:8028/kb/graph/my_kb/extract?max_chunks=0"

# 2️⃣ Query graph entities with pagination
curl "http://localhost:8028/kb/graph/my_kb/entities?limit=20&offset=0"

# 3️⃣ Delete the complete graph for a specified knowledge base
curl -X DELETE "http://localhost:8028/kb/graph/my_kb"
```

#### 📋 Response Models & OpenAPI Examples

Graph endpoint return values are strongly typed by 9 Pydantic response models:

| Response Model | Purpose |
|----------------|---------|
| `GraphEntityResponse` / `GraphRelationResponse` | A single entity / relation |
| `GraphDataResponse` / `GraphDeleteResponse` | A complete graph / deletion result |
| `GraphEntityListResponse` / `GraphRelationListResponse` | An entity / relation list |
| `GraphEntityDetailResponse` | Entity details and its one-degree relationships |
| `GraphBuildStats` / `GraphBuildResponse` | Build statistics / build result |

After starting the service, Swagger UI (`/docs`) shows each endpoint's automatically generated Schema and a realistic Chinese "Example Value"; the raw Schema is available from `/openapi.json`. Example values are for documentation display only and do not affect runtime serialization behavior.

---

### 📋 API Endpoint Reference

The following table covers all 28 current public endpoints. Interactive documentation is available at `/docs` (Swagger UI), and the machine-readable schema is available at `/openapi.json`. Endpoints with OpenAPI tags are grouped according to their Swagger groups.

#### 🗂️ Knowledge Base Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/kb/create` | Create a new knowledge base |
| `GET` | `/kb/list` | List all knowledge bases |
| `GET` | `/kb/info/{kb_name}` | Get information about a specified knowledge base |
| `DELETE` | `/kb/delete/{kb_name}` | Delete a specified knowledge base; performs best-effort cleanup of its knowledge graph, and the response includes a `graph_deleted` field |
| `GET` | `/kb/progress/{task_id}` | Get the processing progress of a task |
| `POST` | `/kb/upload` | Upload a file to a knowledge base |
| `POST` | `/kb/fix_dimension/{kb_name}` | Fix a dimension mismatch in a knowledge base |
| `POST` | `/kb/set_importance` | Set a file's importance coefficient |

#### 📄 Files & Document Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/kb/files/{kb_name}` | Get all files in a knowledge base |
| `GET` | `/kb/file/{kb_name}/{file_name}` | Get detailed information about a specific file in a knowledge base |
| `DELETE` | `/kb/file/{kb_name}/{file_name}` | Delete a specified file from a knowledge base |
| `POST` | `/kb/replace_file` | Replace a file in a knowledge base |
| `POST` | `/kb/delete_documents` | Delete documents from a knowledge base based on filter conditions |

#### 🔎 Retrieval

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/kb/search` | Search content in a knowledge base |
| `POST` | `/web/search` | Use You.com web search as an external retrieval source; gracefully degrades when the API key is not configured or the search fails |

#### 🧰 Tools

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/chunker/methods` | Get all available chunking methods |
| `POST` | `/extract_text_from_file` | Extract text from a file without chunking |

#### 🕸️ Knowledge Graph · OpenAPI group `knowledge-graph`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/kb/graph/{kb_name}/extract` | Build a knowledge graph from knowledge base text; see the Knowledge Graph API section above |
| `GET` | `/kb/graph/{kb_name}` | Get the complete graph for a specified knowledge base; see the Knowledge Graph API section above |
| `GET` | `/kb/graph/{kb_name}/entities` | Query graph entities with pagination; see the Knowledge Graph API section above |
| `GET` | `/kb/graph/{kb_name}/entities/{entity_id}` | Query entity details and its one-degree relationships; see the Knowledge Graph API section above |
| `GET` | `/kb/graph/{kb_name}/relations` | Query graph relations with pagination; see the Knowledge Graph API section above |
| `DELETE` | `/kb/graph/{kb_name}` | Delete the complete graph for a specified knowledge base; see the Knowledge Graph API section above |

#### 🧠 Session Memory · OpenAPI group `session`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/kb/session/history/{kb_name}/{session_id}` | Query server-side session history; see the Server-side Session Storage section below |
| `DELETE` | `/kb/session/history/{kb_name}/{session_id}` | Clear server-side session history; see the Server-side Session Storage section below |
| `GET` | `/kb/session/stats` | Query server-side session storage statistics; see the Server-side Session Storage section below |

#### 💬 Chat · OpenAPI group `chat`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/kb/chat` | Chat with a knowledge base |
| `POST` | `/kb/chat_stream` | Chat with a knowledge base (streaming responses) |

> 💡 For the latest endpoint changes, `/docs` and `/openapi.json` are the source of truth.

---

## 💻 System Requirements

| Item | Minimum | Recommended | High Performance |
|---|---|---|---|
| 🖥️ **OS** | Windows 10/Linux/macOS | - | - |
| 🐍 **Python** | Python 3.9+ | Python 3.10+ | Python 3.11+ |
| 💾 **Memory** | 8GB | 16GB | 32GB+ |
| 💿 **Disk Space** | 10GB | 50GB | 100GB+ |
| 🎮 **GPU** | Optional | GTX 1060+ | RTX 4090+ |
| 🌐 **Network** | Required for initial model download | - | - |

> 💡 **Tip**: Using Docker can avoid most environment configuration issues.

---

## 🚀 Quick Start

### 📋 Deployment Overview

<div align="center">

```mermaid
graph TD
    A[🎯 Choose Deployment Method] --> B[🐳 Docker Deployment<br/>⭐ Recommended for Beginners]
    A --> C[📜 Script Deployment<br/>⭐ Recommended for Advanced Users]
    A --> D[🔧 Manual Deployment<br/>⭐ Recommended for Experts]
    
    B --> E[docker-compose up -d]
    C --> F[1️⃣ Run deploy script]
    D --> G[1️⃣ Create virtual environment]
    
    F --> H[2️⃣ Run start script]
    G --> I[2️⃣ Install dependencies]
    
    H --> J[🌐 Access Web Interface]
    I --> K[3️⃣ Start the service]
    E --> J
    K --> J
    
    J --> L[🎉 Start Using!]
    
    style A fill:#e1f5fe
    style B fill:#c8e6c9
    style C fill:#fff3e0
    style D fill:#fce4ec
    style L fill:#f3e5f5
```

</div>

---

### 🐳 Method 1: Docker Deployment (⭐Recommended)

```bash
# 1️⃣ Make sure Docker is installed
# 2️⃣ Clone the project locally
git clone https://github.com/BetaStreetOmnis/EasyRAG.git
cd EasyRAG

# 3️⃣ Build the Docker image
sudo docker build -t easyrag .

# 4️⃣ Run the Docker container
# Note: Please modify the host paths in the -v parameters according to your system.
# For example, replace /home/EasyRAG/data_from_docker with your actual path.
docker run -d \
-p 80:80 \
-p 8028:8028 \
-v /home/EasyRAG/data_from_docker/data:/data \
-v /home/EasyRAG/data_from_docker/db:/app/db \
-v /home/EasyRAG/data_from_docker/logs:/app/logs \
-v /home/EasyRAG/data_from_docker/models_file:/app/models_file \
-v /home/EasyRAG/data_from_docker/files:/app/files \
--name easyrag-app \
--restart always \
easyrag:latest

# 5️⃣ Access the service
# Open in browser: http://localhost:8028
```

### 📜 Method 2: Script-based Automatic Deployment (⭐Recommended for Beginners)

#### 🪟 For Windows Users

```cmd
# Step 1: Deploy the environment (automatically installs Python, creates virtual environment, installs dependencies)
Double-click deploy.bat
# Or use the command line: deploy.bat

# Step 2: Start the service (activates environment, starts the service)
Double-click start.bat  
# Or use the command line: start.bat
```

#### 🐧 For Linux/macOS Users

```bash
# Step 1: Add execution permissions
chmod +x deploy.sh start.sh

# Step 2: Deploy the environment
./deploy.sh

# Step 3: Start the service
./start.sh
```

### 🔧 Method 3: Manual Deployment (For Advanced Users)

<details>
<summary>📖 Click to expand detailed steps</summary>

```bash
# 1️⃣ Clone the project
git clone https://github.com/BetaStreetOmnis/EasyRAG.git
cd EasyRAG

# 2️⃣ Create a virtual environment
python -m venv py_env

# 3️⃣ Activate the virtual environment
# Windows:
py_env\Scripts\activate
# Linux/Mac:
source py_env/bin/activate

# 4️⃣ Install dependencies
# CPU version (for most users):
pip install -r requirements_cpu.txt

# GPU version (if you have an NVIDIA graphics card):
pip install -r requirements_gpu.txt

# 5️⃣ Create a configuration file
cp .env.example .env
# Edit the .env file to configure model paths, etc.

# 6️⃣ Start the service
python app.py    # Starts the backend API and frontend UI service (port 8028)
```

</details>

---

## 🎯 Deployment Process Explained

### 📋 Step 1: Environment Deployment (Deploy)

<table>
<tr>
<td width="33%">

#### 🐳 Docker Method
```bash
docker-compose up --build -d
```
✅ **Advantages**
- 🚀 One-click completion of all configurations
- 📦 Fully isolated environment
- 🔄 Supports automatic restart
- 🛡️ Best stability guarantee

**⏱️ Deployment Time**: ~5 minutes

</td>
<td width="33%">

#### 🪟 Windows Script
```cmd
deploy.bat
```
✅ **Automation Features**
- 🔍 Smart detection of Python environment
- 📦 Automatic creation of virtual environment
- 📥 Batch installation of all dependencies
- 🤖 Automatic download of model files

**⏱️ Deployment Time**: ~10 minutes

</td>
<td width="33%">

#### 🐧 Linux/macOS Script
```bash
./deploy.sh
```
✅ **Smart Features**
- 🔧 Automatic system environment detection
- 📋 Smart installation of dependencies
- 🔐 Automatic permission configuration
- ⚙️ Automatic service preparation

**⏱️ Deployment Time**: ~8 minutes

</td>
</tr>
</table>

### 🚀 Step 2: Service Startup (Start)

<table>
<tr>
<td width="50%">

#### 🪟 Windows Startup
```cmd
start.bat
```
🎯 **Startup Process**
- 🔌 Automatically activates Python virtual environment
- 📋 Loads .env configuration file
- 🚀 Starts the Web service (API and UI)
- 🎉 Automatically opens the browser page

**⏱️ Startup Time**: ~30 seconds

</td>
<td width="50%">

#### 🐧 Linux/macOS Startup
```bash
./start.sh
```
🎯 **Startup Features**
- 🔌 Smart activation of virtual environment
- 📋 Automatic loading of configuration file
- 🚀 Starts the knowledge base system in the background
- 🎉 Colored terminal status output
- 📊 Real-time display of service status

**⏱️ Startup Time**: ~20 seconds

</td>
</tr>
</table>

---

## 🌐 Accessing the Service

Once deployed, you can access the service by visiting the following address in your browser:

<div align="center">

| Service Name | Access URL | Description |
|---|---|---|
| 🌐 **EasyRAG Service** | [`http://localhost:8028`](http://localhost:8028) | Knowledge Base Management Interface and API |

</div>

> 💡 **Tip**: If the port is occupied, you can modify the port configuration in the `.env` file.

---

## 📖 Usage Instructions

### 🏗️ Creating a Knowledge Base

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant W as 🌐 Web Interface
    participant A as 🔧 API Service
    participant D as 💾 Database
    
    U->>W: 1. Access Knowledge Base Management
    W->>U: 2. Display creation form
    U->>W: 3. Enter knowledge base information
    W->>A: 4. Submit creation request
    A->>D: 5. Create knowledge base record
    A->>A: 6. Initialize vector index
    A->>W: 7. Return creation result
    W->>U: 8. Display creation success
```

**Detailed Steps**:
1. 🌐 Visit the Web Interface → 📚 Click on the "Knowledge Base Management" tab
2. ➕ Click the "Create Knowledge Base" button → 📝 Enter the knowledge base name and description
3. ⚙️ Select an Embedding model (Recommended: gte-large-zh)
4. 🧩 Choose a chunking strategy (depends on the document type)
5. 📤 Upload document files (supports drag-and-drop for batch uploads)
6. ⏳ Wait for the system to automatically process and build the vector index
7. ✅ Creation complete, ready for API retrieval

### 🔍 API Retrieval Calls

**Basic Retrieval Example**:
```python
import requests

# Retrieval API call
response = requests.post("http://localhost:8028/search", json={
    "knowledge_base_id": "your_kb_id",
    "query": "your query question",
    "top_k": 5,
    "search_mode": "hybrid"  # vector/keyword/hybrid
})

results = response.json()
for result in results["documents"]:
    print(f"Relevance: {result['score']}")
    print(f"Content: {result['content']}")
```

**Integration Example with DocuGen**:
```python
# DocuGen calls EasyRAG for knowledge retrieval
def get_knowledge_context(topic):
    response = requests.post("http://localhost:8028/search", json={
        "knowledge_base_id": "document_kb",
        "query": topic,
        "top_k": 10,
        "search_mode": "hybrid"
    })
    return response.json()["documents"]

# Generate a document based on retrieval results
context = get_knowledge_context("AI development trends")
# Pass to DocuGen for document generation...
```

**Web search (You.com external retriever)**:
```python
import requests

# External retrieval, independent of the local KB; requires YDC_API_KEY.
response = requests.post("http://localhost:8028/web/search", json={
    "query": "latest retrieval-augmented generation research",
    "top_k": 5
})

data = response.json()          # same shape as /kb/search
for item in data["data"]:
    print(f"score: {item['score']}  source: {item['metadata']['url']}")
    print(item["text"])
```
> Without `YDC_API_KEY`, the endpoint returns `{"status": "success", "message": "...联网检索未启用", "data": []}` and other features are unaffected.
> Do not commit your real key to the repo; keep it in an untracked environment variable or local `.env`.

### Conversation History Windowing

- By default, the server retains only the last 10 complete conversation turns and truncates any individual message longer than 8000 characters.
- Filtering, pairing, and windowing are handled consistently by `trim_history()` in `core/memory/history_window.py`.
- Both `/kb/chat` and `/kb/chat_stream` use this behavior, preventing model prompts from growing indefinitely during long conversations.
- The optional request fields `history_max_turns` (1-100) and `history_max_chars` (100-100000) override the number of retained turns and the maximum length of an individual message, respectively.
- When these fields are omitted, the default values remain 10 turns and 8000 characters.

### Server-side Session Storage (Experimental)

- `core/memory/session_store.py` provides a thread-safe, in-memory session store.
- It includes LRU session eviction and a per-session message limit; data is not retained after the process restarts.
- `/kb/chat` and `/kb/chat_stream` accept an optional `session_id` (1-128 characters), with history isolated by `kb_name + session_id`.
- When `session_id` is provided, the server-side session is the single source of truth: the request body's `history` is ignored, and the history-window parameters are also applied when it is read.
- The current turn's `user` and final `assistant` messages are appended only after the request completes successfully; failures, exceptions, and interrupted streams are not written.
- When `session_id` is omitted or set to `null`, the original client-supplied `history` behavior is fully preserved.
- Session data exists only in the memory of the current API process and is lost on restart; this capability is currently experimental.
- `GET /kb/session/history/{kb_name}/{session_id}` returns the session history and returns an empty list when the session does not exist.
- `DELETE /kb/session/history/{kb_name}/{session_id}` idempotently clears session history; neither endpoint validates that the knowledge base exists.
- `GET /kb/session/stats` returns session-storage statistics (the number of sessions and total messages).
- These session-management endpoints are grouped under `session` in the OpenAPI documentation.
- The `/kb/chat` and `/kb/chat_stream` chat endpoints are grouped under `chat` in the OpenAPI documentation.

```python
from core.memory.session_store import InMemorySessionStore

store = InMemorySessionStore()
store.append("kb", "session-id", "user", "Hello")
history = store.get_history("kb", "session-id")
```

```bash
curl http://localhost:8028/kb/session/history/kb/session-id
curl -X DELETE http://localhost:8028/kb/session/history/kb/session-id
curl http://localhost:8028/kb/session/stats
```

### 🔧 Advanced Configuration

<details>
<summary>📋 Environment Variable Configuration (.env file)</summary>

```bash
# Service Port Configuration
API_PORT=8028

# Model Configuration
EMBEDDING_MODEL=thenlper/gte-large-zh
RERANK_MODEL=thenlper/gte-reranker-base

# Database Configuration
DATABASE_URL=sqlite:///./knowledge_base.db

# Cache Configuration
CACHE_DIR=./cache
MODEL_CACHE_DIR=./models

# Retrieval Configuration
DEFAULT_TOP_K=5
DEFAULT_SIMILARITY_THRESHOLD=0.3
MAX_CHUNK_SIZE=500

# Web search (optional): You.com Search API key. With it set, the /web/search
# endpoint works as an external retriever alongside the local KB; left blank the
# endpoint returns a "not enabled" message and nothing else is affected.
YDC_API_KEY=

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/easyrag.log

# API Configuration
MAX_QUERY_LENGTH=1000
ENABLE_RERANK=true
BATCH_SIZE=32
```

</details>

---

## 🏗️ System Architecture

```
🏗️ EasyRAG System Architecture
├── 🚀 app.py                 # FastAPI Service (API + UI)
├── 🚀 main.py                # RAG Core Service (RAGService)
├── 📚 core/                  # Core Functional Modules
│   ├── chunker/             # Text Chunking
│   ├── db/                  # Database Interaction
│   ├── llm/                 # Model Loading & Inference
│   ├── parser/              # Document Parsing
│   ├── retriever/           # Knowledge Retrieval
│   ├── reranker/            # Result Reranking
│   └── utils/               # Common Utilities
├── 📜 deploy.bat/deploy.sh   # Automatic Deployment Scripts
├── 🚀 start.bat/start.sh     # Quick Start Scripts
├── 🐳 docker-compose.yml     # Docker Orchestration
├── ⚙️ .env                   # Environment Configuration File
├── 📦 models/                # Model Cache Directory
├── 💾 data/                  # Knowledge Base Data Directory
├── 📋 requirements*.txt      # Python Dependencies
└── 📖 docs/                  # Project Documentation
```

---

## 🔧 Technical Details

### 🤖 Model Support Matrix

<table>
<tr>
<td width="50%">

#### 📊 Embedding Models
| Model Name | Dimensions | Language | Performance |
|---|---|---|---|
| **gte-large-zh** ⭐ | 1024 | Chinese | 🚀 Excellent |
| **gte-base-zh** | 768 | Chinese | 🚀 Excellent |
| gte-large | 1024 | English | ⚡ Good |
| gte-base | 768 | English | ⚡ Good |

</td>
<td width="50%">

#### 🏆 Reranker Models
| Model Name | Accuracy | Speed | Recommendation |
|---|---|---|---|
| **gte-reranker-base** | 95% | Fast | ⭐⭐⭐ |
| gte-reranker-large | 96% | Medium | ⭐⭐⭐ |
| bge-reranker-base | 93% | Fast | ⭐⭐ |

</td>
</tr>
</table>

### 🔍 Retrieval and Chunking Technologies

#### 🎯 Retrieval Strategy Comparison
| Strategy Type | Use Case | Accuracy | Speed | Recommendation |
|---|---|---|---|---|
| 🔍 **Vector Search** | Semantic similarity queries | 90% | Fast | ⭐⭐⭐ |
| 🔤 **Keyword Search** | Exact match queries | 85% | Very Fast | ⭐⭐ |
| 🎯 **Hybrid Search** | Comprehensive query needs | 95% | Medium | ⭐⭐⭐⭐⭐ |
| 🏆 **Reranking Optimization** | High accuracy requirements | 97% | Slow | ⭐⭐⭐⭐ |

#### 📄 Chunking Strategies Explained
- 🧠 **Semantic Chunking** - Based on semantic boundaries, suitable for continuous text.
- 🔤 **Recursive Character Chunking** - Splits by character count, suitable for long documents.
- 📝 **Markdown Chunking** - Based on heading structure, suitable for technical documents.
- 📚 **Subheading Chunking** - Preserves hierarchical structure, suitable for academic papers.

---

## 🚨 Important Reminders

### ⚠️ Common Issue Resolution

<details>
<summary>🔧 Faiss Vector Library Installation Failure</summary>

**Problem Description**: Faiss compilation fails during manual installation.

**Solution**:
```bash
# Solution 1: Install with conda
conda install -c conda-forge faiss-cpu

# Solution 2: Use pre-compiled packages
pip install faiss-cpu --no-cache-dir

# Solution 3: GPU version
pip install faiss-gpu
```

**Recommendation**: Using Docker deployment can avoid this issue.
</details>

<details>
<summary>🐧 Missing Linux Dependencies</summary>

```bash
# Ubuntu/Debian systems
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# CentOS/RHEL systems
sudo yum install -y mesa-libGL glib2 libSM libXext libXrender libgomp
```
</details>

<details>
<summary>🪟 Windows Permission Issues</summary>

- Run PowerShell or CMD as an administrator.
- Ensure the path does not contain Chinese characters.
- Check firewall settings to allow Python programs to access the network.
</details>

### 📊 Performance Optimization Suggestions

| Hardware Configuration | Recommended Settings | Expected Performance |
|---|---|---|
| **8GB Memory** | Small model + CPU | Process 10k documents |
| **16GB Memory** | Medium model + CPU | Process 100k documents |
| **32GB Memory + GPU** | Large model + GPU | Process 1M documents |

---

## 🔧 Troubleshooting

### 🐳 For Docker Users
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs -f

# Rebuild images
docker-compose up --build --force-recreate

# Clean cache and rebuild
docker system prune -a
docker-compose up --build
```

### 📜 For Script Users
```bash
# Check Python environment
python --version
pip --version

# Check virtual environment
source py_env/bin/activate  # Linux/Mac
py_env\Scripts\activate     # Windows

# Verify key dependencies
pip list | grep -E "(faiss|torch|transformers)"

# View detailed errors
python app.py
```

### 🔧 Common Error Codes

| Error Code | Problem Description | Solution |
|---|---|---|
| `ModuleNotFoundError` | Missing Python package | `pip install -r requirements.txt` |
| `CUDA out of memory` | Insufficient GPU memory | Reduce batch_size or use CPU |
| `Port already in use` | Port is occupied | Modify API_PORT in .env |
| `Permission denied` | Insufficient permissions | Run as administrator |

---

## 🤔 Frequently Asked Questions (FAQ)

<details>
<summary>❓ What document formats are supported?</summary>

**Supported Formats**: PDF, Word(.docx), Markdown(.md), Plain Text(.txt), Web Pages(.html), Excel(.xlsx), PowerPoint(.pptx), RTF, CSV, etc.

**Special Features**: 
- PDF supports OCR text recognition.
- Word supports table and image extraction.
- Markdown supports code block syntax highlighting.
</details>

<details>
<summary>❓ How to integrate with DocuGen?</summary>

**Integration Method**:
1. Ensure the EasyRAG service is running at `http://localhost:8028`.
2. Configure `EASYRAG_API_URL=http://localhost:8028` in DocuGen's `.env`.
3. DocuGen will automatically call EasyRAG's retrieval API to get relevant knowledge.

**API Call Example**:
```python
# Call from within DocuGen
response = requests.post("http://localhost:8028/search", json={
    "knowledge_base_id": "your_kb_id",
    "query": "your query content",
    "top_k": 10
})
```
</details>

<details>
<summary>❓ How to choose the right model?</summary>

**Embedding Model Selection**:
- For Chinese documents: `gte-large-zh` (recommended)
- For English documents: `gte-large`
- For limited resources: `gte-base-zh` (Chinese) or `gte-base` (English)

**Reranker Model Selection**:
- For high accuracy requirements: `gte-reranker-large`
- for balanced performance: `gte-reranker-base` (recommended)
- As a compatibility option: `bge-reranker-base`
</details>

<details>
<summary>❓ How many documents does the system support?</summary>

**Capacity Limits**:
- Free version: Up to 100k documents.
- Hardware limits: Depends on memory and storage space.
- Recommended configuration: 16GB memory can handle 500k documents.

**Performance Optimization**:
- Use SSD storage to improve retrieval speed.
- Enable GPU acceleration for vector calculations.
- Periodically clean up unused documents and indexes.
</details>

<details>
<summary>❓ How to back up and migrate data?</summary>

**Data Backup**:
```bash
# Back up the entire data directory
tar -czf easyrag_backup.tar.gz data/ models/ .env

# Back up only the knowledge base data
cp -r data/knowledge_bases/ /path/to/backup/
```


---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

## 🔧 Development and Verification

If you would like to contribute code to EasyRAG, please make sure it passes code verification.

### ✅ Run Verification

```bash
# Run all validations (Python + frontend)
./validate.sh

# Verify Python code only
./validate.sh python

# Verify frontend code only
./validate.sh frontend
```

### 📋 Verification Contents

- **Python**: Check code style with flake8
- **JavaScript**: Check code style with ESLint

> 💡 For more details, please refer to [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🤝 Contribution Guide

We welcome all forms of contributions!

### 🎯 Ways to Contribute
- 🐛 **Report Bugs**: Submit an issue describing the problem.
- 💡 **Suggest Features**: Propose new feature ideas.
- 📝 **Improve Documentation**: Enhance documentation and tutorials.
- 💻 **Contribute Code**: Submit a Pull Request.

---

## 📞 Support & Community

### 🆘 Getting Help
1. 📋 **Check Documentation**: Read this README and the [detailed docs](docs/).
2. 🔍 **Search Issues**: Look for similar issues in the Issues section.
3. 🐛 **Submit an Issue**: [Create a new Issue](https://github.com/BetaStreetOmnis/EasyRAG/issues/new).
4. 💬 **Join Discussions**: [GitHub Discussions](https://github.com/BetaStreetOmnis/EasyRAG/discussions).

---

## 🏆 Acknowledgements

Thanks to the following open-source projects for their support:
- [FastAPI](https://fastapi.tiangolo.com/) - A modern web API framework.
- [Transformers](https://huggingface.co/transformers/) - Pre-trained model library.
- [Faiss](https://github.com/facebookresearch/faiss) - Efficient vector similarity search.

**Special Thanks**:
- 🖋️ [DocuGen](https://github.com/BetaStreetOmnis/DocuGen) - An intelligent document generation system based on EasyRAG.

---

<div align="center">

### 🌟 If this project helps you, please give us a Star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=BetaStreetOmnis/EasyRAG&type=Date)](https://star-history.com/#BetaStreetOmnis/EasyRAG&Date)

**Made with ❤️ by the EasyRAG Team**

**🔗 Ecosystem Project**: [DocuGen - AI Document Generation](https://github.com/BetaStreetOmnis/DocuGen) | [Try DocuGen Online](http://150.138.81.55:8080/)

[⬆️ Back to Top](#-easyrag---a-lightweight-local-knowledge-base-enhancement-system)

</div>
