# Setting up the Atlomy Chat Project

This document provides instructions for setting up and running the Atlomy Chat project in a Conda environment.

## Prerequisites

- Anaconda or Miniconda installed on your system
- Git (for cloning the repository)

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
   conda activate atlomy_chat
   ```

4. Set up environment variables:
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Open the `.env` file and fill in the necessary values for your configuration.

## Running the Project

After setting up the environment, you can run the project using the following command:

```
python -m src.playground
```

This will start the interactive playground where you can test the LLMAssistant and LexicalValueGenerator components.



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

[Rest of the content remains unchanged]

## Additional Information

- To deactivate the Conda environment when you're done, run:
  ```
  conda deactivate
  ```

- If you need to update dependencies in the future, you can re-run the `setup_conda_env.sh` script.

- For more detailed information about the project structure and components, please refer to the main README.md file.
