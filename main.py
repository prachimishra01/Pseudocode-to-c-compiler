"""
Main Desktop Application and Entry Point for the Pseudocode to C Compiler.
Supports both the modernized Desktop GUI (Tkinter) and the Online Web IDE.
Run:
  python main.py          -> Launches modernized Desktop GUI with Web IDE launcher
  python main.py --web    -> Launches Web IDE server directly in browser
  python server.py        -> Starts local HTTP server
"""

import sys
import threading
import webbrowser

# Ensure Windows terminal supports UTF-8 console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog

from lexer import Lexer
from parser import Parser
from code_generator import CodeGenerator
from errors import CompilerError
from examples import EXAMPLES
from server import start_server, PORT


# Theme definitions for Tkinter GUI
THEMES = {
    "dark": {
        "bg_base": "#0d1117",
        "bg_surface": "#161b22",
        "bg_elevated": "#21262d",
        "bg_input": "#0b0e14",
        "text_primary": "#f0f6fc",
        "text_secondary": "#8b949e",
        "accent": "#2f81f7",
        "accent_text": "#ffffff",
        "border": "#30363d",
        "success": "#3fb950",
        "error": "#f85149"
    },
    "light": {
        "bg_base": "#f6f8fa",
        "bg_surface": "#ffffff",
        "bg_elevated": "#f0f2f5",
        "bg_input": "#ffffff",
        "text_primary": "#1f2328",
        "text_secondary": "#57606a",
        "accent": "#0969da",
        "accent_text": "#ffffff",
        "border": "#d0d7de",
        "success": "#1a7f37",
        "error": "#cf222e"
    }
}


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pseudocode to C Compiler - Modern IDE")
        self.root.geometry("1300x800")
        self.root.minsize(900, 600)

        self.current_theme_name = "dark"
        self.theme = THEMES[self.current_theme_name]
        self.last_c_code = ""
        self.server_started = False

        self.setup_ui()
        self.apply_theme()

        # Load first example by default
        self.load_example_by_index(0)

    def setup_ui(self):
        # Configure root grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # ---------------------------------------------------------------------
        # TOP BAR
        # ---------------------------------------------------------------------
        self.top_bar = tk.Frame(self.root, height=54, padx=16, pady=8)
        self.top_bar.grid(row=0, column=0, sticky="ew")

        # Logo and Title
        self.logo_label = tk.Label(
            self.top_bar,
            text="⚡ Pseudocode → C Compiler",
            font=("Arial", 16, "bold")
        )
        self.logo_label.pack(side="left", padx=(0, 16))

        # Example selector dropdown
        tk.Label(
            self.top_bar,
            text="Example:",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=(10, 4))

        self.example_titles = [ex["title"] for ex in EXAMPLES]
        self.selected_example_var = tk.StringVar(value=self.example_titles[0])
        self.example_dropdown = ttk.Combobox(
            self.top_bar,
            textvariable=self.selected_example_var,
            values=self.example_titles,
            state="readonly",
            width=32
        )
        self.example_dropdown.pack(side="left", padx=(0, 10))
        self.example_dropdown.bind("<<ComboboxSelected>>", self.on_example_selected)

        # Web IDE button
        self.web_ide_btn = tk.Button(
            self.top_bar,
            text="🌐 Open Modern Web IDE",
            font=("Arial", 10, "bold"),
            command=self.open_web_ide,
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        )
        self.web_ide_btn.pack(side="right", padx=(6, 0))

        # Theme toggle button
        self.theme_btn = tk.Button(
            self.top_bar,
            text="☀️ Light Mode",
            font=("Arial", 10),
            command=self.toggle_theme,
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2"
        )
        self.theme_btn.pack(side="right", padx=6)

        # ---------------------------------------------------------------------
        # MAIN DUAL-PANEL WORKSPACE
        # ---------------------------------------------------------------------
        self.container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=6)
        self.container.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)

        # ---------------- LEFT PANEL: Pseudocode Input ----------------
        self.left_panel = tk.Frame(self.container, padx=8, pady=8)
        self.container.add(self.left_panel, minsize=400)

        left_header = tk.Frame(self.left_panel)
        left_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            left_header,
            text="📝 Pseudocode Input",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        clear_btn = tk.Button(
            left_header,
            text="🗑️ Clear",
            font=("Arial", 9),
            command=self.clear_input,
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        clear_btn.pack(side="right")

        self.input_text = scrolledtext.ScrolledText(
            self.left_panel,
            font=("Consolas", 12),
            wrap=tk.WORD,
            undo=True
        )
        self.input_text.pack(fill="both", expand=True)

        # ---------------- RIGHT PANEL: Output & Details Tabs ----------------
        self.right_panel = tk.Frame(self.container, padx=8, pady=8)
        self.container.add(self.right_panel, minsize=450)

        right_header = tk.Frame(self.right_panel)
        right_header.pack(fill="x", pady=(0, 6))

        tk.Label(
            right_header,
            text="💻 Generated C Code & Diagnostics",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        self.copy_btn = tk.Button(
            right_header,
            text="📋 Copy Code",
            font=("Arial", 9),
            command=self.copy_c_code,
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        self.copy_btn.pack(side="right", padx=(4, 0))

        self.save_btn = tk.Button(
            right_header,
            text="⬇️ Save .c File",
            font=("Arial", 9),
            command=self.save_c_file,
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        self.save_btn.pack(side="right", padx=(4, 0))

        # Notebook tabs for C Code / Explanation / Symbols
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: C Code
        self.c_tab = tk.Frame(self.notebook)
        self.notebook.add(self.c_tab, text="Generated C Code")
        self.output_text = scrolledtext.ScrolledText(
            self.c_tab,
            font=("Consolas", 12),
            wrap=tk.NONE
        )
        self.output_text.pack(fill="both", expand=True)

        # Tab 2: Explanation
        self.explain_tab = tk.Frame(self.notebook)
        self.notebook.add(self.explain_tab, text="Conversion Explanation")
        self.explain_text = scrolledtext.ScrolledText(
            self.explain_tab,
            font=("Arial", 11),
            wrap=tk.WORD
        )
        self.explain_text.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # BOTTOM CONTROLS & STATUS BAR
        # ---------------------------------------------------------------------
        self.bottom_bar = tk.Frame(self.root, padx=16, pady=8)
        self.bottom_bar.grid(row=2, column=0, sticky="ew")

        self.compile_button = tk.Button(
            self.bottom_bar,
            text="⚡ CONVERT TO C",
            font=("Arial", 12, "bold"),
            command=self.compile_code,
            padx=20,
            pady=6,
            relief="flat",
            cursor="hand2"
        )
        self.compile_button.pack(side="left")

        self.status_label = tk.Label(
            self.bottom_bar,
            text="● Ready",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(side="left", padx=16)

    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg_base"])
        self.top_bar.configure(bg=t["bg_surface"])
        self.left_panel.configure(bg=t["bg_surface"])
        self.right_panel.configure(bg=t["bg_surface"])
        self.bottom_bar.configure(bg=t["bg_surface"])

        self.logo_label.configure(bg=t["bg_surface"], fg=t["text_primary"])
        self.status_label.configure(bg=t["bg_surface"], fg=t["success"])

        self.theme_btn.configure(
            bg=t["bg_elevated"],
            fg=t["text_primary"],
            text="☀️ Light Mode" if self.current_theme_name == "dark" else "🌙 Dark Mode"
        )
        self.web_ide_btn.configure(bg=t["accent"], fg=t["accent_text"])
        self.compile_button.configure(bg=t["accent"], fg=t["accent_text"])

        # Editor styling
        self.input_text.configure(
            bg=t["bg_input"],
            fg=t["text_primary"],
            insertbackground=t["text_primary"]
        )
        self.output_text.configure(
            bg=t["bg_input"],
            fg=t["text_primary"],
            insertbackground=t["text_primary"]
        )
        self.explain_text.configure(
            bg=t["bg_input"],
            fg=t["text_primary"]
        )

    def toggle_theme(self):
        self.current_theme_name = "light" if self.current_theme_name == "dark" else "dark"
        self.theme = THEMES[self.current_theme_name]
        self.apply_theme()

    def on_example_selected(self, event=None):
        idx = self.example_dropdown.current()
        if idx >= 0:
            self.load_example_by_index(idx)

    def load_example_by_index(self, idx):
        if 0 <= idx < len(EXAMPLES):
            ex = EXAMPLES[idx]
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", ex["pseudocode"].strip())
            self.compile_code()

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.explain_text.delete("1.0", tk.END)
        self.status_label.config(text="● Cleared", fg=self.theme["text_secondary"])

    def copy_c_code(self):
        if self.last_c_code:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_c_code)
            messagebox.showinfo("Copied", "Generated C code copied to clipboard!")
        else:
            messagebox.showwarning("Notice", "No code to copy.")

    def save_c_file(self):
        if not self.last_c_code:
            messagebox.showwarning("Notice", "No generated C code to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".c",
            filetypes=[("C Source Files", "*.c"), ("All Files", "*.*")],
            initialfile="program.c"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.last_c_code)
            messagebox.showinfo("Saved", f"File saved successfully to:\n{file_path}")

    def open_web_ide(self):
        """Starts the local web server in a background thread if not already running, and opens browser."""
        if not self.server_started:
            self.server_started = True
            threading.Thread(target=start_server, kwargs={"port": PORT, "open_browser": False}, daemon=True).start()

        webbrowser.open(f"http://localhost:{PORT}")
        self.status_label.config(text="● Web IDE Opened in Browser ✓", fg=self.theme["success"])

    def compile_code(self):
        pseudocode = self.input_text.get("1.0", tk.END).strip()
        self.output_text.delete("1.0", tk.END)
        self.explain_text.delete("1.0", tk.END)

        if not pseudocode:
            self.status_label.config(text="● Please enter pseudocode", fg=self.theme["error"])
            return

        try:
            lexer = Lexer()
            tokens = lexer.tokenize(pseudocode)

            parser = Parser(tokens)
            tree = parser.parse()

            generator = CodeGenerator()
            result = generator.generate_with_metadata(tree)

            self.last_c_code = result["c_code"]
            self.output_text.insert(tk.END, self.last_c_code)

            # Render Explanation
            explain_lines = ["=== STEP-BY-STEP CONVERSION EXPLANATION ===\n\n"]
            for step in result["explanation"]:
                explain_lines.append(f"• {step['stage']}:\n  {step['details']}\n\n")

            if result["warnings"]:
                explain_lines.append("=== WARNINGS & ADVISORIES ===\n")
                for w in result["warnings"]:
                    explain_lines.append(f"⚠️ {w}\n")

            self.explain_text.insert(tk.END, "".join(explain_lines))

            self.status_label.config(
                text="● Compilation Successful ✓",
                fg=self.theme["success"]
            )

        except CompilerError as error:
            err_msg = f"/* =========================================================\n" \
                      f"   COMPILATION ERROR DETECTED\n" \
                      f"   {error}\n" \
                      f"========================================================= */\n"
            self.output_text.insert(tk.END, err_msg)
            self.explain_text.insert(tk.END, str(error))
            self.status_label.config(
                text="● Compilation Failed ✗",
                fg=self.theme["error"]
            )

        except Exception as error:
            self.output_text.insert(tk.END, f"Unexpected Error:\n\n{str(error)}")
            self.status_label.config(
                text="● Unexpected Error",
                fg=self.theme["error"]
            )


def main():
    if "--web" in sys.argv:
        start_server(port=PORT, open_browser=True)
    else:
        root = tk.Tk()
        app = CompilerGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()