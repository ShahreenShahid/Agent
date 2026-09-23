# Space Fractions Code Agent

This repository contains an autonomous Python code agent that turns architecture documentation and PlantUML views into a runnable Space Fractions Node.js repository.

## Agent Architecture

The workflow follows Claude Code-style execution principles:

1. **Document ingestion**: `agent.py` reads `Architecture_Documentation.md` and `Architecture_View.md` from disk.
2. **Structured JSON planning**: Gemini converts the architecture into `output/architecture_plan.json`. The plan contains the project name and a list of repository files with descriptions.
3. **Autonomous file generation**: The agent sends targeted architecture context to Gemini for each planned file, removes accidental Markdown fences, creates nested directories, and writes complete files under `output/space-fractions/`.
4. **Verification**: The generated Node.js project can be installed and tested with its npm scripts.

The agent discovers currently available Gemini models with `client.models.list()`, prioritizes text-generation Flash and Pro models, and uses the Google GenAI Chat API for generation.

## Repository Inputs

The default input files are:

- `Architecture_Documentation.md`: system requirements, REST/OpenAPI details, protobuf contracts, SQL DDL, Kubernetes deployment information, security, operations, and testing strategy.
- `Architecture_View.md`: the 11 PlantUML views covering use cases, classes, objects, state, activity, sequence, collaboration, packages, components, deployment, and containers.

Alternative paths can be supplied with `--documentation` and `--view`.

## Generated Outputs

After a successful run:

- `output/architecture_plan.json`: normalized execution plan with `project_name: "space-fractions"`.
- `output/space-fractions/`: generated Node.js project.
- `output/space-fractions/package.json`: npm scripts and dependencies.
- `output/space-fractions/src/`: application and game, question, and user components.
- `output/space-fractions/test/`: Jest and Supertest tests.
- `output/space-fractions/sql/`: PostgreSQL DDL files.
- `output/space-fractions/proto/`: internal protobuf contract.
- `output/space-fractions/openapi.yaml`: public API contract.
- `output/space-fractions/k8s/`: Kubernetes deployment manifest.

The plan guarantees the required course artifacts are present. Gemini may add useful supporting files such as `Dockerfile` or `env.example`.

## Prerequisites

Install:

- Python 3.10 or newer
- Node.js 18 or newer and npm
- A valid Gemini API key with access to a text-generation model

Do not commit `.env` files or API keys. The key must be available through `GEMINI_API_KEY`.

## Quickstart: Bash, macOS, Linux, or Git Bash

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install google-genai python-dotenv
export GEMINI_API_KEY="YOUR_REAL_GEMINI_API_KEY"
python agent.py
cd output/space-fractions
npm install
npm test
```

The single command that triggers the complete planning and generation workflow is:

```bash
python agent.py
```

To use a different output directory:

```bash
python agent.py --output generated
```

## Quickstart: Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install google-genai python-dotenv
$env:GEMINI_API_KEY = "YOUR_REAL_GEMINI_API_KEY"
python agent.py
Set-Location output\space-fractions
npm install
npm test
```

## Quickstart: Windows Command Prompt

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install google-genai python-dotenv
set "GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY"
python agent.py
cd output\space-fractions
npm install
npm test
```

In Command Prompt, `GEMINI_MODEL` is optional. Leave it unset for automatic model discovery. If you set it, use a model name, never an API key:

```cmd
set "GEMINI_MODEL="
```

## Verification

The generated project's test command is defined in `output/space-fractions/package.json`:

```bash
npm test
```

Additional checks are available when supported by the generated project:

```bash
npm run test:coverage
npm run lint
```

A successful evaluation should show Jest passing and the agent's final log:

```text
[3/3] Generation complete.
```

To verify the generated file count from the repository root in PowerShell:

```powershell
(Get-ChildItem output\space-fractions -Recurse -File).Count
```

## CLI Options

```text
python agent.py --help
```

Available options:

- `--documentation PATH`: architecture documentation input.
- `--view PATH`: PlantUML architecture view input.
- `--output PATH`: parent directory for `architecture_plan.json` and the generated project.

## Security Notes

API keys are secrets. Use a temporary environment variable for local testing, revoke keys that have been pasted into chat, terminals, or source files, and remove the key from the environment when finished.
