#!/usr/bin/env python3
"""Convert SQLFluff JSON lint output to SonarQube Generic Issue Import format.

Usage:
    sqlfluff lint --format json [options] <paths> 2>/dev/null | python sqlfluff_to_sonarqube.py > sonarqube-report.json

    Or from a file:
    sqlfluff lint --format json [options] <paths> 2>/dev/null > sqlfluff-report.json
    python sqlfluff_to_sonarqube.py sqlfluff-report.json > sonarqube-report.json

Then import in SonarQube by setting the analysis parameter:
    sonar.externalIssuesReportPaths=sonarqube-report.json
"""

import json
import sys

# Map sqlfluff rule code prefixes to clean code attributes and impacts.
# See: https://docs.sqlfluff.com/en/stable/reference/rules.html
RULE_PREFIX_MAP = {
    "AL": {  # Aliasing
        "cleanCodeAttribute": "CLEAR",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "AM": {  # Ambiguous
        "cleanCodeAttribute": "CLEAR",
        "type": "CODE_SMELL",
        "severity": "MAJOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "MEDIUM"},
    },
    "CP": {  # Capitalisation
        "cleanCodeAttribute": "CONVENTIONAL",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "CV": {  # Convention
        "cleanCodeAttribute": "CONVENTIONAL",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "JJ": {  # Jinja
        "cleanCodeAttribute": "CONVENTIONAL",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "LT": {  # Layout
        "cleanCodeAttribute": "FORMATTED",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "RF": {  # References
        "cleanCodeAttribute": "LOGICAL",
        "type": "BUG",
        "severity": "MAJOR",
        "impact": {"softwareQuality": "RELIABILITY", "severity": "MEDIUM"},
    },
    "ST": {  # Structure
        "cleanCodeAttribute": "CLEAR",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
    "TQ": {  # Templating
        "cleanCodeAttribute": "CONVENTIONAL",
        "type": "CODE_SMELL",
        "severity": "MINOR",
        "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
    },
}

DEFAULT_MAPPING = {
    "cleanCodeAttribute": "CONVENTIONAL",
    "type": "CODE_SMELL",
    "severity": "MINOR",
    "impact": {"softwareQuality": "MAINTAINABILITY", "severity": "LOW"},
}

ENGINE_ID = "sqlfluff"


def get_rule_mapping(code):
    """Get the SonarQube mapping for a sqlfluff rule code based on its prefix."""
    prefix = "".join(c for c in code if c.isalpha())
    return RULE_PREFIX_MAP.get(prefix, DEFAULT_MAPPING)


def convert(sqlfluff_results):
    """Convert sqlfluff JSON output to SonarQube generic issue import format."""
    rules_seen = {}
    issues = []

    for file_result in sqlfluff_results:
        filepath = file_result.get("filepath", "")

        for violation in file_result.get("violations", []):
            code = violation["code"]
            mapping = get_rule_mapping(code)

            # Collect unique rules
            if code not in rules_seen:
                rules_seen[code] = {
                    "id": code,
                    "name": f"{code}: {violation.get('name', code)}",
                    "description": violation.get("description", code),
                    "engineId": ENGINE_ID,
                    "cleanCodeAttribute": mapping["cleanCodeAttribute"],
                    "type": mapping["type"],
                    "severity": mapping["severity"],
                    "impacts": [mapping["impact"]],
                }

            text_range = {"startLine": violation["start_line_no"]}
            if violation.get("end_line_no"):
                text_range["endLine"] = violation["end_line_no"]
            if violation.get("start_line_pos"):
                text_range["startColumn"] = violation["start_line_pos"] - 1  # sqlfluff is 1-based, SonarQube is 0-based
            if violation.get("end_line_pos"):
                text_range["endColumn"] = violation["end_line_pos"] - 1

            issues.append({
                "ruleId": code,
                "effortMinutes": 2,
                "primaryLocation": {
                    "message": violation["description"],
                    "filePath": filepath,
                    "textRange": text_range,
                },
            })

    return {
        "rules": list(rules_seen.values()),
        "issues": issues,
    }


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    result = convert(data)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
