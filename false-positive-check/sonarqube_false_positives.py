#!/usr/bin/env python3
"""
SonarQube False Positive Issues Reporter

This script iterates through all SonarQube projects and collects information about
issues marked as false positives, generating a CSV report with project names,
issue counts, and the rules that generated them.
"""

import requests
import csv
import sys
import argparse
from typing import List, Dict, Set
from collections import defaultdict


RULE_TYPE_TO_SOFTWARE_QUALITY = {
    'CODE_SMELL': ['MAINTAINABILITY'],
    'BUG': ['RELIABILITY'],
    'VULNERABILITY': ['SECURITY'],
    'SECURITY_HOTSPOT': ['SECURITY'],
}


class SonarQubeClient:
    """Client for interacting with SonarQube Web API"""
    
    def __init__(self, base_url: str, token: str = None):
        """
        Initialize SonarQube client
        
        Args:
            base_url: SonarQube server URL (e.g., 'http://localhost:9000')
            token: Authentication token (optional, can also use username:password)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if token:
            # Use token authentication
            self.session.auth = (token, '')

    def _get_projects_page(self, page: int, page_size: int) -> Dict:
        """Fetch one page of projects using endpoints available across server versions."""
        params = {
            'p': page,
            'ps': page_size
        }
        last_error = None

        for endpoint in ('/api/components/search_projects', '/api/projects/search'):
            url = f"{self.base_url}{endpoint}"

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                last_error = e

        if last_error:
            raise last_error

        return {'components': [], 'paging': {'total': 0}}
        
    def get_all_projects(self) -> List[Dict]:
        """
        Retrieve all projects from SonarQube
        
        Returns:
            List of project dictionaries with keys: key, name
        """
        projects = []
        page = 1
        page_size = 500
        
        while True:
            try:
                data = self._get_projects_page(page, page_size)
                
                projects.extend(data.get('components', []))
                
                # Check if there are more pages
                paging = data.get('paging', {})
                total = paging.get('total', 0)
                
                if page * page_size >= total:
                    break
                    
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching projects: {e}", file=sys.stderr)
                break
        
        return projects
    
    def get_false_positive_issues(self, project_key: str) -> List[Dict]:
        """
        Get all issues marked as false positives for a specific project

        Args:
            project_key: The project key

        Returns:
            List of issue dictionaries
        """
        issues = []
        page = 1
        page_size = 500

        while True:
            url = f"{self.base_url}/api/issues/search"
            params = {
                'componentKeys': project_key,
                'resolutions': 'FALSE-POSITIVE',
                'p': page,
                'ps': page_size
            }

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                issues.extend(data.get('issues', []))

                # Check if there are more pages
                paging = data.get('paging', {})
                total = paging.get('total', 0)

                if page * page_size >= total:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching issues for project {project_key}: {e}", file=sys.stderr)
                break

        return issues

    def get_total_issues_count(self, project_key: str) -> int:
        """
        Get total count of all issues for a specific project

        Args:
            project_key: The project key

        Returns:
            Total number of issues
        """
        url = f"{self.base_url}/api/issues/search"
        params = {
            'componentKeys': project_key,
            'ps': 1,  # We only need the total count, not the actual issues
            'p': 1
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            paging = data.get('paging', {})
            total = paging.get('total', 0)
            return total

        except requests.exceptions.RequestException as e:
            print(f"Error fetching total issues for project {project_key}: {e}", file=sys.stderr)
            return 0

    def get_all_false_positive_issues(self) -> List[Dict]:
        """
        Get all issues marked as false positives across all projects

        Returns:
            List of issue dictionaries
        """
        issues = []
        page = 1
        page_size = 500

        print("Fetching all false positive issues...")

        while True:
            url = f"{self.base_url}/api/issues/search"
            params = {
                'resolutions': 'FALSE-POSITIVE',
                'p': page,
                'ps': page_size
            }

            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                page_issues = data.get('issues', [])
                issues.extend(page_issues)

                # Check if there are more pages
                paging = data.get('paging', {})
                total = paging.get('total', 0)

                print(f"  Fetched {len(issues)} of {total} issues...")

                if page * page_size >= total:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                print(f"Error fetching all false positive issues: {e}", file=sys.stderr)
                break

        print(f"Total false positive issues fetched: {len(issues)}")
        return issues

    def get_project_quality_gate(self, project_key: str) -> str:
        """
        Get the quality gate associated with a project

        Args:
            project_key: The project key

        Returns:
            Quality gate name or 'N/A' if not found
        """
        url = f"{self.base_url}/api/qualitygates/get_by_project"
        params = {'project': project_key}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            quality_gate = data.get('qualityGate', {})
            return quality_gate.get('name', 'N/A')

        except requests.exceptions.RequestException as e:
            print(f"Error fetching quality gate for project {project_key}: {e}", file=sys.stderr)
            return 'N/A'

    def get_quality_profiles_for_project(self, project_key: str) -> Dict[str, str]:
        """
        Get quality profiles associated with a project

        Args:
            project_key: The project key

        Returns:
            Dictionary mapping language to quality profile name
        """
        url = f"{self.base_url}/api/qualityprofiles/search"
        params = {'project': project_key}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            profiles = {}
            for profile in data.get('profiles', []):
                language = profile.get('language', 'unknown')
                name = profile.get('name', 'N/A')
                profiles[language] = name

            return profiles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching quality profiles for project {project_key}: {e}", file=sys.stderr)
            return {}

    def get_rule_details(self, rule_key: str) -> Dict:
        """
        Get details about a specific rule

        Args:
            rule_key: The rule key (e.g., 'java:S1234')

        Returns:
            Dictionary with rule details including severity and software qualities
        """
        url = f"{self.base_url}/api/rules/show"
        params = {'key': rule_key}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            rule = data.get('rule', {})
            
            # Extract software qualities (impacts)
            impacts = rule.get('impacts', [])
            software_qualities = [impact.get('softwareQuality', '') for impact in impacts if impact.get('softwareQuality')]
            
            return {
                'severity': rule.get('severity', 'N/A'),
                'name': rule.get('name', 'N/A'),
                'language': rule.get('lang', 'N/A'),
                'software_qualities': software_qualities
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching rule details for {rule_key}: {e}", file=sys.stderr)
            return {'severity': 'N/A', 'name': 'N/A', 'language': 'N/A', 'software_qualities': []}

    def get_quality_profiles_with_rule(self, rule_key: str) -> List[str]:
        """
        Get quality profiles where a specific rule is active

        Args:
            rule_key: The rule key (e.g., 'java:S1234')

        Returns:
            List of quality profile names where the rule is active
        """
        url = f"{self.base_url}/api/qualityprofiles/search"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()

            active_profiles = []
            
            for profile in data.get('profiles', []):
                profile_key = profile.get('key')
                profile_name = profile.get('name')
                language = profile.get('language')
                
                # Check if rule is active in this profile
                if self.is_rule_active_in_profile(rule_key, profile_key):
                    active_profiles.append(f"{profile_name} ({language})")

            return active_profiles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching quality profiles for rule {rule_key}: {e}", file=sys.stderr)
            return []

    def is_rule_active_in_profile(self, rule_key: str, profile_key: str) -> bool:
        """
        Check if a rule is active in a specific quality profile

        Args:
            rule_key: The rule key
            profile_key: The quality profile key

        Returns:
            True if the rule is active in the profile, False otherwise
        """
        url = f"{self.base_url}/api/rules/search"
        params = {
            'qprofile': profile_key,
            'rule_key': rule_key,
            'activation': 'true'
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            total = data.get('total', 0)
            return total > 0

        except requests.exceptions.RequestException as e:
            return False


def analyze_false_positives(sonarqube_url: str, token: str = None) -> List[Dict]:
    """
    Analyze false positive issues across all projects

    Args:
        sonarqube_url: SonarQube server URL
        token: Authentication token (optional)

    Returns:
        List of dictionaries with project analysis results
    """
    client = SonarQubeClient(sonarqube_url, token)

    print("Fetching all projects...")
    projects = client.get_all_projects()
    print(f"Found {len(projects)} projects")

    results = []

    for i, project in enumerate(projects, 1):
        project_key = project.get('key')
        project_name = project.get('name', project_key)

        print(f"Processing project {i}/{len(projects)}: {project_name}")

        # Get false positive issues for this project
        issues = client.get_false_positive_issues(project_key)
        
        # Get total issues count for this project
        total_issues = client.get_total_issues_count(project_key)
        
        # Calculate percentage
        percentage = (len(issues) / total_issues * 100) if total_issues > 0 else 0

        # Collect unique rule IDs
        rule_ids: Set[str] = set()
        for issue in issues:
            rule = issue.get('rule')
            if rule:
                rule_ids.add(rule)

        results.append({
            'project_name': project_name,
            'project_key': project_key,
            'issue_count': len(issues),
            'total_issues': total_issues,
            'percentage': percentage,
            'rule_ids': sorted(list(rule_ids))
        })

    return results


def export_to_csv(results: List[Dict], output_file: str = 'sonarqube_false_positives.csv'):
    """
    Export results to CSV file

    Args:
        results: List of project analysis results
        output_file: Output CSV file path
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Project Name', 'Number of Issues', 'Total Issues', 'Percentage', 'Rule IDs']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for result in results:
            # Convert rule IDs list to comma-separated string
            rule_ids_str = ', '.join(result['rule_ids']) if result['rule_ids'] else ''

            writer.writerow({
                'Project Name': result['project_name'],
                'Number of Issues': result['issue_count'],
                'Total Issues': result['total_issues'],
                'Percentage': f"{result['percentage']:.2f}%",
                'Rule IDs': rule_ids_str
            })

    print(f"\nReport exported to: {output_file}")


def count_false_positives_by_rule(sonarqube_url: str, token: str = None) -> List[Dict]:
    """
    Count false positive issues by rule across all projects and gather rule details

    Args:
        sonarqube_url: SonarQube server URL
        token: Authentication token (optional)

    Returns:
        List of dictionaries with rule ID, count, severity, and quality profiles
    """
    client = SonarQubeClient(sonarqube_url, token)

    # Get all false positive issues
    all_issues = client.get_all_false_positive_issues()

    # Count issues by rule
    rule_counts = defaultdict(int)
    for issue in all_issues:
        rule = issue.get('rule')
        if rule:
            rule_counts[rule] += 1

    # Gather detailed information for each rule
    print("\nFetching rule details...")
    rule_details = []
    
    for i, (rule_id, count) in enumerate(rule_counts.items(), 1):
        print(f"  Processing rule {i}/{len(rule_counts)}: {rule_id}")
        
        # Get rule details (severity and software qualities)
        details = client.get_rule_details(rule_id)
        
        rule_details.append({
            'rule_id': rule_id,
            'count': count,
            'severity': details.get('severity', 'N/A'),
            'software_qualities': details.get('software_qualities', [])
        })
    
    return rule_details


def export_rule_counts_to_csv(rule_details: List[Dict], output_file: str = 'false_positives_by_rule.csv'):
    """
    Export rule-wise false positive counts to CSV file

    Args:
        rule_details: List of dictionaries with rule information
        output_file: Output CSV file path
    """
    # Sort rules by count (descending)
    sorted_rules = sorted(rule_details, key=lambda x: x['count'], reverse=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Rule ID', 'False Positive Count', 'Severity', 'Software Qualities']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for rule in sorted_rules:
            # Convert software qualities list to comma-separated string
            qualities_str = ', '.join(rule['software_qualities']) if rule['software_qualities'] else 'N/A'
            
            writer.writerow({
                'Rule ID': rule['rule_id'],
                'False Positive Count': rule['count'],
                'Severity': rule['severity'],
                'Software Qualities': qualities_str
            })

    print(f"Rule-wise report exported to: {output_file}")


def main():
    """Main entry point"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate a report of false positive issues from SonarQube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --url http://localhost:9000 --token mytoken123
  %(prog)s --url https://sonarqube.example.com --token mytoken123 --output report.csv
  %(prog)s -u http://localhost:9000 -t mytoken123 -o custom_report.csv
        ''')
    
    parser.add_argument(
        '-u', '--url',
        required=True,
        help='SonarQube server URL (e.g., http://localhost:9000)')
    
    parser.add_argument(
        '-t', '--token',
        default='',
        help='SonarQube authentication token (optional)')
    
    parser.add_argument(
        '-o', '--output',
        default='sonarqube_false_positives.csv',
        help='Output CSV file path (default: sonarqube_false_positives.csv)')
    
    parser.add_argument(
        '-r', '--rule-output',
        default='false_positives_by_rule.csv',
        help='Output CSV file for rule-wise counts (default: false_positives_by_rule.csv)')
    
    args = parser.parse_args()
    
    print(f"Connecting to SonarQube at: {args.url}")
    print("=" * 60)
    
    try:
        # Analyze false positives
        results = analyze_false_positives(args.url, args.token)
        
        # Export to CSV
        export_to_csv(results, args.output)
        
        # Count false positives by rule and export to CSV
        print("\n" + "=" * 60)
        rule_details = count_false_positives_by_rule(args.url, args.token)
        export_rule_counts_to_csv(rule_details, args.rule_output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"Total projects analyzed: {len(results)}")
        total_issues = sum(r['issue_count'] for r in results)
        print(f"Total false positive issues: {total_issues}")
        print(f"Total unique rules generating false positives: {len(rule_details)}")
        
        # Show projects with most false positives
        if results:
            sorted_results = sorted(results, key=lambda x: x['issue_count'], reverse=True)
            print("\nTop 5 projects with most false positives:")
            for result in sorted_results[:5]:
                if result['issue_count'] > 0:
                    print(f"  - {result['project_name']}: {result['issue_count']} issues")
        
        # Show rules with most false positives
        if rule_details:
            sorted_rules = sorted(rule_details, key=lambda x: x['count'], reverse=True)
            print("\nTop 5 rules generating most false positives:")
            for rule in sorted_rules[:5]:
                print(f"  - {rule['rule_id']}: {rule['count']} issues (Severity: {rule['severity']})")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
