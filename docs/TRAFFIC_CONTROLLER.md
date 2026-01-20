# Traffic Controller - Technical Documentation

> Enables project previews using free external compute (WebContainers, Binder, Colab).

## Architecture Overview

```mermaid
flowchart LR
    subgraph User
        U[Submit Project URL]
    end
    
    subgraph Kiri Backend
        H[Huey Task Queue]
        AI[AI Classifier]
        GS[Gist Service]
    end
    
    subgraph External Free Compute
        WC[WebContainer<br/>Browser]
        BD[Binder<br/>mybinder.org]
        CL[Colab<br/>Google GPU]
    end
    
    U --> H
    H --> AI
    AI --> |Lane A| WC
    AI --> |Lane B| GS --> BD
    AI --> |Lane C| GS --> CL
```

## Lane Classification

| Lane | Badge | Criteria | Infrastructure |
|------|-------|----------|----------------|
| **A** | 🟢 Instant Run | React, Vue, Node.js, static sites | **Kiri Studio** (Built-in IDE) |
| **B** | 🟠 Cloud Boot | Django, Flask, FastAPI, Docker | [mybinder.org](https://mybinder.org) |
| **C** | 🔴 GPU Powered | PyTorch, TensorFlow, Transformers | [Google Colab](https://colab.research.google.com) |

## Files

| File | Purpose |
|------|---------|
| `core/ai_service.py` | Gemini + Groq classification |
| `projects/gist_service.py` | GitHub Gist creation for Binder/Colab |
| `projects/models.py` | `lane`, `execution_url`, `gist_id` fields |
| `kiri_project/tasks.py` | `classify_project_lane()` background task |

## API Keys Required

```bash
# .env
GEMINI_API_KEY=...        # aistudio.google.com/apikey
GROQ_API_KEY=...          # console.groq.com/keys
KIRI_BOT_GITHUB_TOKEN=... # GitHub PAT with 'gist' scope
KIRI_BOT_USERNAME=...     # GitHub username for bot
```

## Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant K as Kiri
    participant G as GitHub
    participant AI as Gemini/Groq
    participant GH as Gists
    
    U->>K: Submit project URL
    K->>G: Fetch repo structure
    K->>AI: Classify lane
    AI-->>K: {lane, reason, command}
    
    alt Lane B or C
        K->>AI: Generate config
        K->>GH: Create Gist
        GH-->>K: Gist ID
        K->>K: Build URL
    end
    
    K->>U: Project with badge + launch button
```

## URL Formats

**Binder (Lane B):**
```
https://mybinder.org/v2/gist/{username}/{gist_id}/HEAD?urlpath=proxy/{port}/
```

**Colab (Lane C):**
```
https://colab.research.google.com/gist/{username}/{gist_id}/demo.ipynb
```

## Free Tier Limits

| Service | Limit |
|---------|-------|
| Gemini 2.5 Flash | 250 req/day |
| Groq | 1000 req/day |
| Binder | 1-2GB RAM, 10min idle |
| Colab | T4 GPU, ~12hr sessions |
| GitHub Gists | Unlimited |

## Testing

```bash
uv run python test_traffic_controller.py
```
