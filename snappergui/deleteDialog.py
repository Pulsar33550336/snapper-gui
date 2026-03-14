from snappergui import snapper
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTreeView, QDialogButtonBox, QLabel)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
from pwd import getpwuid

class deleteDialog(QDialog):
    def __init__(self, parent, config, snapshots):
        super(deleteDialog, self).__init__(parent)
        self.setWindowTitle("Delete Snapshots")
        self.resize(400, 300)
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Select snapshots to delete:"))

        self.treeview = QTreeView()
        self.model = QStandardItemModel(0, 4)
        self.model.setHorizontalHeaderLabels(["Delete", "ID", "User", "Description"])
        self.treeview.setModel(self.model)
        self.layout.addWidget(self.treeview)

        self.to_delete = list(snapshots)

        parents = {}
        for snap_id in snapshots:
            try:
                snapinfo = snapper.GetSnapshot(config, snap_id)
                items = self.get_row_items(snapinfo)

                if snapinfo[1] == 1: # Pre
                    self.model.appendRow(items)
                    parents[snap_id] = items[0]
                elif snapinfo[1] == 2: # Post
                    parent_id = snapinfo[2]
                    if parent_id in parents:
                        parents[parent_id].appendRow(items)
                    else:
                        self.model.appendRow(items)
                else: # Single
                    self.model.appendRow(items)
            except Exception as e:
                print(f"Error loading snapshot {snap_id} for deletion: {e}")

        self.treeview.expandAll()
        self.model.itemChanged.connect(self.on_item_changed)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_row_items(self, snapinfo):
        check_item = QStandardItem()
        check_item.setCheckable(True)
        check_item.setCheckState(Qt.Checked)
        check_item.setData(snapinfo[0], Qt.UserRole)

        try:
            user = getpwuid(snapinfo[4])[0]
        except:
            user = str(snapinfo[4])

        return [
            check_item,
            QStandardItem(str(snapinfo[0])),
            QStandardItem(user),
            QStandardItem(snapinfo[5])
        ]

    def on_item_changed(self, item):
        if item.column() == 0:
            snap_id = item.data(Qt.UserRole)
            if item.checkState() == Qt.Checked:
                if snap_id not in self.to_delete:
                    self.to_delete.append(snap_id)
            else:
                if snap_id in self.to_delete:
                    self.to_delete.remove(snap_id)
