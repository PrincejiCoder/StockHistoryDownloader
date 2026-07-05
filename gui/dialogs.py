import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess

def show_post_save_dialog(parent, filepath: str):
    """Shows a dialog asking what to do after saving."""
    dialog = tk.Toplevel(parent)
    dialog.title("Saved Successfully")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Calculate geometry to center over parent
    parent.update_idletasks()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    parent_x = parent.winfo_x()
    parent_y = parent.winfo_y()
    
    dialog_width = 300
    dialog_height = 120
    
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    dialog.focus_set()
    
    ttk.Label(dialog, text=f"Data saved to:\n{os.path.basename(filepath)}", justify=tk.CENTER).pack(pady=10)
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def open_file():
        os.startfile(filepath)
        dialog.destroy()
        
    def open_folder():
        os.startfile(os.path.dirname(filepath))
        dialog.destroy()
        
    ttk.Button(btn_frame, text="Open File", command=open_file).pack(side=tk.LEFT, padx=5, expand=True)
    ttk.Button(btn_frame, text="Open Folder", command=open_folder).pack(side=tk.LEFT, padx=5, expand=True)
    ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True)
    
    parent.wait_window(dialog)
