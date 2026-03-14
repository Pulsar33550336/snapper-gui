from snappergui import snapper
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
from time import strftime, localtime
from pwd import getpwuid

class snapshotsView(QTreeView):
    def __init__(self, config):
        super(snapshotsView, self).__init__()
        self.config = config
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        self._model = QStandardItemModel(0, 7)
        self._model.setHorizontalHeaderLabels([
            "ID", "Type", "Pre ID", "Date", "User", "Description", "Cleanup"
        ])
        self.setModel(self._model)
        self._model.itemChanged.connect(self.on_item_changed)
        
        self.update_view()

    def update_view(self):
        self._model.clear()
        self._model.setHorizontalHeaderLabels([
            "ID", "Type", "Pre ID", "Date", "User", "Description", "Cleanup"
        ])
        
        try:
            snapshots_list = snapper.ListSnapshots(self.config)
        except Exception as e:
            print(f"Error listing snapshots for {self.config}: {e}")
            return

        if not snapshots_list:
            return

        parents = {}
        # type 1: pre, 2: post, 0: single
        for snapshot in snapshots_list:
            items = self.create_snapshot_items(snapshot)
            
            if snapshot[1] == 1:  # Pre snapshot
                self._model.appendRow(items)
                parents[snapshot[0]] = items[0]
            elif snapshot[1] == 2:  # Post snapshot
                parent_id = snapshot[2]
                if parent_id in parents:
                    parents[parent_id].appendRow(items)
                else:
                    self._model.appendRow(items)
            else:  # Single snapshot
                self._model.appendRow(items)

    def create_snapshot_items(self, snapshot):
        # snapshot format from DBus: [id, type, pre_id, date, uid, description, cleanup, userdata_dict]
        if snapshot[3] == -1:
            date_str = "Now"
        else:
            date_str = strftime("%a %x %R", localtime(snapshot[3]))
        
        try:
            user = getpwuid(snapshot[4])[0]
        except:
            user = str(snapshot[4])

        type_str = {0: "single", 1: "pre", 2: "post"}.get(snapshot[1], str(snapshot[1]))

        items = [
            QStandardItem(str(snapshot[0])),
            QStandardItem(type_str),
            QStandardItem(str(snapshot[2]) if snapshot[2] != 0 else ""),
            QStandardItem(date_str),
            QStandardItem(user),
            QStandardItem(snapshot[5]),
            QStandardItem(snapshot[6])
        ]
        
        # ID item stores the actual ID for easier retrieval
        items[0].setData(snapshot[0], Qt.UserRole)
        
        # Make most items read-only
        for i in range(5):
            items[i].setEditable(False)
            
        return items

    def add_snapshot_to_tree(self, snapshot_id):
        try:
            snapinfo = snapper.GetSnapshot(self.config, snapshot_id)
            items = self.create_snapshot_items(snapinfo)
            
            if snapinfo[1] == 2: # Post
                pre_id = snapinfo[2]
                parent_item = self.find_item_by_id(pre_id)
                if parent_item:
                    parent_item.appendRow(items)
                    return
            
            self._model.appendRow(items)
        except Exception as e:
            print(f"Error adding snapshot to tree: {e}")

    def remove_snapshot_from_tree(self, snapshot_id):
        item = self.find_item_by_id(snapshot_id)
        if item:
            parent = item.parent()
            if parent:
                parent.removeRow(item.row())
            else:
                self._model.removeRow(item.row())

    def find_item_by_id(self, snapshot_id, parent=None):
        if parent is None:
            parent = self._model.invisibleRootItem()
            
        for i in range(parent.rowCount()):
            item = parent.child(i, 0)
            if item.data(Qt.UserRole) == snapshot_id:
                return item
            child_result = self.find_item_by_id(snapshot_id, item)
            if child_result:
                return child_result
        return None

    def on_item_changed(self, item):
        if item.column() not in [5, 6]:
            return
            
        row_id_item = self._model.item(item.row(), 0)
        if not row_id_item: # Could be a child item
            # Find the ID item in the same row
            parent = item.parent() or self._model.invisibleRootItem()
            row_id_item = parent.child(item.row(), 0)
            
        snapshot_id = row_id_item.data(Qt.UserRole)
        
        try:
            snapshot_info = snapper.GetSnapshot(self.config, snapshot_id)
            description = snapshot_info[5]
            cleanup = snapshot_info[6]
            
            if item.column() == 5:
                description = item.text()
            elif item.column() == 6:
                cleanup = item.text()
                
            snapper.SetSnapshot(self.config, snapshot_id, description, cleanup, snapshot_info[7])
        except Exception as e:
            print(f"Error setting snapshot properties: {e}")
