# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Security Features

### Authentication & Credentials
- OAuth 2.0 authentication with Gmail API (read-only scopes by default)
- Credentials stored using OS keyring via `SecureCredentialManager`
- Token refresh handled automatically with secure storage
- Repository credential protection: prevents accidentally storing credentials in git repos

### Data Protection
- PII redaction in logs via `SecureLogger`
- Atomic file writes to prevent corruption
- Input validation using Pydantic schemas
- Rate limiting to prevent API abuse

### API Security
- Batch API with proper error handling and retry logic
- API response validation to prevent injection attacks
- Network error isolation and proper exception handling

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security concerns to the maintainer (create private disclosure)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: Within 24-48 hours
  - High: Within 7 days
  - Medium: Within 30 days
  - Low: Next scheduled release

## Security Best Practices

### For Users

1. **Credential Protection**
   - Never commit `credentials.json` or `token.json` to version control
   - Store credentials outside the repository directory
   - Use `--allow-repo-credentials` flag only if absolutely necessary

2. **API Scopes**
   - Default scope is read-only (`gmail.readonly`)
   - Modify/delete operations require explicit scope upgrade
   - Review requested scopes before granting access

3. **Output Security**
   - Email backups may contain sensitive information
   - Secure your backup directories with appropriate permissions
   - Consider encrypting backup storage

### For Developers

1. **Code Reviews**
   - All PRs require security review
   - No hardcoded credentials or secrets
   - Use `SecureLogger` instead of standard logging for user data

2. **Dependency Management**
   - Dependencies pinned via `requirements.lock`
   - Regular security audits with `pip-audit`
   - Automated dependency updates monitored

3. **Testing**
   - Security tests in `tests/security/`
   - Input validation tests required for all user inputs
   - Exception handling tested for all API interactions

## Known Security Considerations

### Gmail API Access
- This tool requires access to your Gmail account
- OAuth tokens are stored locally and can access your email
- Revoke access via Google Account settings if compromised

### Local Storage
- Email backups are stored unencrypted by default
- Token files contain refresh tokens - protect them like passwords
- Checkpoint files may contain message IDs

## Changelog

### v2.0.0
- Added `SecureCredentialManager` for OS keyring storage
- Added `SecureLogger` with PII redaction
- Added repository credential protection
- Added input validation via Pydantic schemas
