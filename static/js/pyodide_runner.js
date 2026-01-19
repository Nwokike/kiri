// Pyodide Runner for Kiri Research Labs
// Handles client-side execution of Python code blocks

let pyodide = null;
let pyodideOutput = null;

async function loadPyodideEnvironment() {
    if (pyodide) return pyodide;

    const statusEl = document.getElementById('pyodide-status');
    if (statusEl) statusEl.innerText = 'Loading Python kernel...';

    console.log("Loading Pyodide...");
    pyodide = await loadPyodide();
    console.log("Pyodide loaded.");

    // Load common scientific packages
    await pyodide.loadPackage("micropip");
    // await pyodide.loadPackage(["numpy", "pandas"]); // Load on demand instead to save bandwidth

    if (statusEl) statusEl.innerText = 'Kernel Ready';
    return pyodide;
}

window.runPythonCode = async function (code, outputElementId) {
    const outputEl = document.getElementById(outputElementId);
    if (!outputEl) return;

    // Clear previous output
    outputEl.innerText = '';
    outputEl.innerHTML = '<span class="text-text-tertiary">Running...</span>';

    try {
        if (!pyodide) {
            await loadPyodideEnvironment();
        }

        // Capture stdout
        pyodide.setStdout({
            batched: (msg) => {
                outputEl.innerText += msg + "\n";
            }
        });

        // Run
        let result = await pyodide.runPythonAsync(code);

        // If result is not undefined and we didn't print anything, show result
        if (result !== undefined && outputEl.innerText === '<span class="text-text-tertiary">Running...</span>') {
            outputEl.innerText = result;
        } else if (result !== undefined) {
            outputEl.innerText += "\n[Result]: " + result;
        }

    } catch (err) {
        // Use textContent for XSS safety - error message could contain user input
        outputEl.textContent = `Error: ${err}`;
        outputEl.className = 'text-error font-bold';
        console.error(err);
    }
};

// Initialize interactive blocks
document.addEventListener('DOMContentLoaded', () => {
    // Find all 'run-python-btn'
    const buttons = document.querySelectorAll('.run-python-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const code = btn.dataset.code;
            const outputId = btn.dataset.output;
            window.runPythonCode(code, outputId);
        });
    });
});
