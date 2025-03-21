import requests
import json
from datetime import datetime, timedelta

# Configuration
SONARQUBE_URL = 'REPLACE-ME'  # Replace with your actual SonarQube URL
AUTH_TOKEN = 'REPLACE-ME'  # Replace with your actual token

# Function to get issue distribution by severity. Returns a JSON output of the distribution
# Facets are used to group issues by resolution and severity, however there is a limit of 10000 issues
# For projects with > 10000 issues, /api/projects/export_findings should be used, but additional logic needs to be implemented
# since facets are not available in that endpoint
def get_issue_distribution(project_key):
    url = f"{SONARQUBE_URL}/api/issues/search"
    params = {
        'componentKeys': project_key,
        'facets': 'resolutions,severities',
        'p': 1,
       # 'ps': 500  # Page size, maximum is 500
    }
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

    data = response.json()

    return json.dumps(data['facets'], indent=4)

# Function to get code coverage rate. Returns the percentage of code coverage
# greater than or equal to a specific goal from the history of coverage measures
# This endpoint has a limit of 1000 measures, so it may not work for projects with a lot of history
# Returns None if the request fails
def get_codecoverage_rate(project_key):
    url = f"{SONARQUBE_URL}/api/measures/search_history"
    params = {
        'component': project_key,
        'metrics': 'coverage'
    }
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None 
    data = response.json() 
    for measure in data['measures']:
        if measure['metric'] == 'coverage':
            total = 0
            count = 0
            for history in measure['history']:
                if history['value'] >= '60': # Assuming 60% is the goal for coverage
                    count += 1
                total += 1
    return (count/total)*100

# Function to get all issues for a project. Returns a list of issues
# This function handles pagination to retrieve all issues, as the API limits the number of issues returned per request
# For projects with > 10000 issues, /api/projects/export_findings should be used instead
def get_all_issues(project_key):
    url = f"{SONARQUBE_URL}/api/issues/search"
    params = {
        'componentKeys': project_key,
        #'ps': 500  # Page size, maximum is 500
    }
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }

    issues = []
    page = 1
    while True:
        params['p'] = page
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            return None
        data = response.json()
        issues.extend(data['issues'])
        if page >= data['paging']['total']:
            break
        page += 1

    return issues

# Function to calculate the on-time resolution rate for issues based on their severity
# This function checks if issues are resolved within the specified time limits for each severity level
# Returns a JSON object with the on-time resolution rates for each severity level
# The time limits are:  MAJOR (24 hours), CRITICAL (72 hours), MINOR (14 days)  
def get_on_time_resolution_rate(project_key):
    issues = get_all_issues(project_key)
    on_time_counts = {
        'MAJOR': 0,
        'CRITICAL': 0,
        'MINOR': 0
    }
    total_counts = {
        'MAJOR': 0,
        'CRITICAL': 0,
        'MINOR': 0
    }

    for issue in issues:
        severity = issue['severity']
        status = issue['issueStatus']
        if severity in on_time_counts and (status == 'FIXED' or status == 'ACCEPTED'):
            creation_date = datetime.strptime(issue['creationDate'], '%Y-%m-%dT%H:%M:%S%z')
            update_date = datetime.strptime(issue['closeDate'], '%Y-%m-%dT%H:%M:%S%z')
            resolution_time = update_date - creation_date

            if (severity == 'MAJOR' and resolution_time <= timedelta(hours=24)) or \
               (severity == 'CRITICAL' and resolution_time <= timedelta(hours=72)) or \
               (severity == 'MINOR' and resolution_time <= timedelta(days=14)):
                on_time_counts[severity] += 1

            if severity in total_counts:
                total_counts[severity] += 1

    on_time_rates = {severity: (on_time_counts[severity] / total_counts[severity]) * 100 if total_counts[severity] > 0 else 0 for severity in on_time_counts}

    return json.dumps(on_time_rates, indent=4)

if __name__ == "__main__":
    project_key = 'replace-me' #Replace with your project key
    severity_distribution = get_issue_distribution(project_key)
    print(severity_distribution)
    coverage_rate = get_codecoverage_rate(project_key)
    print(f"Code Coverage Rate (>80%): {coverage_rate:.2f}%") if coverage_rate is not None else print("Failed to retrieve coverage rate.")
    on_time_resolution_rate = get_on_time_resolution_rate(project_key)
    print(f"On-Time Resolution Rates: {on_time_resolution_rate}")
