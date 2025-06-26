# FrappePilot Test Suite

## Overview

This comprehensive test suite validates all aspects of your FrappePilot installation, from basic system prerequisites to advanced AI functionality. The test suite is designed to help you verify that your installation is working correctly and identify any potential issues.

## Prerequisites

Before running the test suite, ensure you have the following Python packages installed:

```bash
pip3 install mysql-connector-python redis requests
```

## Configuration

1. Copy the `test_config.json.example` to `test_config.json`
2. Update the configuration values to match your environment:
   - Database credentials
   - ERPNext URL
   - Ollama URL
   - Test user credentials

## Running the Tests

### Basic Usage

```bash
python3 test_frappepilot.py
```

### With Custom Configuration

```bash
python3 test_frappepilot.py
# When prompted, enter the path to your configuration file
```

## Test Categories

The test suite includes the following test categories:

1. **System Prerequisites**: Validates Python version, required packages, and system services
2. **Database Connectivity**: Tests database connection and FrappePilot table structure
3. **Redis Connectivity**: Validates Redis connection and basic operations
4. **Ollama Service**: Tests Ollama API and model availability
5. **ERPNext Connectivity**: Validates ERPNext accessibility and API endpoints
6. **FrappePilot Installation**: Checks if FrappePilot app is properly installed
7. **DocType Validation**: Validates FrappePilot DocType structure and data
8. **API Endpoints**: Tests FrappePilot API endpoints (requires authentication)
9. **AI Functionality**: Tests AI integration and inference capabilities
10. **Permission System**: Validates role-based access control configuration
11. **Security Features**: Checks security configurations and restrictions
12. **Performance Metrics**: Measures system response times and performance

## Output

The test suite provides:

- Real-time console output with test results
- Detailed log file at `/tmp/frappepilot_test.log`
- Comprehensive test report at `/tmp/frappepilot_test_report_[timestamp].txt`

## Interpreting Results

- ✓ Green checkmarks indicate successful tests
- ⚠ Yellow warnings indicate potential issues that may not be critical
- ✗ Red X marks indicate failed tests that require attention

## Common Issues

### Database Connection Errors
- Verify database credentials in configuration
- Ensure MariaDB service is running
- Check database user permissions

### Ollama Service Errors
- Verify Ollama service is running: `sudo systemctl status ollama`
- Check if models are installed: `ollama list`
- Ensure Ollama is listening on correct port: `netstat -tlnp | grep 11434`

### ERPNext Connectivity Issues
- Verify ERPNext is running: `bench start` or check production setup
- Check if site is accessible in browser
- Verify bench and site configuration

### Permission Errors
- Ensure test user has appropriate roles
- Check AI Action Definition configurations
- Verify FrappePilot Settings are properly configured

## Troubleshooting

If tests fail, check the detailed log file for specific error messages. The log file contains comprehensive information about each test execution and can help identify the root cause of issues.

For additional troubleshooting, refer to the main FrappePilot Installation Guide.

## Support

For issues with the test suite or FrappePilot installation, please:

1. Review the detailed log files
2. Check the troubleshooting section in the installation guide
3. Ensure all prerequisites are properly installed
4. Verify system configuration matches requirements

## Test Suite Version

- Version: 1.0.0
- Compatible with: FrappePilot 1.0.0
- Last Updated: June 24, 2025

