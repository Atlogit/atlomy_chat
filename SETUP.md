# Setting up the Atlomy Chat Project

This document provides instructions for setting up and running the Atlomy Chat project in a Conda environment.

## Prerequisites

- Anaconda or Miniconda installed on your system
- Git (for cloning the repository)
- Node.js v20.18.0 and npm v10.8.2 (for running the Next.js app)

## Setup Instructions

1. Clone the repository (if you haven't already):
   ```
   git clone https://github.com/Atlogit/atlomy_chat.git
   cd atlomy_chat
   ```

2. Run the setup script to create the Conda environment and install dependencies:
   ```
   bash setup_conda_env.sh
   ```

3. Activate the Conda environment:
   ```
   source /root/miniconda3/bin/activate atlomy_chat
   ```
   or
   ```
   conda activate atlomy_chat
   ```

4. Set up environment variables:
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Open the `.env` file and fill in the necessary values for your configuration.

5. Ensure you have the correct Node.js and npm versions:
   - Required Node.js version: v20.18.0
   - Required npm version: 10.8.2

   To check your current versions:
   ```
   node --version
   npm --version
   ```

   If you need to update Node.js, you can use nvm (Node Version Manager):
   ```
   source ~/.nvm/nvm.sh
   nvm install 20.18.0
   nvm use 20.18.0
   ```

   npm should be automatically updated with Node.js, but if not, you can update it manually:
   ```
   npm install -g npm@10.8.2
   ```

## Running the Project

After setting up the environment, you can run the project using the following steps:

1. Start the FastAPI backend:
   ```
   python app/run_server.py
   ```

2. In a new terminal, navigate to the `next-app/` directory:
   ```
   cd next-app
   ```

3. Install dependencies:
   ```
   npm install
   ```

4. Start the Next.js development server:
   ```
   npm run dev
   ```

5. Open your browser and visit `http://localhost:3000` to access the application.

## Running the Application in Debug Mode

To run the application in debug mode (both backend and frontend):

1. Ensure you are in the project root directory.

2. Run the debug script:
   ```
   bash run_debug.sh
   ```

This script will:
- Start the FastAPI backend in debug mode
- Navigate to the `next-app` directory
- Install frontend dependencies
- Start the Next.js development server

The script will provide information about where the servers are running:
- FastAPI backend: http://localhost:8000
- Next.js frontend: http://localhost:3000

To stop the debugging session, press Enter in the terminal where the script is running.

This will start the backend server in debug mode, allowing you to set breakpoints and debug the backend code.

## Running the Interactive Playground

To run the interactive playground where you can test the LLMAssistant and LexicalValueGenerator components:

```
python -m src.playground
```

## Running the TLG Parser

The TLG (Thesaurus Linguae Graecae) parser is a tool for processing TLG text files and adding them to the corpus. To run the TLG parser:

1. Ensure you have activated the Conda environment:
   ```
   conda activate atlomy_chat
   ```

2. Navigate to the project root directory:
   ```
   cd /path/to/atlomy_chat
   ```

3. Run the TLG parser script with the following command:
   ```
   python -m src.data_parsing.tlg_parser --input_path /path/to/tlg/files [options]
   ```

   Options:
   - `--input_path`: Path to the input file or directory containing TLG files (required)
   - `--corpus_path`: Path to the corpus directory (default: project_root/assets/texts/annotated)
   - `--skip-existing`: Skip processing files that already exist in the corpus
   - `--log-level`: Set the logging level (choices: DEBUG, INFO, WARNING, ERROR, CRITICAL; default: INFO)

   Example:
   ```
   python -m src.data_parsing.tlg_parser --input_path /path/to/tlg/files --log-level DEBUG
   ```

4. The script will process the TLG files and add them to the corpus. You can monitor the progress in the console output.

Note: Make sure you have the necessary TLG files and the required spaCy model (atlomy_full_pipeline_annotation_131024) installed before running the parser.

## Additional Information

- To deactivate the Conda environment when you're done, run:
  ```
  conda deactivate
  ```

- If you need to update dependencies in the future, you can re-run the `setup_conda_env.sh` script.

- For more detailed information about the project structure and components, please refer to the main README.md file.

## Running Tests

To run tests for the Next.js app, use the following commands in the `next-app` directory:

- Run all tests: `npm test`
- Run tests in watch mode: `npm run test:watch`
- Generate test coverage report: `npm run test:coverage`

For more detailed information about the project structure, components, and development guidelines, please refer to the main README.md file and other documentation in the `cline_docs/` directory.