import sys
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusArgument
from PySide6.QtCore import QObject, Signal, Slot

def unpack(val, depth=0):
    if depth > 10:
        return str(val)
    if isinstance(val, QDBusArgument):
        inner = val.asVariant()
        if isinstance(inner, QDBusArgument):
            return str(inner)
        return unpack(inner, depth + 1)
    if isinstance(val, list):
        return [unpack(i, depth + 1) for i in val]
    if isinstance(val, tuple):
        return tuple(unpack(i, depth + 1) for i in val)
    if isinstance(val, dict):
        return {k: unpack(v, depth + 1) for k, v in val.items()}
    return val

class SnapperInterface(QObject):
    # Signals for external use
    snapshotCreated = Signal(str, int)
    snapshotModified = Signal(str, int)
    snapshotsDeleted = Signal(str, list)
    configCreated = Signal(str)
    configModified = Signal()
    configDeleted = Signal()

    def __init__(self):
        super().__init__()
        self._bus = QDBusConnection.systemBus()
        if not self._bus.isConnected():
            # In some environments (like testing) DBus might not be available
            pass

        self._interface = QDBusInterface(
            "org.opensuse.Snapper",
            "/org/opensuse/Snapper",
            "org.opensuse.Snapper",
            self._bus
        )

        # Connect D-Bus signals to our internal slots
        # Signature: connect(service, path, interface, name, receiver, slot)
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "SnapshotCreated", self, "handleSnapshotCreated(QString,uint)"
        )
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "SnapshotModified", self, "handleSnapshotModified(QString,uint)"
        )
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "SnapshotsDeleted", self, "handleSnapshotsDeleted(QString,QList<uint>)"
        )
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "ConfigCreated", self, "handleConfigCreated(QString)"
        )
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "ConfigModified", self, "handleConfigModified()"
        )
        self._bus.connect(
            "org.opensuse.Snapper", "/org/opensuse/Snapper", "org.opensuse.Snapper",
            "ConfigDeleted", self, "handleConfigDeleted()"
        )

    @Slot(str, int)
    def handleSnapshotCreated(self, config, num):
        self.snapshotCreated.emit(config, num)

    @Slot(str, int)
    def handleSnapshotModified(self, config, num):
        self.snapshotModified.emit(config, num)

    @Slot(str, list)
    def handleSnapshotsDeleted(self, config, nums):
        self.snapshotsDeleted.emit(config, list(nums))

    @Slot(str)
    def handleConfigCreated(self, config):
        self.configCreated.emit(config)

    @Slot()
    def handleConfigModified(self):
        self.configModified.emit()

    @Slot()
    def handleConfigDeleted(self):
        self.configDeleted.emit()

    def _call(self, method, *args):
        msg = self._interface.call(method, *args)
        if msg.type() == QDBusMessage.MessageType.ErrorMessage:
            raise Exception(f"Snapper DBus Error ({method}): {msg.errorMessage()}")

        res = msg.arguments()
        if not res:
            return None
        if len(res) == 1:
            return unpack(res[0])
        return [unpack(a) for a in res]

    # API Methods
    def ListConfigs(self):
        try:
            raw = self._call('ListConfigs')
        except Exception as e:
            print(f"Error calling ListConfigs: {e}")
            return []
        if raw is None: return []
        # raw is list of (name, subvolume, attrs)
        if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], (list, tuple)):
             return [str(item[0]) for item in raw]
        return []

    def ListSnapshots(self, config: str):
        raw = self._call('ListSnapshots', str(config))
        if raw is None: return []
        return [tuple(item) for item in raw]

    def GetSnapshot(self, config: str, number: int):
        res = self._call('GetSnapshot', str(config), int(number))
        return tuple(res) if isinstance(res, (list, tuple)) else res

    def SetSnapshot(self, config: str, number: int, description: str, cleanup: str, userdata: dict):
        self._call('SetSnapshot', str(config), int(number), str(description), str(cleanup), userdata)

    def CreateSingleSnapshot(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreateSingleSnapshot', str(config), str(description), str(cleanup), userdata)

    def CreateSingleSnapshotOfDefault(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreateSingleSnapshotOfDefault', str(config), str(description), str(cleanup), userdata)

    def CreatePreSnapshot(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreatePreSnapshot', str(config), str(description), str(cleanup), userdata)

    def CreatePostSnapshot(self, config: str, pre_num: int, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreatePostSnapshot', str(config), int(pre_num), str(description), str(cleanup), userdata)

    def DeleteSnapshots(self, config: str, ids: list):
        self._call('DeleteSnapshots', str(config), [int(i) for i in ids])

    def MountSnapshot(self, config: str, number: int, read_only: bool) -> str:
        return self._call('MountSnapshot', str(config), int(number), bool(read_only))

    def UmountSnapshot(self, config: str, number: int, read_only: bool):
        self._call('UmountSnapshot', str(config), int(number), bool(read_only))

    def GetMountPoint(self, config: str, number: int) -> str:
        return self._call('GetMountPoint', str(config), int(number))

    def CreateConfig(self, name: str, subvolume: str, fstype: str, template: str):
        self._call('CreateConfig', str(name), str(subvolume), str(fstype), str(template))

    def SetConfig(self, name: str, attrs: dict):
        self._call('SetConfig', str(name), attrs)

    def DeleteConfig(self, name: str):
        self._call('DeleteConfig', str(name))

    def GetConfig(self, name: str) -> dict:
        res = self._call('GetConfig', str(name))
        if isinstance(res, (list, tuple)) and len(res) == 3:
            return {'name': res[0], 'subvolume': res[1], 'attrs': res[2]}
        return {}

    def CreateComparison(self, config: str, begin: int, end: int) -> int:
        return self._call('CreateComparison', str(config), int(begin), int(end))

    def DeleteComparison(self, config: str, begin: int, end: int):
        self._call('DeleteComparison', str(config), int(begin), int(end))

    def GetFiles(self, config: str, begin: int, end: int) -> list:
        raw = self._call('GetFiles', str(config), int(begin), int(end))
        if raw is None: return []
        return [{'name': path, 'status': status} for path, status in raw]

snapper = SnapperInterface()
