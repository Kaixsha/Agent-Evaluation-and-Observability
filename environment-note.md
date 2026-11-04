# Environment Note

All three systems were reproduced and tested in a GitHub Codespaces Linux environment using isolated Python virtual environments.

The exact Python version and operating-system information captured during execution are preserved in the evidence pack:

- `evidence/system1/environment.txt`
- `evidence/system2/environment.txt`
- `evidence/system3/environment.txt`

Each system was executed from its own project directory using its local `.venv`. Test, static-analysis, behavioral, and perturbation outputs were captured with `tee` so that the submitted evidence reflects the actual terminal runs.
