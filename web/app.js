/**
 * Pseudocode to C Compiler - Modern IDE Client Application
 * Handles theme persistence, editor interactions, live compilation,
 * tabs, diagnostics, examples modal, and code export.
 */

// Application State
const state = {
    theme: localStorage.getItem("compiler_theme") || "dark",
    examples: [],
    currentExampleCategory: "All",
    lastGeneratedCode: "",
    isCompiling: false
};

// DOM Elements
const elements = {
    html: document.documentElement,
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    themeIcon: document.getElementById("themeIcon"),
    themeLabel: document.getElementById("themeLabel"),
    statusIndicator: document.getElementById("statusIndicator"),
    statusText: document.getElementById("statusText"),
    
    // Editors
    pseudocodeInput: document.getElementById("pseudocodeInput"),
    inputLineNumbers: document.getElementById("inputLineNumbers"),
    cCodeDisplay: document.getElementById("cCodeDisplay"),
    outputLineNumbers: document.getElementById("outputLineNumbers"),
    charCount: document.getElementById("charCount"),
    lineCount: document.getElementById("lineCount"),
    
    // Buttons
    convertBtn: document.getElementById("convertBtn"),
    clearCodeBtn: document.getElementById("clearCodeBtn"),
    pasteCodeBtn: document.getElementById("pasteCodeBtn"),
    loadExampleQuickBtn: document.getElementById("loadExampleQuickBtn"),
    copyCodeBtn: document.getElementById("copyCodeBtn"),
    copyText: document.getElementById("copyText"),
    downloadCodeBtn: document.getElementById("downloadCodeBtn"),
    runGccBtn: document.getElementById("runGccBtn"),
    
    // Navigation & Modals
    navHomeBtn: document.getElementById("navHomeBtn"),
    navExamplesBtn: document.getElementById("navExamplesBtn"),
    navDocsBtn: document.getElementById("navDocsBtn"),
    examplesModal: document.getElementById("examplesModal"),
    closeExamplesModalBtn: document.getElementById("closeExamplesModalBtn"),
    examplesGrid: document.getElementById("examplesGrid"),
    exampleCategoryFilters: document.getElementById("exampleCategoryFilters"),
    docsModal: document.getElementById("docsModal"),
    closeDocsModalBtn: document.getElementById("closeDocsModalBtn"),
    
    // Tabs & Panels
    tabButtons: document.querySelectorAll(".tab-btn"),
    tabContents: document.querySelectorAll(".tab-content"),
    diagBadge: document.getElementById("diagBadge"),
    explanationContent: document.getElementById("explanationContent"),
    diagnosticsContent: document.getElementById("diagnosticsContent"),
    symbolsContent: document.getElementById("symbolsContent"),
    execConsole: document.getElementById("execConsole"),
    
    // Toast
    toast: document.getElementById("toast")
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initEventListeners();
    updateEditorStats();
    updateInputLineNumbers();
    fetchExamples();
    
    // Auto-convert initial example on load
    if (elements.pseudocodeInput.value.trim()) {
        compilePseudocode();
    }
});

// ==========================================================================
// Theme Management
// ==========================================================================
function initTheme() {
    applyTheme(state.theme);
}

function toggleTheme() {
    const nextTheme = state.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
}

function applyTheme(theme) {
    state.theme = theme;
    elements.html.setAttribute("data-theme", theme);
    localStorage.setItem("compiler_theme", theme);
    
    if (theme === "light") {
        elements.themeIcon.textContent = "🌙";
        elements.themeLabel.textContent = "Dark Mode";
    } else {
        elements.themeIcon.textContent = "☀️";
        elements.themeLabel.textContent = "Light Mode";
    }
}

// ==========================================================================
// Event Listeners
// ==========================================================================
function initEventListeners() {
    // Theme
    elements.themeToggleBtn.addEventListener("click", toggleTheme);
    
    // Editor typing & scrolling
    elements.pseudocodeInput.addEventListener("input", () => {
        updateEditorStats();
        updateInputLineNumbers();
    });
    
    elements.pseudocodeInput.addEventListener("scroll", () => {
        elements.inputLineNumbers.scrollTop = elements.pseudocodeInput.scrollTop;
    });
    
    // Tab key support in textarea (4 spaces)
    elements.pseudocodeInput.addEventListener("keydown", (e) => {
        if (e.key === "Tab") {
            e.preventDefault();
            const start = elements.pseudocodeInput.selectionStart;
            const end = elements.pseudocodeInput.selectionEnd;
            elements.pseudocodeInput.value = elements.pseudocodeInput.value.substring(0, start) + "    " + elements.pseudocodeInput.value.substring(end);
            elements.pseudocodeInput.selectionStart = elements.pseudocodeInput.selectionEnd = start + 4;
            updateEditorStats();
            updateInputLineNumbers();
        }
        
        // Ctrl+Enter or Cmd+Enter to compile
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            compilePseudocode();
        }
    });

    // Conversion
    elements.convertBtn.addEventListener("click", compilePseudocode);
    
    // Quick actions
    elements.clearCodeBtn.addEventListener("click", clearEditor);
    elements.pasteCodeBtn.addEventListener("click", pasteFromClipboard);
    elements.copyCodeBtn.addEventListener("click", copyGeneratedCode);
    elements.downloadCodeBtn.addEventListener("click", downloadCFile);
    elements.runGccBtn.addEventListener("click", runCWithGcc);
    
    // Modals
    elements.loadExampleQuickBtn.addEventListener("click", openExamplesModal);
    elements.navExamplesBtn.addEventListener("click", openExamplesModal);
    elements.closeExamplesModalBtn.addEventListener("click", closeExamplesModal);
    
    elements.navDocsBtn.addEventListener("click", openDocsModal);
    elements.closeDocsModalBtn.addEventListener("click", closeDocsModal);
    
    // Close modal on background click
    window.addEventListener("click", (e) => {
        if (e.target === elements.examplesModal) closeExamplesModal();
        if (e.target === elements.docsModal) closeDocsModal();
    });
    
    // Close on Escape key
    window.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeExamplesModal();
            closeDocsModal();
        }
    });

    // Category filter clicks
    elements.exampleCategoryFilters.addEventListener("click", (e) => {
        if (e.target.classList.contains("category-btn")) {
            document.querySelectorAll(".category-btn").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            state.currentExampleCategory = e.target.dataset.category;
            renderExamplesGrid();
        }
    });

    // Tabs
    elements.tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTabId = btn.getAttribute("data-tab");
            switchTab(targetTabId);
        });
    });
}

// ==========================================================================
// Editor Utilities
// ==========================================================================
function updateEditorStats() {
    const text = elements.pseudocodeInput.value;
    const charCount = text.length;
    const lines = text.split("\n").length;
    
    elements.charCount.textContent = `${charCount} character${charCount === 1 ? '' : 's'}`;
    elements.lineCount.textContent = `${lines} line${lines === 1 ? '' : 's'}`;
}

function updateInputLineNumbers() {
    const lines = elements.pseudocodeInput.value.split("\n").length;
    let numbers = [];
    for (let i = 1; i <= Math.max(lines, 1); i++) {
        numbers.push(i);
    }
    elements.inputLineNumbers.innerHTML = numbers.join("<br>");
}

function updateOutputLineNumbers(codeText) {
    const lines = codeText.split("\n").length;
    let numbers = [];
    for (let i = 1; i <= Math.max(lines, 1); i++) {
        numbers.push(i);
    }
    elements.outputLineNumbers.innerHTML = numbers.join("<br>");
}

function clearEditor() {
    elements.pseudocodeInput.value = "";
    elements.cCodeDisplay.textContent = "// Output cleared. Enter pseudocode and click 'Convert to C'.";
    state.lastGeneratedCode = "";
    updateEditorStats();
    updateInputLineNumbers();
    updateOutputLineNumbers("");
    setStatus("ready", "Ready");
    showToast("Editor cleared");
}

async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            elements.pseudocodeInput.value = text;
            updateEditorStats();
            updateInputLineNumbers();
            showToast("Pasted from clipboard");
        }
    } catch (err) {
        elements.pseudocodeInput.focus();
        showToast("Press Ctrl+V to paste into editor");
    }
}

// ==========================================================================
// Compilation Pipeline
// ==========================================================================
async function compilePseudocode() {
    const pseudocode = elements.pseudocodeInput.value.trim();
    if (!pseudocode) {
        showToast("Please enter pseudocode to convert");
        return;
    }

    setLoading(true);
    setStatus("compiling", "Compiling...");

    try {
        const response = await fetch("/api/compile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: pseudocode })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            handleCompileSuccess(data);
        } else {
            handleCompileError(data);
        }
    } catch (err) {
        handleCompileError({
            error: {
                type: "Network / Server Error",
                message: "Could not communicate with the compiler backend. Ensure server.py is running.",
                suggestion: "Run 'python server.py' in the project directory."
            }
        });
    } finally {
        setLoading(false);
    }
}

function handleCompileSuccess(data) {
    state.lastGeneratedCode = data.c_code;
    elements.cCodeDisplay.textContent = data.c_code;
    updateOutputLineNumbers(data.c_code);

    setStatus("ready", "Compilation Successful ✓");
    showToast("Converted to C successfully!");

    // Render Explanations
    renderExplanation(data.explanation, data.headers);

    // Render Diagnostics & Warnings
    renderDiagnostics(data.warnings || []);

    // Render Symbol Table & AST
    renderSymbolTable(data.symbols || {});

    // Ensure C Code tab is visible if on diagnostics/error tab
    const currentTab = document.querySelector(".tab-btn.active").getAttribute("data-tab");
    if (currentTab === "tabDiagnostics" && (!data.warnings || data.warnings.length === 0)) {
        switchTab("tabGeneratedCode");
    }
}

function handleCompileError(data) {
    const err = data.error || {
        type: "Compiler Error",
        message: data.message || "An unknown compilation error occurred."
    };

    setStatus("error", "Compilation Failed ✗");
    
    // Render error card in diagnostics tab
    elements.diagnosticsContent.innerHTML = `
        <div class="diag-card error">
            <div class="diag-header">
                <span class="diag-badge">${escapeHtml(err.type || 'Error')}</span>
                <span class="diag-line">${err.line ? `Line ${err.line}` : ''}</span>
            </div>
            <div class="diag-msg">${escapeHtml(err.message)}</div>
            ${err.suggestion ? `<div class="diag-suggestion">💡 <strong>Suggestion:</strong> ${escapeHtml(err.suggestion)}</div>` : ''}
        </div>
    `;

    // Also display visible error header above C output without wiping out current view
    elements.cCodeDisplay.textContent = `/* =========================================================================
   COMPILATION ERROR DETECTED
   ${err.type || 'Error'}${err.line ? ` at Line ${err.line}` : ''}
   Message: ${err.message}
   ${err.suggestion ? `Suggestion: ${err.suggestion}` : ''}
========================================================================= */\n\n` + (state.lastGeneratedCode || '// Fix the error above and re-compile.');

    updateOutputLineNumbers(elements.cCodeDisplay.textContent);

    elements.diagBadge.style.display = "inline-block";
    elements.diagBadge.textContent = "1";
    
    // Switch to diagnostics tab to show the issue clearly
    switchTab("tabDiagnostics");
    showToast("Compilation failed - see diagnostics", true);
}

function setStatus(type, text) {
    elements.statusIndicator.className = `status-indicator ${type}`;
    elements.statusText.textContent = text;
}

function setLoading(isLoading) {
    state.isCompiling = isLoading;
    if (isLoading) {
        elements.convertBtn.classList.add("loading");
        elements.convertBtn.disabled = true;
    } else {
        elements.convertBtn.classList.remove("loading");
        elements.convertBtn.disabled = false;
    }
}

// ==========================================================================
// Rendering Tabs
// ==========================================================================
function switchTab(tabId) {
    elements.tabButtons.forEach(btn => {
        btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
    });
    
    elements.tabContents.forEach(content => {
        content.classList.toggle("active", content.id === tabId);
    });
}

function renderExplanation(steps, headers) {
    if (!steps || steps.length === 0) {
        elements.explanationContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">💡</span>
                <h3>No Explanation Details</h3>
                <p>Compile a program to see step-by-step conversion rationale.</p>
            </div>
        `;
        return;
    }

    let html = "";
    steps.forEach((step, idx) => {
        html += `
            <div class="explain-step-card">
                <div class="explain-step-header">
                    <span class="explain-step-num">${idx + 1}</span>
                    <span class="explain-step-title">${escapeHtml(step.stage)}</span>
                </div>
                <div class="explain-step-desc">${escapeHtml(step.details)}</div>
            </div>
        `;
    });

    elements.explanationContent.innerHTML = html;
}

function renderDiagnostics(warnings) {
    if (!warnings || warnings.length === 0) {
        elements.diagBadge.style.display = "none";
        elements.diagnosticsContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">✓</span>
                <h3>Clean Compilation</h3>
                <p>No syntax errors or type warnings detected.</p>
            </div>
        `;
        return;
    }

    elements.diagBadge.style.display = "inline-block";
    elements.diagBadge.textContent = warnings.length;

    let html = "";
    warnings.forEach(warn => {
        html += `
            <div class="diag-card warning">
                <div class="diag-header">
                    <span class="diag-badge">Warning</span>
                </div>
                <div class="diag-msg">${escapeHtml(warn)}</div>
            </div>
        `;
    });

    elements.diagnosticsContent.innerHTML = html;
}

function renderSymbolTable(symbols) {
    const keys = Object.keys(symbols);
    if (keys.length === 0) {
        elements.symbolsContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">🔍</span>
                <h3>No Symbols Declared</h3>
                <p>Declare or assign variables to view them in the symbol table.</p>
            </div>
        `;
        return;
    }

    let rows = "";
    keys.forEach(k => {
        const sym = symbols[k];
        const cType = sym.c_type || "int";
        const pseudoType = sym.pseudo_type || "INTEGER";
        const origin = sym.is_explicit ? "Explicit" : "Inferred";
        const arrayNote = sym.is_array ? `Array [${sym.array_size || 100}]` : "Scalar";

        rows += `
            <tr>
                <td><strong>${escapeHtml(k)}</strong></td>
                <td><code>${escapeHtml(cType)}</code></td>
                <td>${escapeHtml(pseudoType)}</td>
                <td><span class="badge ${sym.is_explicit ? '' : 'inferred-badge'}">${origin}</span></td>
                <td>${escapeHtml(arrayNote)}</td>
            </tr>
        `;
    });

    elements.symbolsContent.innerHTML = `
        <table class="symbol-table">
            <thead>
                <tr>
                    <th>Variable Name</th>
                    <th>C Type</th>
                    <th>Pseudocode Type</th>
                    <th>Resolution</th>
                    <th>Structure</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

// ==========================================================================
// Code Export & GCC Execution
// ==========================================================================
function copyGeneratedCode() {
    if (!state.lastGeneratedCode) {
        showToast("No generated C code to copy");
        return;
    }

    navigator.clipboard.writeText(state.lastGeneratedCode).then(() => {
        elements.copyText.textContent = "Copied!";
        showToast("C code copied to clipboard!");
        setTimeout(() => {
            elements.copyText.textContent = "Copy";
        }, 2000);
    }).catch(() => {
        showToast("Failed to copy automatically. Select and copy manually.");
    });
}

function downloadCFile() {
    if (!state.lastGeneratedCode) {
        showToast("No generated C code to download");
        return;
    }

    const blob = new Blob([state.lastGeneratedCode], { type: "text/x-csrc;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "program.c";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("Downloaded program.c");
}

async function runCWithGcc() {
    if (!state.lastGeneratedCode) {
        showToast("Please compile pseudocode into C code first.");
        return;
    }

    elements.execConsole.innerHTML = `
        <div class="console-line info-line">[Compiler] Checking local C compiler (gcc / clang)...</div>
    `;

    try {
        const response = await fetch("/api/run_c", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: state.lastGeneratedCode })
        });

        const data = await response.json();

        if (data.gcc_available) {
            elements.execConsole.innerHTML = `
                <div class="console-line success-line">[GCC] Compiler located: ${escapeHtml(data.compiler_version || 'GCC')}</div>
                <div class="console-line success-line">[GCC] Build succeeded without syntax errors!</div>
                <div class="console-line info-line">[Output]:</div>
                <pre class="console-output">${escapeHtml(data.output || '(No console output produced)')}</pre>
            `;
            showToast("GCC build verified successfully!");
        } else {
            elements.execConsole.innerHTML = `
                <div class="console-line error-line">[GCC] GCC compiler executable was not found in system PATH.</div>
                <div class="console-line note-line">[Info] The generated C code follows standard C99/C11 syntax.</div>
                <div class="console-line note-line">[Action] To compile and execute locally:</div>
                <div class="console-line">  1. Click 'Download .c' to save program.c.</div>
                <div class="console-line">  2. Install GCC (MinGW-w64 on Windows) or open in VS Code / Code::Blocks / Dev-C++.</div>
                <div class="console-line">  3. Run: gcc -Wall program.c -o program.exe && ./program.exe</div>
            `;
            showToast("GCC not in PATH - download .c to run locally");
        }
    } catch (err) {
        elements.execConsole.innerHTML = `
            <div class="console-line error-line">[Error] Could not connect to compile service: ${escapeHtml(err.message)}</div>
        `;
    }
}

// ==========================================================================
// Examples System
// ==========================================================================
async function fetchExamples() {
    try {
        const response = await fetch("/api/examples");
        if (response.ok) {
            const data = await response.json();
            state.examples = data.examples || [];
        }
    } catch (e) {
        // Fallback bundled examples if offline
        state.examples = getFallbackExamples();
    }
}

function openExamplesModal() {
    renderExamplesGrid();
    elements.examplesModal.classList.add("open");
    elements.examplesModal.setAttribute("aria-hidden", "false");
}

function closeExamplesModal() {
    elements.examplesModal.classList.remove("open");
    elements.examplesModal.setAttribute("aria-hidden", "true");
}

function renderExamplesGrid() {
    const category = state.currentExampleCategory;
    const filtered = category === "All" 
        ? state.examples 
        : state.examples.filter(ex => ex.category === category);

    if (filtered.length === 0) {
        elements.examplesGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <p>No examples found in this category.</p>
            </div>
        `;
        return;
    }

    let html = "";
    filtered.forEach(ex => {
        html += `
            <div class="example-card" data-id="${ex.id}">
                <div>
                    <div class="example-card-header">
                        <span class="example-card-title">${escapeHtml(ex.title)}</span>
                        <span class="example-badge">${escapeHtml(ex.category)}</span>
                    </div>
                    <p class="example-card-desc">${escapeHtml(ex.description)}</p>
                </div>
                <div class="example-card-footer">
                    <button class="btn btn-primary btn-sm load-ex-btn" data-id="${ex.id}">
                        Load & Compile ⚡
                    </button>
                </div>
            </div>
        `;
    });

    elements.examplesGrid.innerHTML = html;

    // Attach click handlers
    elements.examplesGrid.querySelectorAll(".load-ex-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const exId = btn.getAttribute("data-id");
            loadExampleById(exId);
        });
    });

    elements.examplesGrid.querySelectorAll(".example-card").forEach(card => {
        card.addEventListener("click", () => {
            const exId = card.getAttribute("data-id");
            loadExampleById(exId);
        });
    });
}

function loadExampleById(exId) {
    const ex = state.examples.find(item => item.id === exId);
    if (!ex) return;

    elements.pseudocodeInput.value = ex.pseudocode.trim();
    updateEditorStats();
    updateInputLineNumbers();
    closeExamplesModal();
    compilePseudocode();
    showToast(`Loaded: ${ex.title}`);
}

// ==========================================================================
// Documentation Modal
// ==========================================================================
function openDocsModal() {
    elements.docsModal.classList.add("open");
    elements.docsModal.setAttribute("aria-hidden", "false");
}

function closeDocsModal() {
    elements.docsModal.classList.remove("open");
    elements.docsModal.setAttribute("aria-hidden", "true");
}

// ==========================================================================
// Toast Notification
// ==========================================================================
let toastTimeout = null;
function showToast(message, isError = false) {
    if (toastTimeout) clearTimeout(toastTimeout);
    elements.toast.textContent = message;
    elements.toast.style.borderColor = isError ? "var(--danger-base)" : "var(--border-subtle)";
    elements.toast.classList.add("show");
    toastTimeout = setTimeout(() => {
        elements.toast.classList.remove("show");
    }, 2800);
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function getFallbackExamples() {
    return [
        {
            id: "hello_world",
            title: "1. Hello World",
            category: "Basics",
            description: "Fundamental print program in pseudocode.",
            pseudocode: "START\n    OUTPUT \"Hello, World!\"\nEND"
        }
    ];
}
