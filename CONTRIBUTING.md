# Contributing to InfraPilot AI

We welcome contributions to InfraPilot AI!

## Development Guidelines

1. **Safety First**: Never allow the AI assistant to directly execute shell strings. All host and remote actions must pass through `SafeActionEngine` or `SSHService` with fixed templates, argument arrays, target validation, and explicit operator approval.
2. **Real Metrics**: Never fake or hardcode telemetry metrics. Use `psutil`, SSH diagnostic commands, or Linux `/proc` interfaces with proper permission error handling.
3. **SoloHost Compliance**: Keep `deployment/solohost/` aligned with the SoloHost publishing contract. Never introduce `privileged: true`, host bind mounts, or host network mode in the SoloHost package.
4. **Testing**: Run all unit and integration tests before submitting pull requests:
   ```bash
   PYTHONPATH=. pytest backend/tests/ agent/tests/ -v
   ```
