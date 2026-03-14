import dbus
import dbus.mainloop.glib
from PySide6.QtCore import QObject, Signal, Slot

class SnapperInterface(QObject):
    # Signals for external use (Qt signals)
    snapshotCreated = Signal(str, int)
    snapshotModified = Signal(str, int)
    snapshotsDeleted = Signal(str, list)
    configCreated = Signal(str)
    configModified = Signal()
    configDeleted = Signal()

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()
        # Essential for dbus-python signals in a Qt app
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self._iface = None
        try:
            self._bus = dbus.SystemBus()
            self._obj = self._bus.get_object('org.opensuse.Snapper', '/org/opensuse/Snapper')
            self._iface = dbus.Interface(self._obj, 'org.opensuse.Snapper')

            # Connect DBus signals to internal handlers that emit Qt signals
            self._bus.add_signal_receiver(
                self._handle_snapshot_created,
                signal_name="SnapshotCreated",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
            self._bus.add_signal_receiver(
                self._handle_snapshot_modified,
                signal_name="SnapshotModified",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
            self._bus.add_signal_receiver(
                self._handle_snapshots_deleted,
                signal_name="SnapshotsDeleted",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
            self._bus.add_signal_receiver(
                self._handle_config_created,
                signal_name="ConfigCreated",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
            self._bus.add_signal_receiver(
                self._handle_config_modified,
                signal_name="ConfigModified",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
            self._bus.add_signal_receiver(
                self._handle_config_deleted,
                signal_name="ConfigDeleted",
                dbus_interface="org.opensuse.Snapper",
                bus_name="org.opensuse.Snapper"
            )
        except Exception as e:
            print(f"Error initializing DBus: {e}")

    def _native(self, obj):
        """Recursively convert dbus types to Python native types"""
        if isinstance(obj, dbus.String):
            return str(obj)
        if isinstance(obj, dbus.Boolean):
            return bool(obj)
        if isinstance(obj, (dbus.Int16, dbus.Int32, dbus.Int64,
                            dbus.UInt16, dbus.UInt32, dbus.UInt64,
                            dbus.Byte)):
            return int(obj)
        if isinstance(obj, dbus.Double):
            return float(obj)
        if isinstance(obj, (dbus.Array, list, tuple)):
            return [self._native(i) for i in obj]
        if isinstance(obj, (dbus.Dictionary, dict)):
            return {self._native(k): self._native(v) for k, v in obj.items()}
        if isinstance(obj, dbus.Struct):
            return tuple(self._native(i) for i in obj)
        return obj

    def _call(self, method, *args):
        if not self._iface:
            raise Exception("Snapper DBus interface not initialized")
        try:
            fn = getattr(self._iface, method)
            result = fn(*args)
            return self._native(result)
        except Exception as e:
            raise Exception(f"Snapper DBus Error ({method}): {e}")

    # Internal handlers to relay signals to Qt
    def _handle_snapshot_created(self, config, num):
        self.snapshotCreated.emit(str(config), int(num))

    def _handle_snapshot_modified(self, config, num):
        self.snapshotModified.emit(str(config), int(num))

    def _handle_snapshots_deleted(self, config, nums):
        self.snapshotsDeleted.emit(str(config), [int(n) for n in nums])

    def _handle_config_created(self, config):
        self.configCreated.emit(str(config))

    def _handle_config_modified(self):
        self.configModified.emit()

    def _handle_config_deleted(self):
        self.configDeleted.emit()

    # API Methods
    def ListConfigs(self):
        try:
            raw = self._call('ListConfigs')
            if not raw: return []
            return [str(item[0]) for item in raw]
        except:
            return []

    def ListSnapshots(self, config: str):
        try:
            raw = self._call('ListSnapshots', config)
            return [tuple(item) for item in raw]
        except:
            return []

    def GetSnapshot(self, config: str, number: int):
        return tuple(self._call('GetSnapshot', config, dbus.UInt32(number)))

    def SetSnapshot(self, config: str, number: int, description: str, cleanup: str, userdata: dict):
        self._call('SetSnapshot', config, dbus.UInt32(number), description, cleanup, userdata)

    def CreateSingleSnapshot(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreateSingleSnapshot', config, description, cleanup, userdata)

    def CreateSingleSnapshotOfDefault(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreateSingleSnapshotOfDefault', config, description, cleanup, userdata)

    def CreatePreSnapshot(self, config: str, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreatePreSnapshot', config, description, cleanup, userdata)

    def CreatePostSnapshot(self, config: str, pre_num: int, description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreatePostSnapshot', config, dbus.UInt32(pre_num), description, cleanup, userdata)

    def DeleteSnapshots(self, config: str, ids: list):
        self._call('DeleteSnapshots', config, dbus.Array([dbus.UInt32(i) for i in ids], signature='u'))

    def MountSnapshot(self, config: str, number: int, read_only: bool) -> str:
        return self._call('MountSnapshot', config, dbus.UInt32(number), dbus.Boolean(read_only))

    def UmountSnapshot(self, config: str, number: int, read_only: bool):
        self._call('UmountSnapshot', config, dbus.UInt32(number), dbus.Boolean(read_only))

    def GetMountPoint(self, config: str, number: int) -> str:
        return self._call('GetMountPoint', config, dbus.UInt32(number))

    def CreateConfig(self, name: str, subvolume: str, fstype: str, template: str):
        self._call('CreateConfig', name, subvolume, fstype, template)

    def SetConfig(self, name: str, attrs: dict):
        self._call('SetConfig', name, attrs)

    def DeleteConfig(self, name: str):
        self._call('DeleteConfig', name)

    def GetConfig(self, name: str) -> dict:
        n, subvol, attrs = self._call('GetConfig', name)
        return {'name': n, 'subvolume': subvol, 'attrs': attrs}

    def CreateComparison(self, config: str, begin: int, end: int) -> int:
        return self._call('CreateComparison', config, dbus.UInt32(begin), dbus.UInt32(end))

    def DeleteComparison(self, config: str, begin: int, end: int):
        self._call('DeleteComparison', config, dbus.UInt32(begin), dbus.UInt32(end))

    def GetFiles(self, config: str, begin: int, end: int) -> list:
        raw = self._call('GetFiles', config, dbus.UInt32(begin), dbus.UInt32(end))
        return [{'name': path, 'status': status} for path, status in raw]

snapper = SnapperInterface.get_instance()
