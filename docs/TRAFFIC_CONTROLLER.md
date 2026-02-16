# Kiri Traffic Controller (KTC)

The Traffic Controller is the "Brain" of Kiri. It analyzes GitHub repositories and routes them to the most efficient execution environment (Lane) based on their contents.

## The 4-Lane Architecture

We have moved away from the generic "Browser Lane" to two specialized engines.

| Lane | Name | Engine | Best For | Start Time |
| :--- | :--- | :--- | :--- | :--- |
| **P** | **PyStudio** | **Pyodide (WASM)** | Data Science, Pandas, Numpy, Simple Python Scripts, Algorithms. | Instant |
| **J** | **JS Studio** | **WebContainer (Node)** | React, Vue, Next.js, Node.js, Static Sites, Vite. | ~5s (Boot) |
| **B** | **Binder** | **Docker (Cloud)** | Django, Flask, FastAPI, Go, Rust, SQL Databases. | ~60s |
| **C** | **Colab** | **GPU Cluster** | PyTorch, TensorFlow, Transformers, LLM Training. | ~10s |

## Classification Logic (AI + Heuristics)

The classification happens in `core.ai_service.AIService`.

### Lane P (PyStudio)
* **Triggers:**
    * `requirements.txt` exists but contains NO web frameworks (Django/Flask) and NO GPU libs (Torch).
    * Simple `.py` files found in root.
    * `Jupyter Notebooks` (*.ipynb).
* **Constraints:** No socket binding, no heavy system calls.

### Lane J (JS Studio)
* **Triggers:**
    * `package.json` exists.
    * Presence of `vite.config.js`, `next.config.js`.
    * Pure HTML/CSS/JS files.
* **Constraints:** Runs in-browser Node.js. Can run `npm run dev`.

### Lane B (Cloud Container)
* **Triggers:**
    * `dockerfile` exists.
    * `requirements.txt` contains `django`, `flask`, `fastapi`, `uvicorn`.
    * Needs a real Linux kernel or specific ports exposed.

### Lane C (GPU Cluster)
* **Triggers:**
    * `requirements.txt` contains `torch`, `tensorflow`, `transformers`, `cuda`.
    * Deep Learning or LLM workloads.

## Override Mechanism

Admins can manually override the Lane in the Django Admin if the AI misclassifies a project (e.g., a "Django" project that is actually just a tutorial script).