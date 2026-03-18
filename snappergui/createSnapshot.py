from snappergui import snapper
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QTreeView, QPushButton,
                             QDialogButtonBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

class createSnapshot(QDialog):
    def __init__(self, parent, config_name):
        super(createSnapshot, self).__init__(parent)
        self.setWindowTitle(self.tr("Create Snapshot"))
        self.resize(400, 300)

        self.layout = QVBoxLayout(self)

        # Config
        self.layout.addWidget(QLabel(self.tr("Configuration:")))
        self.configs_combo = QComboBox()
        self.layout.addWidget(self.configs_combo)

        configs = snapper.ListConfigs()
        for i, config in enumerate(configs):
            name = str(config)
            self.configs_combo.addItem(name)
            if name == config_name:
                self.configs_combo.setCurrentIndex(i)

        # Description
        self.layout.addWidget(QLabel(self.tr("Description:")))
        self.description_edit = QLineEdit()
        self.layout.addWidget(self.description_edit)

        # Cleanup
        self.layout.addWidget(QLabel(self.tr("Cleanup Algorithm:")))
        self.cleanup_combo = QComboBox()
        self.cleanup_combo.addItems([self.tr("None"), "number", "timeline", "empty-pre-post"])
        self.layout.addWidget(self.cleanup_combo)

        # Userdata
        self.layout.addWidget(QLabel(self.tr("Userdata:")))
        self.userdata_tree = QTreeView()
        self.userdata_model = QStandardItemModel(0, 2)
        self.userdata_model.setHorizontalHeaderLabels([self.tr("Key"), self.tr("Value")])
        self.userdata_tree.setModel(self.userdata_model)
        self.layout.addWidget(self.userdata_tree)

        self.type_here_text = self.tr("<Type here>")
        self.userdata_model.appendRow([QStandardItem(self.type_here_text), QStandardItem("")])
        self.userdata_model.itemChanged.connect(self.on_item_changed)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def on_item_changed(self, item):
        if item.text() != "" and item.text() != self.type_here_text:
            # If we edited the "Type here" row, add a new one
            if item.row() == self.userdata_model.rowCount() - 1:
                 self.userdata_model.appendRow([QStandardItem(self.type_here_text), QStandardItem("")])

    @property
    def config(self):
        return self.configs_combo.currentText()

    @property
    def description(self):
        return self.description_edit.text()

    @property
    def cleanup(self):
        c = self.cleanup_combo.currentText()
        if c == self.tr("None"):
            return ""
        return c

    @property
    def userdata(self):
        data = {}
        for i in range(self.userdata_model.rowCount()):
            key = self.userdata_model.item(i, 0).text()
            val = self.userdata_model.item(i, 1).text()
            if key and key != self.type_here_text:
                data[key] = val
        return data
