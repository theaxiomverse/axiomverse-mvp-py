# AxiomVerse Deployment instruction v1.0.0

## Deployment for verified master nodes & Bootnodes only!

*Make sure* you have applied for master node before running this script or it will not work. Follow the instructions that was sent to you upon acceptation of your master node application to store your POM (proof of master) token.

Here are the complete capabilities and workflow of the deploy.sh script:

1. **Prerequisite Checks and Setup**:
   ```bash
   # Check and install base requirements
   ./deploy.sh --verbose
   ```
   - Checks Docker and Docker Compose installation
   - Verifies and installs liboqs and python-oqs
   - Sets up required directories and configurations

2. **OQS Management**:
   ```bash
   # Force reinstall of OQS libraries
   ./deploy.sh --force-oqs
   ```
   - Clones latest liboqs from GitHub
   - Builds and installs liboqs
   - Installs python-oqs bindings
   - Updates Dockerfile with OQS dependencies

3. **Testing**:
   ```bash
   # Run tests before deployment
   ./deploy.sh --run-tests
   ```
   - Runs pytest suite in isolated container
   - Checks code coverage
   - Validates functionality

4. **Clean Deployment**:
   ```bash
   # Full clean deployment
   ./deploy.sh --no-cache --force-oqs --force-certs
   ```
   - Rebuilds all containers from scratch
   - Reinstalls OQS libraries
   - Regenerates certificates
   - Performs complete health checks

5. **Advanced Usage**:
   ```bash
   # Complete setup with all options
   ./deploy.sh --force-oqs --no-cache --run-tests --verbose --force-certs
   ```
   This will:
   - Force OQS reinstallation
   - Clean build all containers
   - Run test suite
   - Generate new certificates
   - Show detailed output
   - Perform health checks

6. **Maintenance Operations**:
   ```bash
   # Cleanup resources
   ./deploy.sh --cleanup
   
   # Skip health checks
   ./deploy.sh --no-health
   ```

7. **Service Access**:
   After successful deployment, you can access:
   - API: http://localhost:8000
   - Vault UI: http://localhost:8200
   - Grafana: http://localhost:3000
   - Prometheus: http://localhost:9090
   - NATS Monitoring: http://localhost:8222

8. **Directory Structure Created/Managed**:
   ```
   .
   ├── app/                 # Application code
   ├── modules/            # Python modules
   ├── vendor/            # Third-party files
   ├── certs/             # SSL certificates
   ├── vault/
   │   ├── config/       # Vault configuration
   │   ├── logs/         # Vault logs
   │   └── file/         # Vault data
   ├── nats/
   │   └── config/       # NATS configuration
   ├── prometheus/       # Prometheus configuration
   ├── grafana/
   │   └── provisioning/ # Grafana configuration
   ├── secrets/          # Secret files
   ├── liboqs/           # OQS library source
   └── python-oqs/       # Python OQS bindings
   ```

9. **Error Handling**:
   - Detailed error messages with line numbers
   - Colored output for better readability
   - Verbose mode for debugging
   - Proper cleanup on failure

10. **Security Features**:
    - Secure secret generation
    - Proper file permissions
    - SSL/TLS support
    - Vault integration
    - Non-root container execution
