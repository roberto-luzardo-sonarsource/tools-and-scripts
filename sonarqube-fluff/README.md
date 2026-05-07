# SQLFluff to SonarQube Converter

Convert [SQLFluff](https://sqlfluff.com/) lint results into the [SonarQube Generic Issue Import Format](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/importing-external-issues/generic-issue-import-format), so SQL linting violations appear as external issues in your SonarQube dashboard.

## Prerequisites

- Python 3.6+
- SQLFluff (`pip install sqlfluff`)

## Usage

### 1. Run SQLFluff and convert the output

**Pipe directly:**

```bash
sqlfluff lint --format json --dialect mysql src/ 2>/dev/null \
  | python3 sqlfluff_to_sonarqube.py > sonarqube-report.json
```

**Or save the SQLFluff output first:**

```bash
sqlfluff lint --format json --dialect mysql src/ 2>/dev/null > sqlfluff-report.json
python3 sqlfluff_to_sonarqube.py sqlfluff-report.json > sonarqube-report.json
```

Replace `mysql` with your SQL dialect (e.g., `postgres`, `bigquery`, `snowflake`, `tsql`, `ansi`). Run `sqlfluff dialects` to see all available dialects.

### 2. Import into SonarQube

Add the following property to your `sonar-project.properties` file or pass it as a command-line argument during analysis:

**sonar-project.properties:**

```properties
sonar.externalIssuesReportPaths=sonarqube-report.json
```

**Or via command line:**

```bash
sonar-scanner -Dsonar.externalIssuesReportPaths=sonarqube-report.json
```

## Rule Mapping

SQLFluff rule prefixes are mapped to SonarQube attributes as follows:

| Prefix | Category       | Clean Code Attribute | Type         | Severity | Software Quality |
|--------|----------------|----------------------|--------------|----------|------------------|
| AL     | Aliasing       | CLEAR                | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| AM     | Ambiguous      | CLEAR                | CODE_SMELL   | MAJOR    | MAINTAINABILITY  |
| CP     | Capitalisation | CONVENTIONAL         | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| CV     | Convention     | CONVENTIONAL         | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| JJ     | Jinja          | CONVENTIONAL         | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| LT     | Layout         | FORMATTED            | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| RF     | References     | LOGICAL              | BUG          | MAJOR    | RELIABILITY      |
| ST     | Structure      | CLEAR                | CODE_SMELL   | MINOR    | MAINTAINABILITY  |
| TQ     | Templating     | CONVENTIONAL         | CODE_SMELL   | MINOR    | MAINTAINABILITY  |

The output includes both `type`/`severity` fields (Standard Experience mode) and `impacts` fields (MQR mode), so it works with either SonarQube configuration.

## Example

A sample SQL file (`sample.sql`) is included for testing:

```bash
sqlfluff lint --format json --dialect mysql sample.sql 2>/dev/null \
  | python3 sqlfluff_to_sonarqube.py > sonarqube-report.json
```

## CI/CD Integration

Add this step to your pipeline to include SQLFluff results in every SonarQube analysis:

```yaml
# GitHub Actions example
- name: Lint SQL with SQLFluff
  run: |
    pip install sqlfluff
    sqlfluff lint --format json --dialect mysql src/**/*.sql 2>/dev/null \
      | python3 sqlfluff_to_sonarqube.py > sonarqube-report.json || true

- name: SonarQube Scan
  uses: sonarsource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

Make sure `sonar.externalIssuesReportPaths=sonarqube-report.json` is set in your `sonar-project.properties`.

## References

- [SQLFluff Rules Reference](https://docs.sqlfluff.com/en/stable/reference/rules.html)
- [SonarQube Generic Issue Import Format](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/importing-external-issues/generic-issue-import-format)
