# EasyRAG - Lightweight Local Knowledge Base Enhancement System

[中文](README.md) | [English](README_EN.md)

## Project Introduction

EasyRAG is an intelligent Q&A system based on a local knowledge base, capable of helping users quickly retrieve and access information from the knowledge base. The system integrates vector retrieval and large language models to achieve intelligent knowledge question answering. With the support of the DeepSeek 1.5B model, the system can generate more intelligent and accurate answers based on knowledge base retrieval results.

## Interface Preview

### Main Interface
![Main Interface](images/main_interface.png)

### File Upload
![File Upload](images/file_upload.png)

### Knowledge Base Retrieval
![Knowledge Base Retrieval](images/search_interface.png)

### Intelligent Conversation
![Intelligent Conversation](images/chat_interface.png)

## Main Features

- Knowledge Base Management: Create, update, and delete knowledge bases
- Document Processing: Support for PDF, Word, text, and other document formats
- Intelligent Retrieval: Precise content retrieval based on vector similarity
- Intelligent Q&A: Generate accurate answers combined with knowledge base content
- Local Deployment: All functions run locally, ensuring data security
- DeepSeek Integration: Using DeepSeek 1.5B model for intelligent responses
- Context Awareness: Support for context-aware conversations
- Diverse Chunking Strategies: Support for multiple document chunking methods, including the new subheading chunking that preserves main heading information

## System Requirements

- Operating System: Windows/Linux/MacOS
- Recommended Python Version: Python 3.9
- Memory: At least 4GB (8GB or more recommended)
- Disk Space: At least 5GB of available space
- GPU (Optional): NVIDIA GPU with CUDA support can enhance performance

## Quick Start

### One-click Deployment

#### Windows Users

1. Double-click the `deploy.bat` file
2. The script will automatically check the Python environment, downloading and installing it if necessary
3. Create a virtual environment and install required dependencies
4. Automatically start the API server and Web interface

#### Linux/Unix Users

1. Open a terminal and navigate to the project directory
2. Add execution permissions to the script: `chmod +x deploy.sh`
3. Run the script: `./deploy.sh`
4. The script will automatically check the environment, install dependencies, and start services

### Manual Installation

If one-click deployment is not suitable for your environment, you can also install manually following these steps:

1. Ensure Python 3.9 is installed
2. Create a virtual environment: `python -m venv py_env`
3. Activate the virtual environment:
   - Windows: `py_env\Scripts\activate`
   - Linux/Mac: `source py_env/bin/activate`
4. Install dependencies:
   - CPU version: `pip install -r requirements_cpu.txt`
   - GPU version: `pip install -r requirements_gpu.txt`
5. Start services:
   - API server: `python app.py`
   - Web interface: `python ui_new.py`

### Important Note: Faiss Installation

**Note**: The deployment script temporarily skips the installation of the Faiss vector library, as compilation issues may occur in Windows environments. You need to manually install Faiss to use the complete vector retrieval functionality:

- CPU version: `pip install faiss-cpu`
- GPU version: `pip install faiss-gpu`

If the above commands fail in your environment, you can try the following alternative methods:

1. Use pre-compiled wheel packages:
   ```
   pip install faiss-cpu --only-binary=faiss-cpu
   ```

2. Or install from unofficial sources:
   ```
   pip install faiss-cpu -f https://dl.fbaipublicfiles.com/faiss/wheel/faiss_cpu-1.7.4-cp39-cp39-win_amd64.whl
   ```

3. For Linux users, you can try:
   ```
   pip install faiss-cpu -f https://dl.fbaipublicfiles.com/faiss/wheel/faiss_cpu-1.7.4-cp39-cp39-linux_x86_64.whl
   ```

## Usage Instructions

After starting the services, access the following addresses in your browser:

- Web interface: `http://localhost:7861`
- API service: `http://localhost:8000`

### Creating a Knowledge Base

1. Visit the Web interface, select the "Knowledge Base Management" tab
2. Click "Create Knowledge Base", enter a name for the knowledge base
3. Upload documents or paste text
4. The system will automatically process documents and build indexes

### Using Knowledge Base Q&A

1. Select the "Knowledge Base Conversation" tab
2. Choose a previously created knowledge base
3. Enter a question and send
4. The system will retrieve relevant content and generate an answer using the DeepSeek model

## System Architecture

- `app.py`: Backend API service
- `ui_new.py`: Web user interface
- `core/`: Core function modules
  - `kb_doc_process.py`: Document processing module
  - `kb_vector_store.py`: Vector storage module
  - `llm_model.py`: Language model module (including DeepSeek model support)
- `deploy.bat`/`deploy.sh`: Deployment scripts

## Technical Details

### Model Information

- Model used: DeepSeek-Chat-1.5B-Base
- Model source: ModelScope
- Model size: Approximately 3GB
- Will be automatically downloaded locally when first used

### Document Chunking Strategies

The system supports multiple document chunking strategies suitable for different types of documents:

- Semantic Chunking: Divides documents based on semantic boundaries, suitable for general text
- Recursive Character Chunking: Character-level chunking, suitable for unstructured text
- Markdown Header Chunking: Chunking based on Markdown headers, suitable for documents with clear headings
- Hierarchical Chunking: A chunking method that preserves document hierarchical structure
- Subheading Chunking: Designed specifically for technical documents and white papers, chunks by subheadings while preserving main heading information for precise retrieval

Chunking strategies can be selected when creating a knowledge base, and can also be custom configured via API.

## Troubleshooting

If you encounter issues, please check:

1. Whether the network connection is normal (model download is required for first run)
2. Whether there is sufficient disk space (at least 5GB available space needed)
3. View error messages in the command line window
4. Check if faiss is successfully installed (use the `pip list | grep faiss` command)

## Notes

1. Initial model loading requires downloading approximately 3GB of data, please ensure a stable network connection
2. Model response may be slower in CPU environments, running in a GPU environment is recommended
3. Deployment scripts require administrator/root privileges to install Python (if not already in the system)

## Technology Stack

- Frontend: Gradio
- Backend: FastAPI
- Vector Retrieval: Faiss
- Language Models: DeepSeek 1.5B and other supported models

## Future Improvements

1. Add more large language model options
2. Optimize model inference speed
3. Add model parameter adjustment interface
4. Enhance multi-turn conversation capabilities

## License Information

This project is for learning and research purposes only and should not be used for commercial purposes. 