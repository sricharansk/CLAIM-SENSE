<!-- Re-issued Markdown source from the earlier Claim Sense answer set; content preserved. -->

# Prompt 2 --- Saving Claim Sense and Other Projects to GitHub

## User Prompt

And I need to implement send save all my projects into my Github profile
is that possible and how can send save my files into github

## Answer

Yes. You can and should store Claim Sense and your other major projects
in GitHub.

For your situation, GitHub should become the central place for:

-   Source code
-   Documentation
-   Architecture
-   Experiments
-   Deployment configuration
-   Tests
-   Project history

## 1. Recommended Repository Structure

Use one repository per major project.

``` text
GitHub
└── sricharansk/
    ├── claim-sense/
    ├── site-guard-ai/
    ├── pet-segmentation-mobilenet-unet/
    ├── traffic-prediction/
    └── other-projects/
```

For Claim Sense:

``` text
claim-sense/
├── frontend/
├── backend/
├── ai/
│   ├── rag/
│   ├── agents/
│   ├── extraction/
│   └── evaluation/
├── adjudication/
├── ingestion/
├── data/
├── docs/
├── infrastructure/
├── tests/
├── .gitignore
├── README.md
├── requirements.txt
└── docker-compose.yml
```

## 2. What to Store

### Store

-   Python source code
-   Frontend code
-   API code
-   RAG code
-   Database schemas
-   Docker files
-   Kubernetes files
-   Documentation
-   Notebooks
-   Tests
-   Architecture diagrams
-   Configuration templates

### Never upload

-   `.env`
-   API keys
-   Passwords
-   Azure credentials
-   Private company documents
-   Customer claims
-   Personally identifiable information
-   Confidential company data

## 3. Company Project Safety

Because Claim Sense and Site Guard AI are being developed during company
training, start with:

``` text
claim-sense → Private
site-guard-ai → Private
```

Only make them public after receiving permission and sanitizing the
repositories.

Do not upload company-owned documents, real customer claims, internal
SOPs, private databases or credentials.

Instead use:

``` text
data/
├── sample/
├── synthetic/
└── README.md
```

## 4. First-Time Git Setup

Install Git from:

https://git-scm.com/

Check:

``` bash
git --version
```

Configure identity:

``` bash
git config --global user.name "S K Sricharan"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

## 5. Initialize Project

Inside your project directory:

``` bash
git init
```

Create `.gitignore`.

Recommended contents:

``` gitignore
__pycache__/
*.py[cod]
venv/
.venv/
env/

.env
.env.*
!.env.example

.ipynb_checkpoints/

.vscode/
.idea/

*.log
logs/

*.pt
*.pth
*.onnx
*.safetensors
*.bin

data/raw/
data/private/
data/company/

*.pem
*.key
credentials.json
service-account.json

node_modules/
.next/
dist/
build/

tmp/
temp/

.azure/

*.db
*.sqlite
*.sqlite3
```

Create `.env.example`:

``` env
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT=
AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_API_KEY=
POSTGRES_CONNECTION_STRING=
```

## 6. First Commit

Check:

``` bash
git status
```

Add files:

``` bash
git add .
```

Commit:

``` bash
git commit -m "Initial Claim Sense project setup"
```

## 7. Connect to GitHub

After creating the GitHub repository:

``` bash
git remote add origin https://github.com/YOUR_USERNAME/claim-sense.git
git branch -M main
git push -u origin main
```

## 8. Normal Development Workflow

Every time you make changes:

``` bash
git status
git add .
git commit -m "Implement policy document ingestion"
git push
```

Good commit messages include:

``` text
Add policy document ingestion pipeline
Implement hybrid RAG retrieval
Add claim document extraction
Add policy version matching
Implement adjudication rules engine
Add claim evidence generation
Add fraud risk scoring
Add human review workflow
Add Azure deployment configuration
```

Avoid:

``` text
update
changes
final
final2
latest
test
```

## 9. GitHub Project Management

Use GitHub Issues for work items:

``` text
CLAIM-SENSE-001 Set up architecture
CLAIM-SENSE-002 Implement PDF ingestion
CLAIM-SENSE-003 Implement OCR
CLAIM-SENSE-004 Implement policy chunking
CLAIM-SENSE-005 Implement hybrid retrieval
CLAIM-SENSE-006 Build claim extraction
CLAIM-SENSE-007 Implement adjudication
```

Use GitHub Projects with:

``` text
BACKLOG
↓
TODO
↓
IN PROGRESS
↓
TESTING
↓
DONE
```

## 10. GitHub Actions

Eventually implement:

``` text
git push
   ↓
GitHub Actions
   ↓
Tests
   ↓
Linting
   ↓
Security scan
   ↓
Docker build
   ↓
Deployment
```

## 11. Recommended Profile

Your profile can eventually contain:

``` text
S K Sricharan
AI / ML Engineer
M.Tech AI & ML

Featured Projects

Claim Sense
Insurance Claims Intelligence Platform

Site Guard AI
Construction Safety & Quality AI Platform

Traffic Prediction
ARIMA vs LSTM

Pet Segmentation
MobileNetV2-U-Net

TinyML Classroom Intelligence
Edge AI
```

The goal is for GitHub to demonstrate:

**AI + RAG + LLM + ML + Data Engineering + Backend + Cloud + Docker +
Deployment + Product Engineering.**

## 12. Recommended Immediate Structure

Create this first:

``` text
claim-sense/
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── frontend/
├── backend/
├── ai/
├── ingestion/
├── adjudication/
├── fraud/
├── data/
├── tests/
├── docs/
└── infrastructure/
```

Then:

``` bash
git add .
git commit -m "Initialize Claim Sense enterprise AI platform"
git push
```

The best workflow is to commit each major implementation phase
separately.
