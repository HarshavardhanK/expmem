# Expmem: RAG-Based Coding Agents with Long-Term Memory

## Overview
This project leverages **Retrieval-Augmented Generation (RAG)** and **long-term memory mechanisms** to create more intelligent and context-aware coding agents. By integrating RAG for efficient retrieval of relevant knowledge and memory-enhanced architectures for persistent learning, the agents improve their ability to assist with complex coding tasks over time. Our RAG-based agentic coding approach has demonstrated exceptional performance on the HumanEval coding dataset, showcasing the effectiveness of memory-enhanced code generation.

The system implements advanced contextual RAG with sophisticated document processing, semantic understanding, and dynamic query transformation. The agentic system features a multi-stage workflow that includes intelligent document grading, query rewriting, and context-aware code generation.

## Features
- **Advanced Contextual RAG:**
  - Semantic document chunking with context preservation
  - Intelligent document grading for relevance assessment
  - Dynamic query transformation and rewriting
  - Multi-stage retrieval and generation pipeline
  - Context-aware code generation with error analysis

- **Agentic System Architecture:**
  - Multi-stage workflow with intelligent routing
  - Document relevance grading
  - Query transformation capabilities
  - Context-aware code generation
  - Integrated error analysis and debugging

- **Long-Term Memory:**
  - Contextual memory storage with semantic understanding
  - Intelligent chunking with context preservation
  - Memory retrieval with relevance scoring
  - Persistent learning from past interactions

- **Code Generation Features:**
  - Context-aware code generation
  - Error analysis and debugging
  - Test case validation
  - Code explanation generation
  - Solution optimization

- **HumanEval Performance:** Achieves high success rates on the HumanEval coding benchmark through memory-enhanced code generation.

## Technologies Used
- **Language Models:** OpenAI GPT-4, GPT-4o-mini
- **Vector Databases:** 
  - Pinecone with text-embedding-3-small embeddings for long-term memory storage
  - Contextual memory with semantic understanding
- **Frameworks:** 
  - DSPy for RAG pipeline optimization
  - LangGraph for agent orchestration
  - LangChain for LLM integration
  - Streamlit for visualization
- **Storage Systems:**
  - MongoDB for dataset context and experiment results
  - Pinecone for vector-based memory storage
- **Development Tools:** Poetry for dependency management
- **Evaluation:** LLM Sandbox for code execution and testing

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

