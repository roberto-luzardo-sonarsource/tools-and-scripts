# SonarQube False Positive Issues Reporter

A Python script that analyzes all projects in a SonarQube instance and generates a comprehensive CSV report of issues marked as false positives.

## Overview

This tool connects to a SonarQube server, iterates through all projects, and collects information about issues that have been marked as false positives. It generates a CSV report containing:
- Project names
- Number of false positive issues per project
- List of rule IDs that generated the false positive issues

## Requirements

### Python Version
- Python 3.6 or higher

### Dependencies
- `requests` - HTTP library for making API calls

## Installation

### 1. Clone or Download the Script

```bash
git clone https://github.com/roberto-luzardo-sonarsource/tools-and-scripts.git
cd tools-and-scripts/false-positive-check
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install requests
```

## Usage

### Basic Usage

```bash
python sonarqube_false_positives.py -u <SONARQUBE_URL> -t <AUTH_TOKEN>
```

### Command-Line Arguments

| Argument | Short | Required | Description | Default |
|----------|-------|----------|-------------|---------|
| `--url` | `-u` | Yes | SonarQube server URL | N/A |
| `--token` | `-t` | No | Authentication token | None |
| `--output` | `-o` | No | Output CSV file path | `sonarqube_false_positives.csv` |

### Sample Output

```csv
Project Name,Number of Issues,Rule IDs
My Web Application,5,java:S1234, java:S5678
Backend API,12,python:S9012, python:S3456, python:S7890
Frontend Dashboard,3,javascript:S2468
```

### Console Output

During execution, the script displays:
- Connection details
- Progress for each project being processed
- Summary statistics including:
  - Total projects analyzed
  - Total false positive issues
  - Top 5 projects with most false positives

Example console output:
```
Connecting to SonarQube at: https://sonarqube.example.com
============================================================
Fetching all projects...
Found 25 projects
Processing project 1/25: My Web Application
Processing project 2/25: Backend API
...
Report exported to: custom_report.csv

============================================================
Summary:
Total projects analyzed: 25
Total false positive issues: 143

Top 5 projects with most false positives:
  - Backend API: 45 issues
  - My Web Application: 32 issues
  - Frontend Dashboard: 21 issues
  - Mobile App: 18 issues
  - Data Pipeline: 15 issues
```
