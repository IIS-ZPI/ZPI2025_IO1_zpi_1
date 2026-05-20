# System Architecture

## Overview

The Currency Exchange Rate Change Analysis System is a command-line application built using a modular layered architecture. The system is responsible for retrieving historical currency exchange rate data from the National Bank of Poland (NBP) API, processing statistical calculations, and presenting the results to the user.

The application follows a separation-of-concerns approach, where individual modules are responsible for data retrieval, business logic, visualization, and user interaction.

---

## Architecture Layers

### 1. Presentation Layer

Responsible for communication with the user through the command-line interface (CLI).

Main responsibilities:
- reading user commands and parameters
- setting analysis settings
- starting application workflows

Main module:
- `src/app/cli/`

---

### 2. Application Layer

Coordinates application logic and data flow between modules.

Main responsibilities:
- validating user input,
- invoking data processing services
- controlling analysis execution.

Main module:
- `src/app/`

---

### 3. Data Processing Layer

Responsible for statistical analysis and transformation of exchange rate data.

Main responsibilities:
- calculating daily exchange rate changes
- aggregating data monthly or quarterly
- generating histogram-ready datasets
- exporting results to CSV files

---

### 4. Data Access Layer

Handles communication with external services.

Main responsibilities:
- sending HTTP requests
- retrieving historical exchange rate data from the NBP API
- parsing API responses

Technologies:
- `requests`
- NBP API

---

## External Dependencies

The system integrates with:

- National Bank of Poland (NBP) API — exchange rate data source
- GitHub Actions — automated testing and release pipeline

---

## Continuous Integration

The project uses GitHub Actions for:
- automatic unit testing
- release creation
- multi-platform build generation

---

## High-Level Data Flow

1. User executes a CLI command
2. The application validates input parameters
3. The data access layer retrieves exchange rate data from the NBP API
4. The processing layer performs statistical analysis
5. Results are displayed as histograms or exported to CSV files

---