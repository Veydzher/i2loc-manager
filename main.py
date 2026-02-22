import sys
import traceback

print("[DEBUG] main.py - Importing PySide6...")
try:
    from PySide6 import QtWidgets

    print("[DEBUG] main.py - PySide6 imported.")
except ImportError as e:
    print(f"[FATAL] Failed to import PySide6: {e}\n{traceback.format_exc()}")
    sys.exit(1)
except Exception as e:
    print(f"[FATAL] Unexpected error importing PySide6: {e}\n{traceback.format_exc()}")
    sys.exit(1)

print("[DEBUG] main.py - Importing I2ManagerUI...")
try:
    from gui.main_window import I2ManagerUI

    print("[DEBUG] main.py - I2ManagerUI imported.")
except ImportError as e:
    print(f"[FATAL] Failed to import I2ManagerUI: {e}\n{traceback.format_exc()}")
    sys.exit(1)
except Exception as e:
    print(f"[FATAL] Unexpected error importing I2ManagerUI: {e}\n{traceback.format_exc()}")
    sys.exit(1)


def main():
    try:
        print("[DEBUG] main.py - Creating QApplication...")
        app = QtWidgets.QApplication(sys.argv)
        print("[DEBUG] main.py - QApplication created.")

        print("[DEBUG] main.py - Creating I2ManagerUI window...")
        window = I2ManagerUI()
        print("[DEBUG] main.py - I2ManagerUI window created.")

        print("[DEBUG] main.py - Showing window...")
        window.show()
        print("[DEBUG] main.py - Starting app event loop...")
        exit_code = app.exec()
        sys.exit(exit_code)

    except SystemExit as e:
        print(f"[DEBUG] Application exited with code: {e.code}")

    except Exception as e:
        try:
            if QtWidgets.QApplication.instance():
                QtWidgets.QMessageBox.critical(None, "Fatal Error", f"A critical error occurred:\n{e}")
            else:
                print(f"[FATAL] (QApplication not available for MessageBox): {e}\n{traceback.format_exc()}")
        except Exception as error:
            print(f"[FATAL] {e}\n{traceback.format_exc()}")
            print(f"QMessageBox error: {error}\n{traceback.format_exc(error)}")
        sys.exit(1)


if __name__ == "__main__":
    print("[DEBUG] main.py - Running __main__ block...")
    main()
