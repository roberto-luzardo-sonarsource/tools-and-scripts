#!/usr/bin/env python3
"""
Convert CodeNarc XML report to SonarQube generic issue format (JSON).

SonarQube's generic issue report format allows importing issues from external analyzers.
This converter transforms CodeNarc reports to be compatible with SonarQube's latest format
(10.3+), which includes a rules definition array.

Usage:
    python3 codenarc_to_sonarqube.py <codenarc_xml_report> <output_json_report>
"""

import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Mapping from CodeNarc violation names to SonarQube issue types, severities, and descriptions
VIOLATION_MAPPINGS = {
    # Security issues
    'SqlInjection': {
        'type': 'VULNERABILITY', 
        'severity': 'BLOCKER',
        'description': 'SQL injection vulnerability detected - avoid string concatenation in SQL queries',
        'cleanCodeAttribute': 'TRUSTWORTHY'
    },
    'HardcodedPassword': {
        'type': 'VULNERABILITY', 
        'severity': 'BLOCKER',
        'description': 'Hardcoded password or sensitive credential found in source code',
        'cleanCodeAttribute': 'TRUSTWORTHY'
    },
    'InsecureRandomNumberGeneration': {
        'type': 'VULNERABILITY', 
        'severity': 'CRITICAL',
        'description': 'Use SecureRandom instead of Random for cryptographic operations',
        'cleanCodeAttribute': 'TRUSTWORTHY'
    },
    'HardcodedWindowsFileSeparator': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Hardcoded path separator or IP address detected',
        'cleanCodeAttribute': 'CONVENTIONAL'
    },
    'UnnecessaryObjectReferences': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Unnecessary object reference detected',
        'cleanCodeAttribute': 'FOCUSED'
    },
    
    # Bug-like issues
    'ComparisonWithStrings': {
        'type': 'BUG', 
        'severity': 'CRITICAL',
        'description': 'Compare strings with equals() method, not == operator',
        'cleanCodeAttribute': 'CLEAR'
    },
    'CatchException': {
        'type': 'BUG', 
        'severity': 'MAJOR',
        'description': 'Catch specific exception types, not generic Exception',
        'cleanCodeAttribute': 'CLEAR'
    },
    'UseOfDeprecatedMethod': {
        'type': 'BUG', 
        'severity': 'MAJOR',
        'description': 'Using deprecated API or method',
        'cleanCodeAttribute': 'CONVENTIONAL'
    },
    
    # Code smell - Naming
    'FieldNamelowerCaseAndContainsOnlyLettersAndDigits': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Field name should follow naming conventions',
        'cleanCodeAttribute': 'IDENTIFIABLE'
    },
    'MethodNamelowerCaseAndContainsOnlyLettersAndDigits': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Method name should follow naming conventions',
        'cleanCodeAttribute': 'IDENTIFIABLE'
    },
    
    # Code smell - Complexity
    'CyclomaticComplexity': {
        'type': 'CODE_SMELL', 
        'severity': 'MAJOR',
        'description': 'Method has high cyclomatic complexity',
        'cleanCodeAttribute': 'FOCUSED'
    },
    'ParameterCount': {
        'type': 'CODE_SMELL', 
        'severity': 'MAJOR',
        'description': 'Method has too many parameters',
        'cleanCodeAttribute': 'MODULAR'
    },
    
    # Code smell - Size
    'MethodSize': {
        'type': 'CODE_SMELL', 
        'severity': 'MAJOR',
        'description': 'Method exceeds maximum size',
        'cleanCodeAttribute': 'FOCUSED'
    },
    'ClassSize': {
        'type': 'CODE_SMELL', 
        'severity': 'MAJOR',
        'description': 'Class exceeds maximum size',
        'cleanCodeAttribute': 'MODULAR'
    },
    
    # Code smell - Formatting
    'SpaceAroundOperator': {
        'type': 'CODE_SMELL', 
        'severity': 'INFO',
        'description': 'Missing space around operator',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'SpaceAfterOpeningBrace': {
        'type': 'CODE_SMELL', 
        'severity': 'INFO',
        'description': 'Incorrect spacing around braces',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'SpaceBeforeOpeningBrace': {
        'type': 'CODE_SMELL', 
        'severity': 'INFO',
        'description': 'Missing space before opening brace',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'BlankLineBeforePackage': {
        'type': 'CODE_SMELL', 
        'severity': 'INFO',
        'description': 'Missing blank line between code elements',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'LongLine': {
        'type': 'CODE_SMELL', 
        'severity': 'INFO',
        'description': 'Line exceeds maximum allowed length',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'MultipleStatementsOnOneLine': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Multiple statements on a single line',
        'cleanCodeAttribute': 'FORMATTED'
    },
    'BracesRequiredForIfElseBlock': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Control structures should use braces',
        'cleanCodeAttribute': 'FORMATTED'
    },
    
    # Code smell - Unused
    'UnusedVariable': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Variable is assigned but never used',
        'cleanCodeAttribute': 'FOCUSED'
    },
    'UnusedImport': {
        'type': 'CODE_SMELL', 
        'severity': 'MINOR',
        'description': 'Import is not used',
        'cleanCodeAttribute': 'FOCUSED'
    },
}

def map_priority_to_severity(priority: str) -> str:
    """
    Map CodeNarc priority to SonarQube severity.
    CodeNarc uses 1=highest, 3=lowest
    """
    priority_map = {
        '1': 'CRITICAL',
        '2': 'MAJOR',
        '3': 'MINOR',
    }
    return priority_map.get(priority, 'INFO')

def get_rule_config(violation_name: str, priority: str) -> Dict[str, str]:
    """
    Get SonarQube rule configuration from violation name and priority.
    Returns type, severity, description, and cleanCodeAttribute.
    """
    if violation_name in VIOLATION_MAPPINGS:
        return VIOLATION_MAPPINGS[violation_name]
    
    # Default mapping based on priority only
    default_severity = map_priority_to_severity(priority)
    return {
        'type': 'CODE_SMELL',
        'severity': default_severity,
        'description': f"CodeNarc rule: {violation_name}",
        'cleanCodeAttribute': 'CONVENTIONAL'
    }

def build_rules_array(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a deduplicated rules array from violations.
    """
    seen_rules = {}
    rules = []
    
    for violation in violations:
        rule_id = violation['violation_name']
        
        if rule_id not in seen_rules:
            config = get_rule_config(rule_id, violation['priority'])
            rule = {
                'id': rule_id,
                'name': rule_id,  # Use rule ID as name if not found
                'description': config.get('description', f'CodeNarc rule: {rule_id}'),
                'engineId': 'codenarc',
                'type': config['type'],
                'severity': config['severity'],
                'cleanCodeAttribute': config.get('cleanCodeAttribute', 'CONVENTIONAL')
            }
            seen_rules[rule_id] = rule
            rules.append(rule)
    
    return rules

def parse_codenarc_report(xml_file: str, base_path: str = 'src/main/groovy') -> List[Dict[str, Any]]:
    """
    Parse CodeNarc XML report and convert to SonarQube issue format.
    Returns a list of violations with metadata.
    """
    violations = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        return violations
    
    for file_elem in root.findall('.//File'):
        file_path = file_elem.get('name')
        
        for violation in file_elem.findall('Violation'):
            violation_name = violation.get('name')
            priority = violation.get('priority', '3')
            line_number = int(violation.get('lineNumber', '1'))
            message_elem = violation.find('Message')
            message = message_elem.text if message_elem is not None else f"{violation_name}"
            
            violations.append({
                'violation_name': violation_name,
                'priority': priority,
                'line_number': line_number,
                'message': message,
                'file_path': file_path,
                'base_path': base_path
            })
    
    return violations

def create_issue_from_violation(violation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a SonarQube issue object from a violation.
    """
    config = get_rule_config(violation['violation_name'], violation['priority'])
    
    # Build textRange - only include startLine for line-level precision
    # Most static analyzers (like CodeNarc) don't provide column info, so we omit it
    text_range = {
        'startLine': violation['line_number']
    }
    
    issue = {
        'ruleId': violation['violation_name'],
        'primaryLocation': {
            'message': violation['message'],
            'filePath': f"{violation['base_path']}/{violation['file_path']}",
            'textRange': text_range
        },
        'effortMinutes': 5  # Estimated effort to fix
    }
    
    return issue

def generate_sonarqube_report(rules: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate SonarQube generic issue report with rules and issues.
    """
    return {
        'rules': rules,
        'issues': issues
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 codenarc_to_sonarqube.py <codenarc_xml_report> [output_json_report]")
        print("\nExample:")
        print("  python3 codenarc_to_sonarqube.py build/reports/codenarc/CodeNarcReport.xml sonarqube-report.json")
        sys.exit(1)
    
    codenarc_report = sys.argv[1]
    output_report = sys.argv[2] if len(sys.argv) > 2 else 'sonarqube-report.json'
    
    if not Path(codenarc_report).exists():
        print(f"Error: File '{codenarc_report}' not found", file=sys.stderr)
        sys.exit(1)
    
    print(f"Reading CodeNarc report from: {codenarc_report}")
    violations = parse_codenarc_report(codenarc_report)
    print(f"Found {len(violations)} violations")
    
    # Build rules array from unique violations
    rules = build_rules_array(violations)
    print(f"Found {len(rules)} unique rules")
    
    # Create issues from violations
    issues = [create_issue_from_violation(v) for v in violations]
    
    report = generate_sonarqube_report(rules, issues)
    
    output_path = Path(output_report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"SonarQube report written to: {output_report}")
    print("\nSummary by type:")
    type_summary = {}
    for issue in issues:
        # Find the rule for this issue to get the type
        rule_id = issue['ruleId']
        for rule in rules:
            if rule['id'] == rule_id:
                issue_type = rule['type']
                type_summary[issue_type] = type_summary.get(issue_type, 0) + 1
                break
    
    for issue_type, count in sorted(type_summary.items()):
        print(f"  {issue_type}: {count}")
    
    print("\nSummary by severity:")
    severity_summary = {}
    for rule in rules:
        severity = rule['severity']
        # Count issues using this rule
        rule_count = sum(1 for issue in issues if issue['ruleId'] == rule['id'])
        severity_summary[severity] = severity_summary.get(severity, 0) + rule_count
    
    severity_order = ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']
    for severity in severity_order:
        if severity in severity_summary:
            print(f"  {severity}: {severity_summary[severity]}")
    
    print("\nReport format: SonarQube Generic Issue Format (Latest - 10.3+)")
    print("✓ rules array defined")
    print("✓ cleanCodeAttribute included")
    print("✓ No invalid column offset values")

if __name__ == '__main__':
    main()
