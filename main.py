from gui.main_window import MainWindow
import sys

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()