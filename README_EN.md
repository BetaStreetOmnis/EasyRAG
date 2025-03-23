# EasyRAG - Lightweight Local Knowledge Base Enhancement System

[English](README_EN.md) | [中文](README.md)

### Project Overview
EasyRAG is a lightweight knowledge base retrieval system based on vector database, specifically designed for local deployment with minimal hardware requirements. The system incorporates modern data governance principles and provides a user-friendly web interface that supports importing, chunking, and retrieving various file formats. It utilizes Retrieval-Augmented Generation (RAG) technology for effective management and retrieval of large-scale documents, while ensuring data quality, security, and traceability.

### Interface Preview

#### Main Interface
![Main Interface](images/main_interface.png)

#### File Upload
![File Upload](images/file_upload.png)

#### Knowledge Base Search
![Knowledge Base Search](images/search_interface.png)

#### Intelligent Chat
![Intelligent Chat](images/chat_interface.png)

### Core Advantages
- 🚀 Lightweight Deployment
  - Full local deployment support
  - Minimum requirements: 4GB RAM, 2 CPU cores
  - No GPU required, runs smoothly on CPU
  - Incremental resource utilization
- 💡 Intelligent Document Processing
  - Automatic text chunking optimization
  - Smart vector indexing
  - Efficient retrieval algorithms
  - Low-resource embedded computing

### Key Features
- 📚 Knowledge Base Management
  - Create and delete knowledge bases
  - Customize vector dimensions and index types
  - Real-time knowledge base status monitoring
  - Knowledge base metadata management
- 📁 File Management
  - Support multiple file formats (TXT, PDF, DOCX, etc.)
  - Configurable file chunking (size, overlap)
  - File replacement and deletion
  - File version control and tracking
- 🔍 Knowledge Base Search
  - Semantic similarity search
  - Support for reranking optimization
  - Configurable number of results
  - Search result traceability
- 💬 Intelligent Dialogue
  - Knowledge base-based Q&A
  - Context memory support
  - Adjustable response randomness
  - Conversation history tracking
- 🔐 Data Governance
  - Data quality control
  - Data lifecycle management
  - Data access control
  - Data usage tracking
  - Compliance assurance

### Technical Features
- Modern web interface built with Gradio
- Multiple text chunking strategies
- Real-time progress display
- Responsive design, mobile-friendly
- Comprehensive data governance framework
  - Data standardization processing
  - Data quality monitoring
  - Data lineage tracking
  - Data security protection mechanisms
- Optimized Local Computing
  - Efficient vector calculations
  - Intelligent resource scheduling
  - Progressive loading mechanism
  - Cache optimization strategies

### Data Governance Highlights
- Full Data Lifecycle Management
  - Data Collection: Support for multi-source data ingestion with quality assurance
  - Data Processing: Standardized processing workflow ensuring data consistency
  - Data Storage: Secure and reliable storage mechanisms with encryption support
  - Data Usage: Access control and auditing for data security
  - Data Archiving: Automated archiving strategies for storage optimization
- Data Quality Assurance
  - Automated quality detection
  - Data cleansing and standardization
  - Anomaly detection and handling
  - Data update mechanisms
- Data Security and Privacy
  - Fine-grained access control
  - Data masking processing
  - Operation logging
  - Compliance checking

### Quick Start
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start API server:
```bash
python api_server.py
```

3. Start Web interface:
```bash
python ui_new.py
```

4. Access interface:
Open your browser and visit `http://localhost:7861`

### System Requirements
- Operating System: Windows/Linux/MacOS
- CPU: 2+ cores
- Memory: 4GB+ (8GB recommended)
- Storage: 10GB+ (depends on knowledge base size)
- Python Version: 3.8+

### Usage Guide
1. Ensure API server (api_server.py) is running
2. First create a knowledge base
3. Upload files to the knowledge base, system will automatically perform data quality checks
4. Use search or chat features to access knowledge base content, all operations are fully tracked
5. View data usage and governance reports in the management interface

### Performance Optimization Tips
- Adjust chunk size based on actual needs
- Use SSD storage for faster retrieval
- Increase system memory for better concurrent processing
- Regular cache cleaning for storage optimization 