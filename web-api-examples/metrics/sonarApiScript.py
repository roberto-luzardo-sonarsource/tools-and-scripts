import requests
import json

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

if __name__ == "__main__":
    project_key = 'kover-jacoco'
    severity_distribution = get_issue_distribution(project_key)
    print(severity_distribution)
    coverage_rate = get_codecoverage_rate(project_key)
    print(f"Code Coverage Rate (>80%): {coverage_rate:.2f}%") if coverage_rate is not None else print("Failed to retrieve coverage rate.")