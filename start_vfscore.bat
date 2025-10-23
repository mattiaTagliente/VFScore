@echo off
:: Quick Start Script for VFScore
:: Use this script to activate the environment and run VFScore commands

echo Welcome to VFScore!
echo.
echo This script will:
echo 1. Activate the virtual environment
echo 2. Show available commands
echo.

:: Activate the virtual environment
call .\venv\Scripts\activate

echo Virtual environment activated.
echo.
echo Available commands:
echo   vfscore --help          : Show all commands
echo   vfscore run-all         : Run complete pipeline
echo   vfscore run-all --fast  : Run complete pipeline in fast mode
echo.
echo Example usage:
echo   vfscore ingest
echo   vfscore preprocess-gt
echo   vfscore render-cand
echo   vfscore run-all
echo.

cmd /k