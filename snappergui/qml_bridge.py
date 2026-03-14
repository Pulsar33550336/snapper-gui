from PySide6.QtCore import QObject, Property, Signal, Slot, QAbstractListModel, Qt, QModelIndex
from snappergui import snapper
from time import strftime, localtime
from pwd import getpwuid

class ConfigListModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._configs = []
        self.refresh()

    def rowCount(self, parent=QModelIndex()):
        return len(self._configs)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._configs)):
            return None
        if role == Qt.DisplayRole:
            return self._configs[index.row()]
        return None

    @Slot()
    def refresh(self):
        self.beginResetModel()
        try:
            self._configs = snapper.ListConfigs()
        except Exception as e:
            print(f"Error listing configs: {e}")
            self._configs = []
        self.endResetModel()

class SnapshotModel(QAbstractListModel):
    IDRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    PreIDRole = Qt.UserRole + 3
    DateRole = Qt.UserRole + 4
    UserRole = Qt.UserRole + 5
    DescriptionRole = Qt.UserRole + 6
    CleanupRole = Qt.UserRole + 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshots = []
        self._config = ""

    def setConfig(self, config):
        if self._config == config:
            return
        self._config = config
        self.refresh()

    @Slot()
    def refresh(self):
        self.beginResetModel()
        if not self._config:
            self._snapshots = []
        else:
            try:
                raw_snapshots = snapper.ListSnapshots(self._config)
                self._snapshots = []
                for s in raw_snapshots:
                    # s: [id, type, pre_id, date, uid, description, cleanup, userdata]
                    date_str = "Now" if s[3] == -1 else strftime("%a %x %R", localtime(s[3]))
                    try:
                        user = getpwuid(s[4])[0]
                    except:
                        user = str(s[4])
                    type_str = {0: "single", 1: "pre", 2: "post"}.get(s[1], str(s[1]))

                    self._snapshots.append({
                        'id': s[0],
                        'type': type_str,
                        'pre_id': s[2] if s[2] != 0 else "",
                        'date': date_str,
                        'user': user,
                        'description': s[5],
                        'cleanup': s[6],
                        'userdata': s[7]
                    })
            except Exception as e:
                print(f"Error listing snapshots: {e}")
                self._snapshots = []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._snapshots)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._snapshots)):
            return None
        s = self._snapshots[index.row()]
        if role == self.IDRole: return s['id']
        if role == self.TypeRole: return s['type']
        if role == self.PreIDRole: return s['pre_id']
        if role == self.DateRole: return s['date']
        if role == self.UserRole: return s['user']
        if role == self.DescriptionRole: return s['description']
        if role == self.CleanupRole: return s['cleanup']
        return None

    def roleNames(self):
        return {
            self.IDRole: b"snapshotId",
            self.TypeRole: b"snapshotType",
            self.PreIDRole: b"snapshotPreId",
            self.DateRole: b"snapshotDate",
            self.UserRole: b"snapshotUser",
            self.DescriptionRole: b"snapshotDescription",
            self.CleanupRole: b"snapshotCleanup"
        }

    @Slot(int)
    def getUserdata(self, row):
        if 0 <= row < len(self._snapshots):
            ud = self._snapshots[row]['userdata']
            return [{'key': k, 'value': v} for k, v in ud.items()]
        return []

class SnapperBridge(QObject):
    configChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._configModel = ConfigListModel()
        self._snapshotModel = SnapshotModel()
        self._currentConfig = ""

        snapper.snapshotCreated.connect(self._on_snapshot_created)
        snapper.snapshotsDeleted.connect(self._on_snapshots_deleted)
        snapper.configCreated.connect(self._on_config_created)

    @Property(QObject, constant=True)
    def configs(self):
        return self._configModel

    @Property(QObject, constant=True)
    def snapshots(self):
        return self._snapshotModel

    @Property(str, notify=configChanged)
    def currentConfig(self):
        return self._currentConfig

    @currentConfig.setter
    def currentConfig(self, val):
        if self._currentConfig != val:
            self._currentConfig = val
            self._snapshotModel.setConfig(val)
            self.configChanged.emit()

    @Slot(str, str, str, 'QVariantMap')
    def createSnapshot(self, config, description, cleanup, userdata):
        snapper.CreateSingleSnapshot(config, description, cleanup, userdata)

    @Slot(str, list)
    def deleteSnapshots(self, config, ids):
        snapper.DeleteSnapshots(config, ids)

    def _on_snapshot_created(self, config, num):
        if config == self._currentConfig:
            self._snapshotModel.refresh()

    def _on_snapshots_deleted(self, config, nums):
        if config == self._currentConfig:
            self._snapshotModel.refresh()

    def _on_config_created(self, config):
        self._configModel.refresh()
