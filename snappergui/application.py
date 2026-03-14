import sys
import signal
from PySide6.QtWidgets import QApplication
from snappergui.mainWindow import SnapperGUI
from snappergui.propertiesDialog import propertiesDialog

def start_ui():
    app = Application(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())

class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        self.setApplicationName("SnapperGUI")
        self.setDesktopFileName("snappergui")

        self.snappergui = SnapperGUI(self)
        self.snappergui.show()

    def show_configs_properties(self):
        dialog = propertiesDialog(self.snappergui)
        dialog.exec()
