import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import pandas as pd
from typing import Optional

from gui.widgets import SmartSearchBar, DataPreviewTable
from gui.dialogs import show_post_save_dialog
from api.yahoo_api import YahooAPI
from utils.config import ConfigManager
from utils.exporter import DataExporter
from utils.logger import logger
from models.search_result import SearchResult

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("StockHistoryDownloader")
        self.geometry("800x700")
        
        self.config = ConfigManager.load()
        self.current_df: Optional[pd.DataFrame] = None
        self.selected_symbol: Optional[SearchResult] = None
        
        self._cancel_requested = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Search Section ---
        search_lf = ttk.LabelFrame(main_frame, text="Search Symbol", padding="5")
        search_lf.pack(fill=tk.X, pady=(0, 10))
        
        self.search_bar = SmartSearchBar(
            search_lf,
            on_search=self._start_search,
            on_select=self._on_symbol_select
        )
        self.search_bar.pack(fill=tk.X)
        
        self.metadata_lbl = ttk.Label(search_lf, text="", justify=tk.LEFT)
        self.metadata_lbl.pack(anchor=tk.W, pady=5)
        
        # --- Fetch Options ---
        fetch_lf = ttk.LabelFrame(main_frame, text="Data Options", padding="5")
        fetch_lf.pack(fill=tk.X, pady=10)
        
        ttk.Label(fetch_lf, text="Period:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.period_var = tk.StringVar(value=self.config.last_period)
        periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        self.period_cb = ttk.Combobox(fetch_lf, textvariable=self.period_var, values=periods, width=10, state="readonly")
        self.period_cb.grid(row=0, column=1, padx=5, pady=5)
        self.period_cb.bind("<<ComboboxSelected>>", lambda e: self._validate_and_adjust_options("period"))
        
        ttk.Label(fetch_lf, text="Interval:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.interval_var = tk.StringVar(value=self.config.last_interval)
        
        self.interval_btn = ttk.Menubutton(fetch_lf, textvariable=self.interval_var, width=10)
        self.interval_btn.grid(row=0, column=3, padx=5, pady=5)
        
        self.interval_menu = tk.Menu(self.interval_btn, tearoff=0)
        self.interval_btn.config(menu=self.interval_menu)
        
        # Info icon for interval rules
        self.info_btn = ttk.Label(fetch_lf, text="ⓘ", cursor="hand2", foreground="blue", font=("TkDefaultFont", 11, "bold"))
        self.info_btn.grid(row=0, column=4, padx=(2, 10), pady=5, sticky=tk.W)
        self.info_btn.bind("<Button-1>", self._show_info_tooltip)
        
        # Trigger initial validation on load
        self._validate_and_adjust_options("interval")
        
        # Buttons
        btn_frame = ttk.Frame(fetch_lf)
        btn_frame.grid(row=0, column=5, padx=10, pady=5)
        
        self.fetch_btn = ttk.Button(btn_frame, text="Fetch Data", command=self._start_fetch)
        self.fetch_btn.pack(side=tk.LEFT, padx=2)
        
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self._cancel_fetch, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=2)
        
        self.status_lbl = ttk.Label(fetch_lf, text="", foreground="blue")
        self.status_lbl.grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=5)
        
        # --- Preview Section ---
        preview_lf = ttk.LabelFrame(main_frame, text="Data Preview (First 20 rows)", padding="5")
        preview_lf.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_table = DataPreviewTable(preview_lf)
        self.preview_table.pack(fill=tk.BOTH, expand=True)
        
        self.row_count_lbl = ttk.Label(preview_lf, text="")
        self.row_count_lbl.pack(anchor=tk.W, pady=2)
        
        # --- Export Section ---
        export_lf = ttk.LabelFrame(main_frame, text="Export", padding="5")
        export_lf.pack(fill=tk.X, pady=10)
        
        ttk.Label(export_lf, text="Format:").pack(side=tk.LEFT, padx=5)
        self.format_var = tk.StringVar(value=self.config.last_export_format)
        self.format_var.trace_add("write", self._on_format_change)
        
        self.format_cb = ttk.Combobox(export_lf, textvariable=self.format_var, values=["csv", "json"], width=10, state="readonly")
        self.format_cb.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(export_lf, text="Save CSV", command=self._save_data, state=tk.DISABLED)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        # --- Footer ---
        footer = ttk.Frame(main_frame)
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))
        
        ttk.Separator(footer, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        footer_inner = ttk.Frame(footer)
        footer_inner.pack(anchor=tk.CENTER, pady=3)
        
        ttk.Label(footer_inner, text="Found a bug or have an idea?", foreground="gray", font=("TkDefaultFont", 8)).pack(side=tk.LEFT, padx=(0, 4))
        
        link = ttk.Label(footer_inner, text="GitHub Issues", foreground="#3a86ff", cursor="hand2", font=("TkDefaultFont", 8, "underline"))
        link.pack(side=tk.LEFT)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/PrincejiCoder/StockHistoryDownloader/issues"))
        
    def _on_format_change(self, *args):
        fmt = self.format_var.get().upper()
        self.save_btn.config(text=f"Save {fmt}")
        self.config.last_export_format = self.format_var.get()
        ConfigManager.save(self.config)
        
    def _start_search(self, query: str):
        if not query:
            return
        self.search_bar.entry.config(state="disabled")
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()
        
    def _search_thread(self, query: str):
        try:
            results = YahooAPI.search_ticker(query)
            self.after(0, lambda: self._on_search_complete(results))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Search Error", str(e)))
            self.after(0, lambda: self.search_bar.entry.config(state="normal"))
            
    def _on_search_complete(self, results):
        self.search_bar.entry.config(state="normal")
        self.search_bar.update_suggestions(results)
        
    def _on_symbol_select(self, result: SearchResult):
        self.selected_symbol = result
        self.metadata_lbl.config(text=result.metadata_text)
        
        # Update config
        self.config.add_recent_search(result.symbol)
        ConfigManager.save(self.config)
        
    def _start_fetch(self):
        if not self.selected_symbol:
            messagebox.showwarning("Warning", "Please search and select a symbol first.")
            return
            
        self.fetch_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Downloading...")
        self._cancel_requested = False
        
        period = self.period_var.get()
        interval = self.interval_var.get()
        symbol = self.selected_symbol.symbol
        
        # Update config
        self.config.last_period = period
        self.config.last_interval = interval
        ConfigManager.save(self.config)
        
        threading.Thread(target=self._fetch_thread, args=(symbol, period, interval), daemon=True).start()
        
    def _cancel_fetch(self):
        self._cancel_requested = True
        self.status_lbl.config(text="Cancelling...")
        
    def _fetch_thread(self, symbol, period, interval):
        try:
            df = YahooAPI.fetch_history(symbol, period, interval)
            if self._cancel_requested:
                self.after(0, self._on_fetch_cancelled)
            else:
                self.after(0, lambda: self._on_fetch_complete(df))
        except Exception as e:
            self.after(0, lambda: self._on_fetch_error(str(e)))
            
    def _on_fetch_cancelled(self):
        self.fetch_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="Download cancelled.")
        
    def _on_fetch_error(self, err_msg):
        self.fetch_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="")
        messagebox.showerror("Download Error", err_msg)
        
    def _on_fetch_complete(self, df: pd.DataFrame):
        self.fetch_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        
        if df.empty:
            self.status_lbl.config(text="No data found for the selected period/interval.")
            self.current_df = None
            self.save_btn.config(state=tk.DISABLED)
            self.row_count_lbl.config(text="")
            self.preview_table.load_data(None)
            return
            
        self.current_df = df
        self.status_lbl.config(text="Download complete!")
        self.save_btn.config(state=tk.NORMAL)
        
        # Update preview and stats
        self.preview_table.load_data(df)
        
        start_date = df['datetime'].min().strftime("%Y-%m-%d")
        end_date = df['datetime'].max().strftime("%Y-%m-%d")
        self.row_count_lbl.config(text=f"Downloaded {len(df)} rows ({start_date} to {end_date})")
        
    def _save_data(self):
        if self.current_df is None or self.selected_symbol is None:
            return
            
        fmt = self.format_var.get()
        symbol = self.selected_symbol.symbol
        
        default_ext = f".{fmt}"
        filetypes = [("CSV Files", "*.csv")] if fmt == "csv" else [("JSON Files", "*.json")]
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            initialfile=f"{symbol}_data{default_ext}",
            filetypes=filetypes
        )
        
        if not filepath:
            return
            
        try:
            metadata = {
                "Ticker": symbol,
                "Company": self.selected_symbol.short_name,
                "Interval": self.interval_var.get(),
                "Period": self.period_var.get()
            }
            
            if fmt == "csv":
                DataExporter.export_csv(self.current_df, filepath, metadata)
            else:
                DataExporter.export_json(self.current_df, filepath, metadata)
                
            show_post_save_dialog(self, filepath)
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            messagebox.showerror("Save Error", f"Failed to save file:\n{e}")
            
    def _validate_and_adjust_options(self, changed_widget: str):
        period = self.period_var.get()
        interval = self.interval_var.get()
        
        all_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        all_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
        
        interval_durations = {
            "1m": 1, "2m": 2, "5m": 5, "15m": 15, "30m": 30, "60m": 60, "90m": 90, "1h": 60,
            "1d": 1440, "5d": 7200, "1wk": 10080, "1mo": 43200, "3mo": 129600
        }
        
        # Mapping from interval to its allowed periods, taking into account:
        # 1. Yahoo constraints (1m max 7d, 2m-90m max 60d, 1h max 2y)
        # 2. Logical constraint: interval duration < period duration
        interval_to_periods = {
            "1m": ["1d", "5d"],
            "2m": ["1d", "5d", "1mo"],
            "5m": ["1d", "5d", "1mo"],
            "15m": ["1d", "5d", "1mo"],
            "30m": ["1d", "5d", "1mo"],
            "60m": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
            "90m": ["1d", "5d", "1mo"],
            "1h": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
            "1d": ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
            "5d": ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
            "1wk": ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
            "1mo": ["3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
            "3mo": ["6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        }
        
        allowed_intervals = [
            inv for inv in all_intervals 
            if period in interval_to_periods.get(inv, [])
        ]
        
        if changed_widget == "period":
            # If current interval is not allowed under the new period, adjust it to the next best
            if interval not in allowed_intervals:
                best_inv = min(
                    allowed_intervals,
                    key=lambda inv: abs(interval_durations[inv] - interval_durations[interval])
                )
                self.interval_var.set(best_inv)
                interval = best_inv
                
        # Rebuild the menu dynamically to enable/disable items
        self.interval_menu.delete(0, tk.END)
        for inv in all_intervals:
            state = "normal" if inv in allowed_intervals else "disabled"
            self.interval_menu.add_command(
                label=inv,
                state=state,
                command=lambda val=inv: self._on_menu_interval_select(val)
            )

    def _on_menu_interval_select(self, val: str):
        self.interval_var.set(val)
        self._validate_and_adjust_options("interval")

    def _show_info_tooltip(self, event):
        if hasattr(self, "_tooltip_window") and self._tooltip_window.winfo_exists():
            self._tooltip_window.destroy()
            return
            
        # Create a borderless toplevel window
        tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        
        # Position near the click
        x = event.x_root + 10
        y = event.y_root + 10
        tw.wm_geometry(f"+{x}+{y}")
        
        self._tooltip_window = tw
        
        text = (
            "Yahoo Finance Interval Constraints:\n"
            "• 1m: Max 7 days history.\n"
            "• 2m - 90m: Max 60 days history.\n"
            "• 60m / 1h: Max 730 days (2y) history.\n"
            "• Logical rule: Interval duration must be smaller than Period.\n\n"
            "Invalid options are grayed out and unclickable.\n"
            "They will auto-adjust to a working default if the period changes."
        )
        
        frame = ttk.Frame(tw, relief=tk.SOLID, borderwidth=1, padding=10)
        frame.pack()
        
        lbl = ttk.Label(frame, text=text, justify=tk.LEFT)
        lbl.pack()
        
        # Dismiss bindings
        tw.bind("<FocusOut>", lambda e: tw.destroy())
        self.bind("<Button-1>", self._dismiss_tooltip, add="+")
        
        tw.focus_set()
        
    def _dismiss_tooltip(self, event):
        if hasattr(self, "_tooltip_window") and self._tooltip_window.winfo_exists():
            x, y = event.x_root, event.y_root
            tx = self._tooltip_window.winfo_rootx()
            ty = self._tooltip_window.winfo_rooty()
            tw = self._tooltip_window.winfo_width()
            th = self._tooltip_window.winfo_height()
            
            if not (tx <= x <= tx + tw and ty <= y <= ty + th):
                self._tooltip_window.destroy()


