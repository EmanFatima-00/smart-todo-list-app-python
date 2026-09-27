"""
Smart To-Do List Desktop Application
Python Internship - Week 05 Project

Technologies: Python, Tkinter (GUI), JSON (data storage)

This program is organized using one main class (TodoApp) that holds the
GUI widgets, plus clearly named methods for every feature (load_tasks,
save_tasks, add_task, update_task, delete_task, mark_completed, search,
filter, sort, dashboard updates, theme switching, etc.).

Run with:  python todo_app.py
"""

import json
import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


# ----------------------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------------------

DATA_FILE = "tasks.json"
BACKUP_FILE = "tasks_backup.json"
DATE_FORMAT = "%d/%m/%Y"

PRIORITIES = ["High", "Medium", "Low"]
CATEGORIES = ["University", "Learning", "Internship", "Project", "Personal", "Other"]

STATUS_FILTERS = ["All", "Pending", "Completed", "Overdue"]
PRIORITY_FILTERS = ["All Priorities"] + PRIORITIES
CATEGORY_FILTERS = ["All Categories"] + CATEGORIES

SORT_OPTIONS = ["Due Date", "Priority", "Status", "Task Name"]

# Colors for Light / Dark mode
THEMES = {
    "light": {
        "bg": "#f4f6f8",
        "panel_bg": "#ffffff",
        "fg": "#1f2937",
        "accent": "#2563eb",
        "accent_fg": "#ffffff",
        "muted": "#6b7280",
        "tree_bg": "#ffffff",
        "tree_fg": "#1f2937",
        "tree_select": "#dbeafe",
        "overdue": "#dc2626",
        "completed": "#16a34a",
        "entry_bg": "#ffffff",
        "border": "#d1d5db",
    },
    "dark": {
        "bg": "#1e1f26",
        "panel_bg": "#282a36",
        "fg": "#f3f4f6",
        "accent": "#3b82f6",
        "accent_fg": "#ffffff",
        "muted": "#9ca3af",
        "tree_bg": "#20222b",
        "tree_fg": "#f3f4f6",
        "tree_select": "#374151",
        "overdue": "#f87171",
        "completed": "#4ade80",
        "entry_bg": "#2f313d",
        "border": "#3f4250",
    },
}


# ----------------------------------------------------------------------
# DATA LAYER  (JSON load / save / backup)
# ----------------------------------------------------------------------

def load_tasks():
    """Load tasks from the JSON file. Returns an empty list if the file
    does not exist or the JSON is invalid/corrupted."""
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable file -> try to restore from backup,
        # otherwise start fresh instead of crashing.
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []


def save_tasks(tasks):
    """Save the given task list to the JSON file, and refresh the backup."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4)
        backup_tasks()
        return True
    except OSError as e:
        messagebox.showerror("Save Error", f"Could not save tasks:\n{e}")
        return False


def backup_tasks():
    """Keep a simple backup copy of the data file so a corrupted or
    accidentally overwritten tasks.json is less likely to lose data."""
    try:
        if os.path.exists(DATA_FILE):
            shutil.copyfile(DATA_FILE, BACKUP_FILE)
    except OSError:
        pass  # Backup failing should never crash the app


# ----------------------------------------------------------------------
# VALIDATION HELPERS
# ----------------------------------------------------------------------

def validate_date(date_text):
    """Return True if date_text matches DD/MM/YYYY and is a real date."""
    try:
        datetime.strptime(date_text, DATE_FORMAT)
        return True
    except ValueError:
        return False


def is_overdue(task):
    """A task is overdue if its due date has passed and it isn't completed."""
    if task.get("completed"):
        return False
    due_date = task.get("due_date", "")
    if not due_date or not validate_date(due_date):
        return False
    due = datetime.strptime(due_date, DATE_FORMAT)
    return due.date() < datetime.now().date()
# ----------------------------------------------------------------------
# MAIN APPLICATION CLASS
# ----------------------------------------------------------------------

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart To-Do List")
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)

        # ---- data ----
        self.tasks = load_tasks()
        self.next_id = self._get_next_id()
        self.selected_task_id = None
        self.last_deleted_task = None  # for Undo
        self.theme_name = "light"

        # ---- tk variables ----
        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORIES[0])
        self.priority_var = tk.StringVar(value=PRIORITIES[1])
        self.due_date_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value=STATUS_FILTERS[0])
        self.priority_filter_var = tk.StringVar(value=PRIORITY_FILTERS[0])
        self.category_filter_var = tk.StringVar(value=CATEGORY_FILTERS[0])
        self.sort_var = tk.StringVar(value=SORT_OPTIONS[0])

        self.search_var.trace_add("write", lambda *args: self.refresh_task_list())

        self._build_style()
        self._build_layout()
        self.refresh_task_list()

    # ------------------------------------------------------------------
    # SETUP HELPERS
    # ------------------------------------------------------------------

    def _get_next_id(self):
        if not self.tasks:
            return 1
        return max(t["id"] for t in self.tasks) + 1

    def _build_style(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------

    def _build_layout(self):
        # Root container so we can restyle everything on theme change
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self._build_header()
        self._build_dashboard()
        self._build_search_filter_bar()
        self._build_input_area()
        self._build_task_table()
        self._build_action_buttons()

        self.apply_theme()

    def _build_header(self):
        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(fill="x", padx=16, pady=(14, 6))

        self.title_label = tk.Label(
            self.header_frame, text="Smart To-Do List",
            font=("Segoe UI", 20, "bold")
        )
        self.title_label.pack(side="left")

        self.theme_btn = tk.Button(
            self.header_frame, text="🌙 Dark Mode", command=self.toggle_theme,
            relief="flat", cursor="hand2", padx=10, pady=4
        )
        self.theme_btn.pack(side="right")

    def _build_dashboard(self):
        self.dashboard_frame = tk.Frame(self.main_frame)
        self.dashboard_frame.pack(fill="x", padx=16, pady=6)

        self.stat_labels = {}
        stats = ["Total Tasks", "Completed", "Pending", "Overdue", "Completion Rate"]
        for i, name in enumerate(stats):
            card = tk.Frame(self.dashboard_frame, bd=0, relief="flat")
            card.grid(row=0, column=i, padx=6, sticky="nsew")
            self.dashboard_frame.grid_columnconfigure(i, weight=1)

            value_lbl = tk.Label(card, text="0", font=("Segoe UI", 16, "bold"))
            value_lbl.pack(pady=(10, 0))
            name_lbl = tk.Label(card, text=name, font=("Segoe UI", 9))
            name_lbl.pack(pady=(0, 10))

            self.stat_labels[name] = (card, value_lbl, name_lbl)

        # Progress bar showing completion percentage
        self.progress_bar = ttk.Progressbar(
            self.main_frame, orient="horizontal", mode="determinate", maximum=100
        )
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 10))

    def _build_search_filter_bar(self):
        self.filter_frame = tk.Frame(self.main_frame)
        self.filter_frame.pack(fill="x", padx=16, pady=4)

        tk.Label(self.filter_frame, text="🔍 Search:").pack(side="left")
        search_entry = tk.Entry(self.filter_frame, textvariable=self.search_var, width=22)
        search_entry.pack(side="left", padx=(4, 14))

        tk.Label(self.filter_frame, text="Status:").pack(side="left")
        status_combo = ttk.Combobox(
            self.filter_frame, textvariable=self.status_filter_var,
            values=STATUS_FILTERS, width=12, state="readonly"
        )
        status_combo.pack(side="left", padx=(4, 14))
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())

        tk.Label(self.filter_frame, text="Priority:").pack(side="left")
        priority_combo = ttk.Combobox(
            self.filter_frame, textvariable=self.priority_filter_var,
            values=PRIORITY_FILTERS, width=12, state="readonly"
        )
        priority_combo.pack(side="left", padx=(4, 14))
        priority_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())

        tk.Label(self.filter_frame, text="Category:").pack(side="left")
        category_combo = ttk.Combobox(
            self.filter_frame, textvariable=self.category_filter_var,
            values=CATEGORY_FILTERS, width=14, state="readonly"
        )
        category_combo.pack(side="left", padx=(4, 14))
        category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())

        tk.Label(self.filter_frame, text="Sort by:").pack(side="left")
        sort_combo = ttk.Combobox(
            self.filter_frame, textvariable=self.sort_var,
            values=SORT_OPTIONS, width=12, state="readonly"
        )
        sort_combo.pack(side="left", padx=(4, 0))
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_task_list())

    def _build_input_area(self):
        self.input_frame = tk.LabelFrame(self.main_frame, text="Task Details", padx=10, pady=10)
        self.input_frame.pack(fill="x", padx=16, pady=6)

        tk.Label(self.input_frame, text="Title:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        tk.Entry(self.input_frame, textvariable=self.title_var, width=30).grid(
            row=0, column=1, padx=4, pady=4, sticky="w"
        )

        tk.Label(self.input_frame, text="Category:").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            self.input_frame, textvariable=self.category_var,
            values=CATEGORIES, width=15, state="readonly"
        ).grid(row=0, column=3, padx=4, pady=4, sticky="w")

        tk.Label(self.input_frame, text="Priority:").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Combobox(
            self.input_frame, textvariable=self.priority_var,
            values=PRIORITIES, width=15, state="readonly"
        ).grid(row=1, column=1, padx=4, pady=4, sticky="w")

        tk.Label(self.input_frame, text="Due Date (DD/MM/YYYY):").grid(
            row=1, column=2, sticky="w", padx=4, pady=4
        )
        tk.Entry(self.input_frame, textvariable=self.due_date_var, width=17).grid(
            row=1, column=3, padx=4, pady=4, sticky="w"
        )

        self.add_btn = tk.Button(
            self.input_frame, text="➕ Add Task", command=self.add_task,
            relief="flat", cursor="hand2", padx=12, pady=5
        )
        self.add_btn.grid(row=0, column=4, rowspan=2, padx=(16, 4), pady=4)

    def _build_task_table(self):
        table_frame = tk.Frame(self.main_frame)
        table_frame.pack(fill="both", expand=True, padx=16, pady=6)

        columns = ("title", "category", "priority", "due_date", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headings = {
            "title": "Task",
            "category": "Category",
            "priority": "Priority",
            "due_date": "Due Date",
            "status": "Status",
        }
        widths = {"title": 300, "category": 130, "priority": 100, "due_date": 110, "status": 130}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_task_select)

        # Tag colors are (re)applied in apply_theme()
        self.tree.tag_configure("overdue")
        self.tree.tag_configure("completed")

    def _build_action_buttons(self):
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.pack(fill="x", padx=16, pady=(4, 14))

        buttons = [
            ("✏ Update", self.update_task),
            ("✔ Complete", self.mark_completed),
            ("🗑 Delete", self.delete_task),
            ("↩ Undo Delete", self.undo_delete),
            ("🧹 Delete All", self.delete_all_tasks),
            ("✖ Clear Form", self.clear_form),
        ]
        for text, cmd in buttons:
            btn = tk.Button(self.action_frame, text=text, command=cmd,
                             relief="flat", cursor="hand2", padx=10, pady=6)
            btn.pack(side="left", padx=4)
            # ------------------------------------------------------------------
    # CRUD OPERATIONS
    # ------------------------------------------------------------------

    def add_task(self):
        """CREATE: validate the form and add a new task."""
        title = self.title_var.get().strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get().strip()
        due_date = self.due_date_var.get().strip()

        if not self._validate_form(title, category, priority, due_date):
            return

        new_task = {
            "id": self.next_id,
            "title": title,
            "category": category,
            "priority": priority,
            "due_date": due_date,
            "completed": False,
        }
        self.tasks.append(new_task)
        self.next_id += 1

        if save_tasks(self.tasks):
            self.clear_form()
            self.refresh_task_list()
            messagebox.showinfo("Task Added", f"'{title}' was added successfully.")

    def update_task(self):
        """UPDATE: apply form values to the currently selected task."""
        if self.selected_task_id is None:
            messagebox.showwarning("No Task Selected", "Please select a task to update.")
            return

        title = self.title_var.get().strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get().strip()
        due_date = self.due_date_var.get().strip()

        if not self._validate_form(title, category, priority, due_date):
            return

        task = self._find_task(self.selected_task_id)
        if task is None:
            messagebox.showerror("Error", "The selected task no longer exists.")
            return

        task["title"] = title
        task["category"] = category
        task["priority"] = priority
        task["due_date"] = due_date

        if save_tasks(self.tasks):
            self.clear_form()
            self.refresh_task_list()
            messagebox.showinfo("Task Updated", "The task was updated successfully.")

    def delete_task(self):
        """DELETE: remove the selected task, after confirmation. Keeps a
        copy so the user can Undo the delete."""
        if self.selected_task_id is None:
            messagebox.showwarning("No Task Selected", "Please select a task to delete.")
            return

        task = self._find_task(self.selected_task_id)
        if task is None:
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete task '{task['title']}'?")
        if not confirm:
            return

        self.last_deleted_task = task
        self.tasks = [t for t in self.tasks if t["id"] != self.selected_task_id]

        if save_tasks(self.tasks):
            self.clear_form()
            self.refresh_task_list()

    def delete_all_tasks(self):
        """DELETE ALL: clear every task, after confirmation."""
        if not self.tasks:
            messagebox.showinfo("No Tasks", "There are no tasks to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete All",
            "This will permanently delete ALL tasks. Are you sure?"
        )
        if not confirm:
            return

        self.last_deleted_task = None  # bulk delete can't be undone
        self.tasks = []
        if save_tasks(self.tasks):
            self.next_id = 1
            self.clear_form()
            self.refresh_task_list()

    def mark_completed(self):
        """Mark the selected task as completed."""
        if self.selected_task_id is None:
            messagebox.showwarning("No Task Selected", "Please select a task to mark as completed.")
            return

        task = self._find_task(self.selected_task_id)
        if task is None:
            return

        task["completed"] = True
        if save_tasks(self.tasks):
            self.clear_form()
            self.refresh_task_list()

    def undo_delete(self):
        """Restore the most recently deleted single task, if any."""
        if self.last_deleted_task is None:
            messagebox.showinfo("Nothing to Undo", "There is no recently deleted task to restore.")
            return

        self.tasks.append(self.last_deleted_task)
        self.last_deleted_task = None
        save_tasks(self.tasks)
        self.refresh_task_list()

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def _validate_form(self, title, category, priority, due_date):
        if not title:
            messagebox.showerror("Invalid Input", "Task title cannot be empty.")
            return False
        if not category:
            messagebox.showerror("Invalid Input", "Please select a category.")
            return False
        if priority not in PRIORITIES:
            messagebox.showerror("Invalid Input", "Please select a valid priority.")
            return False
        if not due_date:
            messagebox.showerror("Invalid Input", "Please enter a due date.")
            return False
        if not validate_date(due_date):
            messagebox.showerror(
                "Invalid Date", "Due date must be a real date in DD/MM/YYYY format."
            )
            return False
        return True
    # ------------------------------------------------------------------
    # SEARCH / FILTER / SORT
    # ------------------------------------------------------------------

    def search_tasks(self, tasks, query):
        if not query:
            return tasks
        query = query.lower()
        return [
            t for t in tasks
            if query in t["title"].lower()
            or query in t["category"].lower()
            or query in t["priority"].lower()
        ]

    def filter_tasks(self, tasks):
        status = self.status_filter_var.get()
        priority = self.priority_filter_var.get()
        category = self.category_filter_var.get()

        result = tasks
        if status == "Pending":
            result = [t for t in result if not t["completed"]]
        elif status == "Completed":
            result = [t for t in result if t["completed"]]
        elif status == "Overdue":
            result = [t for t in result if is_overdue(t)]

        if priority != "All Priorities":
            result = [t for t in result if t["priority"] == priority]

        if category != "All Categories":
            result = [t for t in result if t["category"] == category]

        return result

    def sort_tasks(self, tasks):
        sort_by = self.sort_var.get()

        if sort_by == "Due Date":
            def key(t):
                try:
                    return datetime.strptime(t["due_date"], DATE_FORMAT)
                except (ValueError, TypeError):
                    return datetime.max
            return sorted(tasks, key=key)

        if sort_by == "Priority":
            order = {"High": 0, "Medium": 1, "Low": 2}
            return sorted(tasks, key=lambda t: order.get(t["priority"], 3))

        if sort_by == "Status":
            return sorted(tasks, key=lambda t: t["completed"])

        if sort_by == "Task Name":
            return sorted(tasks, key=lambda t: t["title"].lower())

        return tasks

    # ------------------------------------------------------------------
    # DISPLAY / REFRESH
    # ------------------------------------------------------------------

    def refresh_task_list(self):
        """READ + Search/Filter/Sort: recompute the visible task list and
        redraw the table, dashboard, and progress bar."""
        visible = self.search_tasks(self.tasks, self.search_var.get().strip())
        visible = self.filter_tasks(visible)
        visible = self.sort_tasks(visible)

        self.tree.delete(*self.tree.get_children())
        for task in visible:
            overdue = is_overdue(task)
            status_text = "Completed" if task["completed"] else ("Overdue" if overdue else "Pending")
            tag = "completed" if task["completed"] else ("overdue" if overdue else "")

            self.tree.insert(
                "", "end", iid=str(task["id"]),
                values=(task["title"], task["category"], task["priority"],
                        task["due_date"], status_text),
                tags=(tag,) if tag else ()
            )

        self.update_dashboard()

    def update_dashboard(self):
        """Recalculate and display Total / Completed / Pending / Overdue /
        Completion Rate, and update the progress bar."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t["completed"])
        overdue = sum(1 for t in self.tasks if is_overdue(t))
        pending = total - completed

        rate = (completed / total * 100) if total > 0 else 0

        self.stat_labels["Total Tasks"][1].config(text=str(total))
        self.stat_labels["Completed"][1].config(text=str(completed))
        self.stat_labels["Pending"][1].config(text=str(pending))
        self.stat_labels["Overdue"][1].config(text=str(overdue))
        self.stat_labels["Completion Rate"][1].config(text=f"{rate:.0f}%")

        self.progress_bar["value"] = rate

    # ------------------------------------------------------------------
    # SELECTION / FORM HELPERS
    # ------------------------------------------------------------------

    def on_task_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_task_id = None
            return

        task_id = int(selection[0])
        task = self._find_task(task_id)
        if task is None:
            return

        self.selected_task_id = task_id
        self.title_var.set(task["title"])
        self.category_var.set(task["category"])
        self.priority_var.set(task["priority"])
        self.due_date_var.set(task["due_date"])

    def clear_form(self):
        self.title_var.set("")
        self.category_var.set(CATEGORIES[0])
        self.priority_var.set(PRIORITIES[1])
        self.due_date_var.set("")
        self.selected_task_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def _find_task(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                return t
        return None
    # ------------------------------------------------------------------
    # THEME (DARK / LIGHT MODE)
    # ------------------------------------------------------------------

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()

    def apply_theme(self):
        c = THEMES[self.theme_name]

        self.root.configure(bg=c["bg"])
        self.main_frame.configure(bg=c["bg"])
        self.header_frame.configure(bg=c["bg"])
        self.title_label.configure(bg=c["bg"], fg=c["fg"])
        self.theme_btn.configure(
            text="☀ Light Mode" if self.theme_name == "dark" else "🌙 Dark Mode",
            bg=c["accent"], fg=c["accent_fg"], activebackground=c["accent"],
            activeforeground=c["accent_fg"]
        )

        self.dashboard_frame.configure(bg=c["bg"])
        for name, (card, value_lbl, name_lbl) in self.stat_labels.items():
            card.configure(bg=c["panel_bg"], highlightbackground=c["border"], highlightthickness=1)
            fg = c["fg"]
            if name == "Overdue":
                fg = c["overdue"]
            elif name == "Completed":
                fg = c["completed"]
            value_lbl.configure(bg=c["panel_bg"], fg=fg)
            name_lbl.configure(bg=c["panel_bg"], fg=c["muted"])

        self.filter_frame.configure(bg=c["bg"])
        for child in self.filter_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=c["bg"], fg=c["fg"])

        self.input_frame.configure(bg=c["panel_bg"], fg=c["fg"])
        for child in self.input_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=c["panel_bg"], fg=c["fg"])
            elif type(child) is tk.Entry:
                child.configure(bg=c["entry_bg"], fg=c["fg"], insertbackground=c["fg"])

        self.add_btn.configure(bg=c["accent"], fg=c["accent_fg"],
                                activebackground=c["accent"], activeforeground=c["accent_fg"])

        self.action_frame.configure(bg=c["bg"])
        for child in self.action_frame.winfo_children():
            if isinstance(child, tk.Button):
                child.configure(bg=c["panel_bg"], fg=c["fg"],
                                activebackground=c["tree_select"], activeforeground=c["fg"])

        self.style.configure("Treeview",
                              background=c["tree_bg"], fieldbackground=c["tree_bg"],
                              foreground=c["tree_fg"], rowheight=26)
        self.style.map("Treeview", background=[("selected", c["tree_select"])])
        self.style.configure("Treeview.Heading", background=c["panel_bg"], foreground=c["fg"])

        self.tree.tag_configure("overdue", foreground=c["overdue"])
        self.tree.tag_configure("completed", foreground=c["completed"])


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()