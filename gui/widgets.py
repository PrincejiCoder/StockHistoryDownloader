import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional
from models.search_result import SearchResult

class SmartSearchBar(ttk.Frame):
    def __init__(self, parent, on_search: Callable[[str], None], on_select: Callable[[SearchResult], None]):
        super().__init__(parent)
        self.on_search = on_search
        self.on_select = on_select
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_type)
        
        # Frame for entry and clear button
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.pack(fill=tk.X, expand=True)
        
        self.entry = ttk.Entry(self.entry_frame, textvariable=self.search_var, width=50)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.clear_btn = ttk.Button(self.entry_frame, text="❌", width=3, command=self.clear)
        self.clear_btn.pack(side=tk.RIGHT)
        
        # Dropdown for suggestions
        self.listbox = tk.Listbox(self, height=5)
        self.listbox.pack(fill=tk.X, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        
        # Keyboard navigation
        self.entry.bind("<Down>", self._focus_listbox)
        self.listbox.bind("<Return>", self._on_listbox_enter)
        self.listbox.bind("<Double-Button-1>", self._on_listbox_enter)
        self.entry.bind("<Return>", lambda e: self.on_search(self.search_var.get()))
        
        self.current_results: List[SearchResult] = []
        self.selected_result: Optional[SearchResult] = None
        
        self.hide_dropdown()
        
    def _on_type(self, *args):
        if self.selected_result is not None:
            # Prevent typing if locked, handled by making entry readonly later or just ignoring.
            # If user types while locked (if we didn't use state="readonly"), unlock it.
            pass

    def update_suggestions(self, results: List[SearchResult]):
        self.current_results = results
        self.listbox.delete(0, tk.END)
        for r in results:
            self.listbox.insert(tk.END, r.display_text)
            
        if results:
            self.show_dropdown()
        else:
            self.hide_dropdown()
            
    def _focus_listbox(self, event):
        if self.listbox.winfo_ismapped() and self.listbox.size() > 0:
            self.listbox.focus_set()
            self.listbox.selection_set(0)
            
    def _on_listbox_select(self, event):
        pass # Optional: update metadata preview on single click without confirming
        
    def _on_listbox_enter(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            result = self.current_results[index]
            self._select_result(result)
            
    def _select_result(self, result: SearchResult):
        self.selected_result = result
        self.search_var.set(result.display_text)
        self.entry.config(state="readonly")
        self.hide_dropdown()
        self.on_select(result)
        
    def clear(self):
        self.entry.config(state="normal")
        self.search_var.set("")
        self.selected_result = None
        self.hide_dropdown()
        self.listbox.delete(0, tk.END)
        self.current_results = []
        
    def show_dropdown(self):
        if not self.listbox.winfo_ismapped():
            self.listbox.pack(fill=tk.X, expand=True)
            
    def hide_dropdown(self):
        if self.listbox.winfo_ismapped():
            self.listbox.pack_forget()

class DataPreviewTable(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.tree = ttk.Treeview(self, show="headings", height=10)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_data(self, df):
        # Clear existing
        self.tree.delete(*self.tree.get_children())
        
        if df is None or df.empty:
            return
            
        # Set columns
        cols = list(df.columns)
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=100)
            
        # Insert data (limit to 20 rows for preview)
        preview_df = df.head(20)
        for _, row in preview_df.iterrows():
            values = [row[col] for col in cols]
            self.tree.insert("", tk.END, values=values)
