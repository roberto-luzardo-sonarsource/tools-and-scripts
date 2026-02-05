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
            url = f"{self.base_url}/api/projects/search"
            params = {
                'p': page,
                'ps': page_size
            }
            
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
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
        fieldnames = ['Project Name', 'Number of Issues', 'Rule IDs']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for result in results:
            # Convert rule IDs list to comma-separated string
            rule_ids_str = ', '.join(result['rule_ids']) if result['rule_ids'] else ''
            
            writer.writerow({
                'Project Name': result['project_name'],
                'Number of Issues': result['issue_count'],
                'Rule IDs': rule_ids_str
            })
    
    print(f"\nReport exported to: {output_file}")


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
    
    args = parser.parse_args()
    
    print(f"Connecting to SonarQube at: {args.url}")
    print("=" * 60)
    
    try:
        # Analyze false positives
        results = analyze_false_positives(args.url, args.token)
        
        # Export to CSV
        export_to_csv(results, args.output)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"Total projects analyzed: {len(results)}")
        total_issues = sum(r['issue_count'] for r in results)
        print(f"Total false positive issues: {total_issues}")
        
        # Show projects with most false positives
        if results:
            sorted_results = sorted(results, key=lambda x: x['issue_count'], reverse=True)
            print("\nTop 5 projects with most false positives:")
            for result in sorted_results[:5]:
                if result['issue_count'] > 0:
                    print(f"  - {result['project_name']}: {result['issue_count']} issues")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
