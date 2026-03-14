import dbus
import dbus.mainloop.glib
from gi.repository import GLib


class SnapperInterface:
    def __init__(self):
        # 初始化 GLib 主循环（信号需要）
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        self._bus = dbus.SystemBus()
        self._obj = self._bus.get_object(
            'org.opensuse.Snapper',
            '/org/opensuse/Snapper'
        )
        self._iface = dbus.Interface(
            self._obj,
            'org.opensuse.Snapper'
        )

    # ──────────────────────────────────────────
    # 内部工具
    # ──────────────────────────────────────────

    @staticmethod
    def _native(obj):
        """递归把 dbus.* 类型转成 Python 原生类型"""
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
            return [SnapperInterface._native(i) for i in obj]
        if isinstance(obj, (dbus.Dictionary, dict)):
            return {SnapperInterface._native(k): SnapperInterface._native(v)
                    for k, v in obj.items()}
        if isinstance(obj, dbus.Struct):
            return tuple(SnapperInterface._native(i) for i in obj)
        return obj

    def _call(self, method, *args):
        """调用 DBus 方法并返回 Python 原生类型"""
        fn = getattr(self._iface, method)
        result = fn(*args)
        return self._native(result)

    # ──────────────────────────────────────────
    # API
    # ──────────────────────────────────────────

    def ListConfigs(self):
        raw = self._call('ListConfigs')
        configs = [str(item[0]) for item in raw]
        print(f"Found configs: {configs}")
        return configs

    def ListSnapshots(self, config: str):
        """
        返回: [(id, type, pre_id, date, uid, description, cleanup, userdata), ...]
        下标与 snapshotsView 一致：[0]=id [1]=type [2]=pre_id [3]=date
                                    [4]=uid [5]=description [6]=cleanup [7]=userdata
        DBus 签名: a(uquxussa{ss})
        """
        raw = self._call('ListSnapshots', config)
        return [tuple(item) for item in raw]

    def GetSnapshot(self, config: str, number: int):
        """
        返回: (id, type, pre_id, date, uid, description, cleanup, userdata)
        DBus 签名: (uquxussa{ss})
        """
        return tuple(self._call('GetSnapshot', config, dbus.UInt32(number)))

    def SetSnapshot(self, config: str, number: int,
                    description: str, cleanup: str, userdata: dict):
        self._call('SetSnapshot', config, dbus.UInt32(number),
                   description, cleanup, userdata)

    def CreateSingleSnapshot(self, config: str, description: str,
                              cleanup: str, userdata: dict) -> int:
        """返回新快照编号"""
        return self._call('CreateSingleSnapshot',
                          config, description, cleanup, userdata)

    def CreateSingleSnapshotOfDefault(self, config: str, description: str,
                                       cleanup: str, userdata: dict) -> int:
        return self._call('CreateSingleSnapshotOfDefault',
                          config, description, cleanup, userdata)

    def CreatePreSnapshot(self, config: str, description: str,
                           cleanup: str, userdata: dict) -> int:
        return self._call('CreatePreSnapshot',
                          config, description, cleanup, userdata)

    def CreatePostSnapshot(self, config: str, pre_num: int,
                            description: str, cleanup: str, userdata: dict) -> int:
        return self._call('CreatePostSnapshot',
                          config, dbus.UInt32(pre_num),
                          description, cleanup, userdata)

    def DeleteSnapshots(self, config: str, ids: list):
        self._call('DeleteSnapshots', config,
                   dbus.Array([dbus.UInt32(i) for i in ids], signature='u'))

    def MountSnapshot(self, config: str, number: int, read_only: bool) -> str:
        return self._call('MountSnapshot', config,
                          dbus.UInt32(number), dbus.Boolean(read_only))

    def UmountSnapshot(self, config: str, number: int, read_only: bool):
        self._call('UmountSnapshot', config,
                   dbus.UInt32(number), dbus.Boolean(read_only))

    def GetMountPoint(self, config: str, number: int) -> str:
        return self._call('GetMountPoint', config, dbus.UInt32(number))

    def CreateConfig(self, name: str, subvolume: str,
                     fstype: str, template: str):
        self._call('CreateConfig', name, subvolume, fstype, template)

    def SetConfig(self, name: str, attrs: dict):
        self._call('SetConfig', name, attrs)

    def DeleteConfig(self, name: str):
        self._call('DeleteConfig', name)

    def GetConfig(self, name: str) -> dict:
        n, subvol, attrs = self._call('GetConfig', name)
        return {'name': n, 'subvolume': subvol, 'attrs': attrs}

    def CreateComparison(self, config: str, begin: int, end: int) -> int:
        return self._call('CreateComparison', config,
                          dbus.UInt32(begin), dbus.UInt32(end))

    def DeleteComparison(self, config: str, begin: int, end: int):
        self._call('DeleteComparison', config,
                   dbus.UInt32(begin), dbus.UInt32(end))

    def GetFiles(self, config: str, begin: int, end: int) -> list:
        """返回: [{'name': str, 'status': int}, ...]"""
        raw = self._call('GetFiles', config,
                         dbus.UInt32(begin), dbus.UInt32(end))
        return [{'name': path, 'status': status} for path, status in raw]

    # ──────────────────────────────────────────
    # 信号连接
    # ──────────────────────────────────────────

    def connect_to_signal(self, signal_name: str, handler):
        """
        连接 Snapper DBus 信号
        signal_name: 如 'SnapshotCreated', 'SnapshotDeleted', 'ConfigCreated' …
        handler: Python callable
        """
        return self._obj.connect_to_signal(
            signal_name,
            handler,
            dbus_interface='org.opensuse.Snapper'
        )


# ──────────────────────────────────────────────────────────────────
# 测试
# ──────────────────────────────────────────────────────────────────

def test_connection():
    print("Testing Snapper DBus connection...")
    snapper = SnapperInterface()

    configs = snapper.ListConfigs()
    print(f"Configs: {[c['name'] for c in configs]}")

    for cfg in configs:
        name = cfg['name']
        print(f"\n── Config: {name} ──")
        snapshots = snapper.ListSnapshots(name)
        for s in snapshots[:5]:   # 只打前 5 条
            print(f"  #{s['id']:>4}  {s['description']!r:30}  cleanup={s['cleanup']!r}")
        if len(snapshots) > 5:
            print(f"  ... ({len(snapshots)} total)")


if __name__ == '__main__':
    test_connection()

snapper = SnapperInterface()
