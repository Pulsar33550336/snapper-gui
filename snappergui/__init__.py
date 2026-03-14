from PySide6.QtDBus import QDBusInterface, QDBusConnection, QDBusMessage

class SnapperInterface:
    def __init__(self):
        self._bus = QDBusConnection.systemBus()
        self._interface = QDBusInterface(
            'org.opensuse.Snapper',
            '/org/opensuse/Snapper',
            'org.opensuse.Snapper',
            self._bus
        )

    def _call(self, method, *args):
        message = self._interface.call(method, *args)
        if message.type() == QDBusMessage.MessageType.ErrorMessage:
            # We should handle this better in a real app
            print(f"Error calling {method}: {message.errorMessage()}")
            return None

        args = message.arguments()
        if len(args) == 1:
            return args[0]
        return args

    def ListConfigs(self):
        return self._call('ListConfigs')

    def ListSnapshots(self, config):
        return self._call('ListSnapshots', config)

    def GetSnapshot(self, config, number):
        return self._call('GetSnapshot', config, number)

    def CreateSingleSnapshot(self, config, description, cleanup, userdata):
        return self._call('CreateSingleSnapshot', config, description, cleanup, userdata)

    def CreateConfig(self, name, subvolume, fstype, template):
        return self._call('CreateConfig', name, subvolume, fstype, template)

    def DeleteSnapshots(self, config, ids):
        return self._call('DeleteSnapshots', config, ids)

    def GetMountPoint(self, config, number):
        return self._call('GetMountPoint', config, number)

    def MountSnapshot(self, config, number, change_suffix):
        return self._call('MountSnapshot', config, number, change_suffix)

    def UmountSnapshot(self, config, number, change_suffix):
        return self._call('UmountSnapshot', config, number, change_suffix)

    def SetSnapshot(self, config, number, description, cleanup, userdata):
        return self._call('SetSnapshot', config, number, description, cleanup, userdata)

    def CreateComparison(self, config, begin, end):
        return self._call('CreateComparison', config, begin, end)

    def GetFiles(self, config, begin, end):
        return self._call('GetFiles', config, begin, end)

    def DeleteComparison(self, config, begin, end):
        return self._call('DeleteComparison', config, begin, end)

    def connect_to_signal(self, signal_name, receiver, slot):
        # QtDBus signal connection
        # slot should be bytes like b"onSignal(QString,int)"
        # We try catch here because if the service is not available, it might fail
        try:
            self._bus.connect(
                'org.opensuse.Snapper',
                '/org/opensuse/Snapper',
                'org.opensuse.Snapper',
                signal_name,
                receiver,
                slot
            )
        except Exception as e:
            print(f"Warning: Could not connect to DBus signal {signal_name}: {e}")

snapper = SnapperInterface()
