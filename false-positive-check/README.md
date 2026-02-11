# SonarQube False Positive Issues Reporter

A Python script that analyzes all projects in a SonarQube instance and generates comprehensive CSV reports of issues marked as false positives.

## Overview

This tool connects to a SonarQube server and generates two detailed CSV reports:

### 1. Project-Based Report
Contains information about false positives per project:
- Project names
- Number of false positive issues per project
- Total issues in the project
- Percentage of false positives
- List of rule IDs that generated the false positive issues

### 2. Rule-Based Report
Contains aggregated statistics about rules generating false positives:
- Rule IDs
- Count of false positive issues per rule
- Rule severity
- Software qualities impacted by each rule

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
| `--output` | `-o` | No | Output CSV file for project-based report | `sonarqube_false_positives.csv` |
| `--rule-output` | `-r` | No | Output CSV file for rule-based report | `false_positives_by_rule.csv` |

### Examples

```bash
# Basic usage with default output files
python sonarqube_false_positives.py -u http://localhost:9000 -t mytoken123

# Custom output file names
python sonarqube_false_positives.py -u https://sonarqube.example.com -t mytoken123 -o projects.csv -r rules.csv
```

### Sample Output Files

#### Project-Based Report (sonarqube_false_positives.csv)

```csv
Project Name,Number of Issues,Total Issues,Percentage,Rule IDs
My Web Application,5,100,5.00%,"java:S1234, java:S5678"
Backend API,12,250,4.80%,"python:S9012, python:S3456, python:S7890"
Frontend Dashboard,3,80,3.75%,javascript:S2468
```

#### Rule-Based Report (false_positives_by_rule.csv)

```csv
Rule ID,False Positive Count,Severity,Software Qualities
java:S1234,45,MAJOR,"MAINTAINABILITY, RELIABILITY"
python:S9012,32,CRITICAL,SECURITY
javascript:S2468,21,MINOR,MAINTAINABILITY
```

### Console Output

During execution, the script displays:
- Connection details
- Progress for each project being processed
- Progress for each rule being analyzed
- Summary statistics including:
  - Total projects analyzed
  - Total false positive issues
  - Total unique rules generating false positives
  - Top 5 projects with most false positives
  - Top 5 rules generating most false positives

Example console output:
```
Connecting to SonarQube at: https://sonarqube.example.com
============================================================
Fetching all projects...
Found 25 projects
Processing project 1/25: My Web Application
Processing project 2/25: Backend API
...

Report exported to: sonarqube_false_positives.csv

============================================================
Fetching all false positive issues...
  Fetched 143 of 143 issues...
Total false positive issues fetched: 143

Fetching rule details...
  Processing rule 1/15: java:S1234
  Processing rule 2/15: python:S9012
...
Rule-wise report exported to: false_positives_by_rule.csv

============================================================
Summary:
Total projects analyzed: 25
Total false positive issues: 143
Total unique rules generating false positives: 15

Top 5 projects with most false positives:
  - Backend API: 45 issues
  - My Web Application: 32 issues
  - Frontend Dashboard: 21 issues
  - Mobile App: 18 issues
  - Data Pipeline: 15 issues

Top 5 rules generating most false positives:
  - java:S1234: 45 issues (Severity: MAJOR)
  - python:S9012: 32 issues (Severity: CRITICAL)
  - javascript:S2468: 21 issues (Severity: MINOR)
  - java:S5678: 18 issues (Severity: MAJOR)
  - python:S3456: 15 issues (Severity: INFO)
```
