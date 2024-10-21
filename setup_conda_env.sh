#!/bin/bash

# Create a new Conda environment with the latest Python version
conda create -n atlomy_chat python -y

# Activate the new environment
conda activate atlomy_chat

# Install pip packages from requirements.txt
pip install -r requirements.txt

# Install the project in editable mode
pip install -e .

echo "Conda environment 'atlomy_chat' has been created with Python 3.11 and packages have been installed."
echo "To activate the environment, run: conda activate atlomy_chat"
