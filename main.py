import sqlite3
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter


# --- 1. Data Model and Database (SQLite) ---
class Snippet:
    """Represents a single code snippet."""

    def __init__(self, title, code, language="text", tags="", description="", id=None):
        self.id = id
        self.title = title
        self.code = code
        self.language = language
        self.tags = tags
        self.description = description

    def to_tuple(self):
        """Returns data in a tuple format for DB insertion/update."""
        return (self.title, self.code, self.language, self.tags, self.description)

    def __str__(self):
        return f"ID: {self.id} | Title: {self.title} | Language: {self.language}"


class SnippetDatabase:
    """Manages CRUD operations with the SQLite database."""

    def __init__(self, db_name="snippets.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Creates the snippets table if it doesn't exist."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                code TEXT NOT NULL,
                language TEXT,
                tags TEXT,
                description TEXT
            )
        """)
        self.conn.commit()

    def add_snippet(self, snippet):
        """Adds a new snippet to the database."""
        self.cursor.execute("INSERT INTO snippets (title, code, language, tags, description) VALUES (?, ?, ?, ?, ?)",
                            snippet.to_tuple())
        self.conn.commit()

    def get_all_snippets(self):
        """Retrieves all snippets as a list of Snippet objects."""
        self.cursor.execute("SELECT * FROM snippets")
        rows = self.cursor.fetchall()
        return [Snippet(id=row[0], title=row[1], code=row[2], language=row[3], tags=row[4], description=row[5]) for row
                in rows]

    def close(self):
        """Closes the database connection."""
        self.conn.close()


# --- 2. Syntax Highlighting Tool (Pygments) ---
def highlight_code_html(code, language):
    """
    Highlights the code using Pygments and returns the HTML output.
    This is what you'd display in a web-view component of a modern GUI.
    For basic Tkinter, we'll simplify the highlighting (see manager class).
    """
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except Exception:
        # Fallback to guessing the language or plain text
        try:
            lexer = guess_lexer(code)
        except Exception:
            lexer = get_lexer_by_name('text', stripall=True)

    formatter = HtmlFormatter(style='default', full=False)
    # Returns the highlighted HTML string
    return highlight(code, lexer, formatter)


# --- 3. Basic GUI Structure (Tkinter) ---
class SnippetManagerApp:
    def __init__(self, master):
        self.db = SnippetDatabase()
        self.master = master
        master.title("📝 Python Code Snippet Manager")
        master.geometry("800x600")

        # Configure styles for better look (still basic Tkinter)
        master.option_add('*Font', 'Arial 10')

        # Frames
        self.list_frame = tk.Frame(master)
        self.list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.detail_frame = tk.Frame(master)
        self.detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Snippet List
        tk.Label(self.list_frame, text="**Saved Snippets**", font='Arial 12 bold').pack(pady=5)

        self.snippet_listbox = tk.Listbox(self.list_frame, width=35, height=25)
        self.snippet_listbox.pack()
        self.snippet_listbox.bind('<<ListboxSelect>>', self.show_snippet_details)

        # Action Buttons
        button_frame = tk.Frame(self.list_frame)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="➕ Add New", command=self.add_new_snippet).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Delete", command=self.delete_snippet).pack(side=tk.LEFT, padx=5)

        # Snippet Details (Right Side)
        tk.Label(self.detail_frame, text="**Snippet Details**", font='Arial 12 bold').pack(pady=5)

        # Display Area for highlighted code (using a simple ScrolledText for now)
        self.code_display = scrolledtext.ScrolledText(self.detail_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.code_display.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.detail_frame,
                 text="*Note: Full syntax highlighting is complex in native Tkinter, a web-view component (e.g., in PyQt/Kivy) is ideal for it.*").pack(
            pady=5)

        self.load_snippets()

    def load_snippets(self):
        """Loads snippets from the DB and populates the listbox."""
        self.snippets = self.db.get_all_snippets()
        self.snippet_listbox.delete(0, tk.END)
        for snippet in self.snippets:
            self.snippet_listbox.insert(tk.END, f"[{snippet.language.upper()}] {snippet.title}")

    def show_snippet_details(self, event):
        """Displays the selected snippet's details and (basic) highlighted code."""
        try:
            selected_index = self.snippet_listbox.curselection()[0]
            snippet = self.snippets[selected_index]

            self.code_display.config(state=tk.NORMAL)
            self.code_display.delete('1.0', tk.END)

            # --- Simplistic Highlighting for Tkinter ---
            # Native Tkinter doesn't easily support the HTML generated by Pygments.
            # For a quick fix, we just display the code and title/desc.

            details = f"Title: {snippet.title}\nLanguage: {snippet.language}\nTags: {snippet.tags}\nDescription:\n{snippet.description}\n\n--- CODE ---\n{snippet.code}"
            self.code_display.insert(tk.END, details)

            self.code_display.config(state=tk.DISABLED)

        except IndexError:
            pass  # No item selected

    def add_new_snippet(self):
        """Opens a dialog to collect new snippet data."""
        title = simpledialog.askstring("Input", "Enter Snippet Title:", parent=self.master)
        if not title: return

        language = simpledialog.askstring("Input", "Enter Language (e.g., python, html):", parent=self.master,
                                          initialvalue="python")
        if not language: language = "text"

        code = simpledialog.askstring("Input", "Paste Code Snippet here:", parent=self.master)
        if not code: return

        tags = simpledialog.askstring("Input", "Enter Tags (comma separated):", parent=self.master)
        description = simpledialog.askstring("Input", "Enter Description:", parent=self.master)

        new_snippet = Snippet(title, code, language, tags, description)
        self.db.add_snippet(new_snippet)
        self.load_snippets()
        messagebox.showinfo("Success", f"Snippet '{title}' added successfully!")

    def delete_snippet(self):
        """Deletes the selected snippet from the list and DB."""
        try:
            selected_index = self.snippet_listbox.curselection()[0]
            snippet = self.snippets[selected_index]

            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{snippet.title}'?"):
                self.db.cursor.execute("DELETE FROM snippets WHERE id=?", (snippet.id,))
                self.db.conn.commit()
                self.load_snippets()

                # Clear the detail view
                self.code_display.config(state=tk.NORMAL)
                self.code_display.delete('1.0', tk.END)
                self.code_display.config(state=tk.DISABLED)

        except IndexError:
            messagebox.showerror("Error", "Please select a snippet to delete.")


# --- Main Execution ---
if __name__ == '__main__':
    root = tk.Tk()
    app = SnippetManagerApp(root)
    root.mainloop()
    app.db.close()
