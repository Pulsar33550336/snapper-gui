from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                             QComboBox, QDialogButtonBox)

class createConfig(QDialog):
    def __init__(self, parent):
        super(createConfig, self).__init__(parent)
        self.setWindowTitle("Create Configuration")
        self.layout = QVBoxLayout(self)

        # Name
        self.layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.layout.addWidget(self.name_edit)

        # Subvolume
        self.layout.addWidget(QLabel("Subvolume (path):"))
        self.subvolume_edit = QLineEdit()
        self.layout.addWidget(self.subvolume_edit)

        # FS Type
        self.layout.addWidget(QLabel("Filesystem Type:"))
        self.fstype_combo = QComboBox()
        self.fstype_combo.addItems(["btrfs", "ext4", "lvm"])
        self.layout.addWidget(self.fstype_combo)

        # Template
        self.layout.addWidget(QLabel("Template:"))
        self.template_edit = QLineEdit("default")
        self.layout.addWidget(self.template_edit)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    @property
    def name(self): return self.name_edit.text()

    @property
    def subvolume(self): return self.subvolume_edit.text()

    @property
    def fstype(self): return self.fstype_combo.currentText()

    @property
    def template(self): return self.template_edit.text()
