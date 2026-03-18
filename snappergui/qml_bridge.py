from PySide6.QtCore import QObject, Property, Signal, Slot, QAbstractListModel, QAbstractTableModel, Qt, QModelIndex, QVariant
from snappergui import snapper
from time import strftime, localtime
import os
import subprocess
import difflib
import time as time_module
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

class SnapshotModel(QAbstractTableModel):
    IDRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    PreIDRole = Qt.UserRole + 3
    DateRole = Qt.UserRole + 4
    UserRole = Qt.UserRole + 5
    DescriptionRole = Qt.UserRole + 6
    CleanupRole = Qt.UserRole + 7

    HEADERS = ["ID", "Type", "Pre ID", "Date", "User", "Description", "Cleanup"]

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

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._snapshots)):
            return None

        s = self._snapshots[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0: return str(s['id'])
            if col == 1: return s['type']
            if col == 2: return str(s['pre_id'])
            if col == 3: return s['date']
            if col == 4: return s['user']
            if col == 5: return s['description']
            if col == 6: return s['cleanup']

        if role == self.IDRole: return s['id']
        if role == self.TypeRole: return s['type']
        if role == self.PreIDRole: return s['pre_id']
        if role == self.DateRole: return s['date']
        if role == self.UserRole: return s['user']
        if role == self.DescriptionRole: return s['description']
        if role == self.CleanupRole: return s['cleanup']
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def roleNames(self):
        roles = super().roleNames()
        roles[self.IDRole] = b"snapshotId"
        roles[self.TypeRole] = b"snapshotType"
        roles[self.PreIDRole] = b"snapshotPreId"
        roles[self.DateRole] = b"snapshotDate"
        roles[self.UserRole] = b"snapshotUser"
        roles[self.DescriptionRole] = b"snapshotDescription"
        roles[self.CleanupRole] = b"snapshotCleanup"
        return roles

    @Slot(int, result=list)
    def getUserdata(self, row):
        if 0 <= row < len(self._snapshots):
            ud = self._snapshots[row]['userdata']
            return [{'key': k, 'value': v} for k, v in ud.items()]
        return []

    @Slot(int, result=int)
    def getSnapshotId(self, row):
        if 0 <= row < len(self._snapshots):
            return self._snapshots[row]['id']
        return -1

class ComparisonModel(QAbstractListModel):
    PathRole = Qt.UserRole + 1
    StatusRole = Qt.UserRole + 2
    StatusTextRole = Qt.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._files)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._files)):
            return None
        f = self._files[index.row()]
        if role == Qt.DisplayRole or role == self.PathRole:
            return f['name']
        if role == self.StatusRole:
            return f['status']
        if role == self.StatusTextRole:
            return self.status_to_string(f['status'])
        return None

    def roleNames(self):
        roles = super().roleNames()
        roles[self.PathRole] = b"path"
        roles[self.StatusRole] = b"status"
        roles[self.StatusTextRole] = b"statusText"
        return roles

    def status_to_string(self, status):
        if status & 1: return "Created"
        if status & 2: return "Deleted"
        if status > 0: return "Modified"
        return "No changes"

    @Slot(str, int, int)
    def compare(self, config, begin, end):
        self.beginResetModel()
        try:
            snapper.CreateComparison(config, begin, end)
            self._files = snapper.GetFiles(config, begin, end)
            snapper.DeleteComparison(config, begin, end)
        except Exception as e:
            print(f"Error comparing: {e}")
            self._files = []
        self.endResetModel()

class SnapperBridge(QObject):
    configChanged = Signal()
    message = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._configModel = ConfigListModel()
        self._snapshotModel = SnapshotModel()
        self._comparisonModel = ComparisonModel()
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

    @Property(QObject, constant=True)
    def comparison(self):
        return self._comparisonModel

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
        try:
            snapper.CreateSingleSnapshot(config, description, cleanup, userdata)
            self.message.emit(self.tr("Snapshot created for {}").format(config))
        except Exception as e:
            self.message.emit(self.tr("Error: {}").format(str(e)))

    @Slot(str, list)
    def deleteSnapshots(self, config, ids):
        try:
            snapper.DeleteSnapshots(config, ids)
            self.message.emit(self.tr("Snapshots deleted from {}").format(config))
        except Exception as e:
            self.message.emit(self.tr("Error: {}").format(str(e)))

    @Slot(str, str, str, str)
    def createConfig(self, name, subvolume, fstype, template):
        try:
            snapper.CreateConfig(name, subvolume, fstype, template)
            self.message.emit(self.tr("Configuration {} created").format(name))
        except Exception as e:
            self.message.emit(self.tr("Error: {}").format(str(e)))

    @Slot(str, result=dict)
    def getConfig(self, name):
        try:
            return snapper.GetConfig(name)
        except Exception as e:
            print(f"Error getting config: {e}")
            return {}

    @Slot(str, 'QVariantMap')
    def setConfig(self, name, attrs):
        try:
            snapper.SetConfig(name, attrs)
            self.message.emit(self.tr("Configuration {} updated").format(name))
        except Exception as e:
            self.message.emit(self.tr("Error: {}").format(str(e)))

    @Slot(str, int)
    def openSnapshotFolder(self, config, snap_id):
        try:
            mountpoint = snapper.GetMountPoint(config, snap_id)
            snapshot_data = snapper.GetSnapshot(config, snap_id)
            if snapshot_data[6] != '':
                 snapper.MountSnapshot(config, snap_id, True)

            subprocess.Popen(['xdg-open', mountpoint])
            self.message.emit(self.tr("Opening {}").format(mountpoint))
        except Exception as e:
            self.message.emit(self.tr("Error: {}").format(str(e)))

    @Slot(str, int, int, int, result=str)
    def getDiff(self, config, begin, end, mode, rel_path):
        # mode: 0=begin, 1=diff, 2=end
        try:
            begin_path = snapper.GetMountPoint(config, begin)
            end_path = snapper.GetMountPoint(config, end)

            fromfile = os.path.join(begin_path, rel_path.lstrip('/'))
            tofile = os.path.join(end_path, rel_path.lstrip('/'))

            def get_lines(path):
                if not os.path.exists(path): return None, False
                try:
                    with open(path, 'rb') as f:
                        if b'\x00' in f.read(8192): return None, True
                    with open(path, 'r', errors='replace') as f:
                        return f.readlines(), False
                except: return None, False

            if mode == 0:
                lines, binary = get_lines(fromfile)
                return "[Binary file]" if binary else ("".join(lines) if lines else "")
            elif mode == 2:
                lines, binary = get_lines(tofile)
                return "[Binary file]" if binary else ("".join(lines) if lines else "")
            else:
                flines, fbin = get_lines(fromfile)
                tlines, tbin = get_lines(tofile)
                if fbin or tbin: return "[Binary file]"

                flines = flines or []
                tlines = tlines or []

                fdate = time_module.ctime(os.stat(fromfile).st_mtime) if os.path.exists(fromfile) else ""
                tdate = time_module.ctime(os.stat(tofile).st_mtime) if os.path.exists(tofile) else ""

                diff = difflib.unified_diff(flines, tlines, fromfile=fromfile, tofile=tofile, fromfiledate=fdate, tofiledate=tdate)
                return "".join(diff)
        except Exception as e:
            return f"Error: {e}"

    def _on_snapshot_created(self, config, num):
        if config == self._currentConfig:
            self._snapshotModel.refresh()

    def _on_snapshots_deleted(self, config, nums):
        if config == self._currentConfig:
            self._snapshotModel.refresh()

    def _on_config_created(self, config):
        self._configModel.refresh()
