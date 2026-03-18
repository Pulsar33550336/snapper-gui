import sys
import signal
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTranslator, QLocale
from snappergui.mainWindow import SnapperGUI
from snappergui.propertiesDialog import propertiesDialog
from snappergui.qml_bridge import SnapperBridge
import os

def start_ui():
    app = Application(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec())

class Application(QApplication):
    def __init__(self, args):
        super(Application, self).__init__(args)
        self.setApplicationName("SnapperGUI")
        self.setDesktopFileName("snappergui")

        self.translator = QTranslator()
        # Find translations in snappergui/i18n/snappergui_*.qm
        i18n_path = os.path.join(os.path.dirname(__file__), "i18n")
        if self.translator.load(QLocale(), "snappergui", "_", i18n_path):
            self.installTranslator(self.translator)

        # Default to QML
        if "--widgets" not in args:
            self.engine = QQmlApplicationEngine()
            self.bridge = SnapperBridge()
            self.engine.rootContext().setContextProperty("snapper", self.bridge)
            qml_file = os.path.join(os.path.dirname(__file__), "main.qml")
            self.engine.load(qml_file)
            if not self.engine.rootObjects():
                sys.exit(-1)
        else:
            self.snappergui = SnapperGUI(self)
            self.snappergui.show()

    def show_configs_properties(self):
        if hasattr(self, 'snappergui'):
            dialog = propertiesDialog(self.snappergui)
            dialog.exec()
