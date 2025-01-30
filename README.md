# Expmem: RAG-Based Coding Agents with Long-Term Memory

## Overview
This project leverages **Retrieval-Augmented Generation (RAG)** and **long-term memory mechanisms** to create more intelligent and context-aware coding agents. By integrating RAG for efficient retrieval of relevant knowledge and memory-enhanced architectures for persistent learning, the agents improve their ability to assist with complex coding tasks over time.

## Features
- **RAG-Enhanced Retrieval:** Uses external knowledge bases to fetch relevant code snippets, documentation, and best practices.
- **Long-Term Memory:** Implements memory mechanisms (e.g., vector databases, knowledge graphs) to store and recall past interactions.
- **Incremental Learning:** Improves over time by adapting to user preferences and refining responses based on past experiences.
- **Multi-Agent Collaboration:** Enables multiple AI agents to work together for debugging, code completion, and optimization.
- **Human-in-the-Loop (HITL):** Supports user feedback loops for iterative improvements.

## Technologies Used
- **Language Models:** OpenAI GPT, Llama, or Mistral-based LLMs
- **Vector Databases:** FAISS, Pinecone, Weaviate
- **Frameworks:** LangChain, LangGraph, Transformers
- **Orchestration:** Docker, FastAPI
- **Memory Storage:** Redis, PostgreSQL, or custom long-term memory modules

## Setup Instructions
1. **Clone the Repository:**
   ```sh
   git clone https://github.com/HarshavardhanK/expmem.git
   cd expmem
   ```
2. **Set Up a Virtual Environment with Poetry:**
   ```sh
   poetry install
   ```
3. **Activate the Virtual Environment:**
   ```sh
   poetry shell
   ```

## Notes on Project Structure
- The current project structure contains multiple directories such as `agents`, `analysis`, `datasets`, and others. The structure needs to be **cleaned and streamlined** to improve maintainability and usability.
- A primary entry point for the application (e.g., `main.py`) is missing and should be created to unify the workflow.

## Usage
- Query the agent for coding-related questions.
- The agent retrieves relevant snippets from stored knowledge.
- Long-term memory allows it to recall past interactions and refine responses.
- Feedback from users improves its suggestions over time.

## Future Improvements
- **Streamline Project Structure**: Remove unused directories and consolidate related components.
- **Better Memory Indexing**: Enhance storage and retrieval efficiency.
- **Fine-tuning LLMs**: Improve agent responses with domain-specific datasets.
- **Enhanced UI**: Develop a frontend interface for better interaction.

## Contributing
Contributions are welcome! Please submit issues or pull requests to improve the project.

## License
This project is licensed under the MIT License.

