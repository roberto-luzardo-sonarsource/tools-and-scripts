import requests
import json
from datetime import datetime, timedelta

# Configuration
SONARQUBE_URL = 'https://robertol.ngrok.io'
AUTH_TOKEN = 'squ_cb91c36a872e8934b1d0859bf9f42757314c1185'

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
                if history['value'] >= '60':
                    count += 1
                total += 1
    return (count/total)*100

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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        issues.extend(data['issues'])
        if page >= data['paging']['total']:
            break
        page += 1

    return issues

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

            if severity == 'MAJOR' and resolution_time <= timedelta(hours=24):
                on_time_counts[severity] += 1
            elif severity == 'CRITICAL' and resolution_time <= timedelta(hours=72):
                on_time_counts[severity] += 1
            elif severity == 'MINOR' and resolution_time <= timedelta(days=14):
                on_time_counts[severity] += 1

            total_counts[severity] += 1

    on_time_rates = {severity: (on_time_counts[severity] / total_counts[severity]) * 100 if total_counts[severity] > 0 else 0 for severity in on_time_counts}

    return json.dumps(on_time_rates, indent=4)

if __name__ == "__main__":
    project_key = 'kover-jacoco'
    severity_distribution = get_issue_distribution(project_key)
    print(severity_distribution)
    coverage_rate = get_codecoverage_rate(project_key)
    print(f"Code Coverage Rate (>80%): {coverage_rate:.2f}%") if coverage_rate is not None else print("Failed to retrieve coverage rate.")
    on_time_resolution_rate = get_on_time_resolution_rate(project_key)
    print(f"On-Time Resolution Rates: {on_time_resolution_rate}")