# ZPI2025_IO1_zpi_1
## Currency Exchange Rate Change Analysis System

### Table of contents

1. [About the project](#about-the-project)
2. [Tech stack](#tech-stack)
3. [Running the application](#running-the-application)
4. [Continuous integration](#continuous-integration)
5. [Backlog](#backlog)
6. [Project structure](#project-structure)

---

## About the project

This is a command-line application designed to analyze currency exchange rate fluctuations. The system retrieves historical exchange rate data from the National Bank of Poland (NBP) API and processes it to generate statistical distributions of daily changes aggregated over monthly or quarterly periods. The results can be exported to a CSV file and use for further analysis, for example to create histogram.

---

## Tech stack

The project uses:

- Python 3.12+
  - pytest
  - requests
- GitHub Actions (CI/CD)

---

## Running the application

### Building project from source

``` bash
pip install --upgrade -r requirements.txt # install dependencies
cd src
py -m src.app.main # run
```

### Running release executables
- Windows - run `app-windows-latest.exe` file
- Linux - run in terminal `./app-ubuntu-latest`
- MacOS - run in terminal `./app-macos-latest`

---

## Backlog

We use GitHub Projects to track project progress, bugs, and tasks.

Link: https://github.com/orgs/IIS-ZPI/projects/33

---

## Continuous integration

The project uses GitHub Actions to automatically test and build releases.

- Branches `develop` and `release` are tested on every push and pull request
- Merging or pushing to `release` triggers a new release build
- Versioning starts from 2.0.0
- Executables are generated for Windows, Linux, and macOS

Releases:
https://github.com/IIS-ZPI/ZPI2025_IO1_zpi_1/releases

---

## Project structure

`src/app/` – application source code

`tests/` – test source code

`docs/` – main documentation

`docs/tests/` – test reports

`docs/diagrams/` – project diagrams

`.github/workflows/` – CI configuration
