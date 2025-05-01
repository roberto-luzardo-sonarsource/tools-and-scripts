import requests

def get_project_keys(sonarqube_url: str, token: str) -> list:
    """
    Fetch all project keys from the SonarQube server.
    
    :param sonarqube_url: Base URL of the SonarQube server.
    :param token: Authentication token for the SonarQube API.
    :return: List of project keys.
    """
    project_keys = []
    page = 1
    page_size = 100  # SonarQube API default page size

    while True:
        response = requests.get(
            f"{sonarqube_url}/api/projects/search",
            params={"p": page, "ps": page_size},
            auth=(token, "")
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract project keys
        project_keys.extend(project["key"] for project in data.get("components", []))
        
        # Check if there are more pages
        if page >= data.get("paging", {}).get("total", 0) // page_size + 1:
            break
        page += 1

    return project_keys
def get_quality_gates(sonarqube_url: str, token: str, project_keys: list) -> dict:
    """
    Fetch the quality gate associated with each project key.
    
    :param sonarqube_url: Base URL of the SonarQube server.
    :param token: Authentication token for the SonarQube API.
    :param project_keys: List of project keys.
    :return: Dictionary mapping project keys to their quality gates.
    """
    quality_gates = {}

    for project_key in project_keys:
        try:
            response = requests.get(
                f"{sonarqube_url}/api/qualitygates/get_by_project",
                params={"project": project_key},
                auth=(token, "")
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract quality gate status
            quality_gates[project_key] = data.get("qualityGate", {}).get("name", "No Quality Gate")
        except requests.RequestException as e:
            print(f"Error fetching quality gate for project {project_key}: {e}")
            quality_gates[project_key] = "Error"

    return quality_gates
if __name__ == "__main__":
    sonarqube_url = "http://localhost"  # Replace with your SonarQube server URL
    token = "your_token_here"  # Replace with your SonarQube API token
    
    try:
        keys = get_project_keys(sonarqube_url, token)
        print("Project keys:", keys)
        qualitygates = get_quality_gates(sonarqube_url, token, keys)
        # Write the quality gates to a CSV file
        with open("quality_gates.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Project Key", "Quality Gate"])  # Header row
            for project_key, quality_gate in qualitygates.items():
                writer.writerow([project_key, quality_gate])
    except requests.RequestException as e:
        print(f"Error fetching project keys: {e}")
