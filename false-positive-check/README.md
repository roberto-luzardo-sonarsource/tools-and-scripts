# SonarQube False Positive Issues Reporter

A Python script that analyzes all projects in a SonarQube instance and generates a comprehensive CSV report of issues marked as false positives.

## Overview

This tool connects to a SonarQube server, iterates through all projects, and collects information about issues that have been marked as false positives. It generates a CSV report containing:
- Project names
- Number of false positive issues per project
- List of rule IDs that generated the false positive issues

## Features

- ✅ Automatic pagination for large SonarQube instances
- ✅ Token-based authentication support
- ✅ Customizable output file path
- ✅ Detailed progress reporting
- ✅ Summary statistics
- ✅ Error handling and logging

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

### Examples

#### Example 1: Basic usage with token authentication
```bash
python sonarqube_false_positives.py \
  --url http://localhost:9000 \
  --token squ_abc123def456
```

#### Example 2: Using HTTPS with custom output file
```bash
python sonarqube_false_positives.py \
  --url https://sonarqube.example.com \
  --token squ_abc123def456 \
  --output my_custom_report.csv
```

#### Example 3: Short form arguments
```bash
python sonarqube_false_positives.py \
  -u https://robertol.ngrok.io/ \
  -t squ_ca864dbb9352de1c7bcae769680a8bea959dc717 \
  -o custom_report.csv
```

#### Example 4: Without authentication (public SonarQube instance)
```bash
python sonarqube_false_positives.py \
  --url http://localhost:9000 \
  --output report.csv
```

## Authentication

### Generating a SonarQube Token

1. Log in to your SonarQube instance
2. Click on your user avatar (top right)
3. Go to **My Account** → **Security**
4. Under "Generate Tokens":
   - Enter a token name (e.g., "false-positive-reporter")
   - Select token type (User Token recommended)
   - Click **Generate**
5. Copy the generated token immediately (it won't be shown again)

### Token Format
SonarQube tokens typically start with `squ_` followed by a long alphanumeric string.

Example: `squ_abc123def456ghi789jkl012mno345`

## Output

### CSV Report Format

The generated CSV file contains three columns:

| Column | Description |
|--------|-------------|
| **Project Name** | The name of the SonarQube project |
| **Number of Issues** | Count of false positive issues in the project |
| **Rule IDs** | Comma-separated list of rule IDs that generated false positives |

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

## Troubleshooting

### Common Issues

#### 1. Authentication Error (401 Unauthorized)
**Problem:** Invalid or expired token

**Solution:**
- Verify your token is correct
- Generate a new token from SonarQube
- Ensure the token has necessary permissions

#### 2. Connection Error
**Problem:** Cannot connect to SonarQube server

**Solution:**
- Verify the URL is correct (include http:// or https://)
- Check if the SonarQube server is running
- Verify network connectivity
- Check firewall rules

#### 3. Permission Error
**Problem:** Cannot access certain projects

**Solution:**
- Ensure your token has "Browse" permission on all projects
- Use an administrator token if needed

#### 4. Module Not Found Error
**Problem:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install requests
```

#### 5. Empty Report
**Problem:** CSV file is generated but contains no data

**Possible Causes:**
- No false positive issues exist in any project
- Insufficient permissions to view issues
- Token authentication failed silently

**Solution:**
- Verify false positives exist in SonarQube UI
- Check token permissions
- Run with verbose error output

## Technical Details

### API Endpoints Used

The script interacts with the following SonarQube Web API endpoints:

1. **`/api/projects/search`**
   - Purpose: Retrieve all projects
   - Pagination: Automatic (500 items per page)

2. **`/api/issues/search`**
   - Purpose: Search for issues with specific criteria
   - Filter: `resolutions=FALSE-POSITIVE`
   - Pagination: Automatic (500 items per page)

### Data Flow

```
1. Connect to SonarQube
         ↓
2. Fetch all projects (paginated)
         ↓
3. For each project:
   a. Fetch false positive issues
   b. Collect unique rule IDs
   c. Count issues
         ↓
4. Generate CSV report
         ↓
5. Display summary statistics
```

## Contributing

To contribute to this script:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This script is provided as-is for use with SonarQube instances.

## Support

For issues or questions:
- Open an issue in the repository
- Contact the repository maintainer

## Version History

- **v1.0** - Initial release
  - Basic functionality for false positive reporting
  - Token authentication support
  - CSV export
  - Pagination support

## Additional Notes

### Performance Considerations

- Large SonarQube instances with many projects may take several minutes to process
- The script uses pagination (500 items per page) to handle large datasets efficiently
- Network latency affects processing time

### Security Best Practices

- **Never commit tokens to version control**
- Store tokens in environment variables or secure vaults
- Use tokens with minimal required permissions
- Rotate tokens regularly
- Consider using `.env` files (excluded from git) for token storage

### Alternative Authentication Methods

While this script primarily uses token authentication, the `SonarQubeClient` class could be extended to support:
- Username/password authentication
- OAuth authentication
- API key authentication

---

**Last Updated:** February 5, 2026
