import subprocess
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QToolBar, QStatusBar, QTabWidget, QTreeView, 
                             QSplitter, QGroupBox, QLabel, QToolButton, 
                             QMenu, QSizePolicy)
from PySide6.QtGui import QAction, QIcon, QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Slot

from snappergui import snapper
from snappergui.createSnapshot import createSnapshot
from snappergui.createConfig import createConfig
from snappergui.deleteDialog import deleteDialog
from snappergui.changesWindow import changesWindow
from snappergui.snapshotsView import snapshotsView
from time import strftime, localtime
from pwd import getpwuid

class SnapperGUI(QMainWindow):
    def __init__(self, app):
        super(SnapperGUI, self).__init__()
        self.app = app
        self.setWindowTitle("SnapperGUI")
        self.resize(700, 600)
        self.setWindowIcon(QIcon.fromTheme("drive-harddisk"))

        self.setup_ui()
        self.init_dbus_signal_handlers()
        
        self.load_configs()

    def setup_ui(self):
        # Toolbar
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # New Snapshot / Config action
        self.new_menu = QMenu(self)
        self.action_create_snapshot = QAction(QIcon.fromTheme("gtk-add"), "Create Snapshot", self)
        self.action_create_snapshot.setToolTip("Create a new snapshot for the current configuration")
        self.action_create_snapshot.triggered.connect(self.on_create_snapshot)
        self.new_menu.addAction(self.action_create_snapshot)

        self.action_create_config = QAction("Create Configuration", self)
        self.action_create_config.triggered.connect(self.on_create_config)
        self.new_menu.addAction(self.action_create_config)

        self.btn_new = QToolButton()
        self.btn_new.setText("New")
        self.btn_new.setIcon(QIcon.fromTheme("gtk-add"))
        self.btn_new.setMenu(self.new_menu)
        self.btn_new.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn_new.setDefaultAction(self.action_create_snapshot)
        self.toolbar.addWidget(self.btn_new)

        # Open action
        self.action_open = QAction(QIcon.fromTheme("gtk-open"), "Open", self)
        self.action_open.setToolTip("Open snapshot mountpoint")
        self.action_open.triggered.connect(self.on_open_snapshot_folder)
        self.toolbar.addAction(self.action_open)

        # Delete action
        self.action_delete = QAction(QIcon.fromTheme("gtk-remove"), "Del", self)
        self.action_delete.setToolTip("Delete selected snapshots")
        self.action_delete.triggered.connect(self.on_delete_snapshot)
        self.toolbar.addAction(self.action_delete)

        # View Changes action
        self.action_changes = QAction(QIcon.fromTheme("gtk-file"), "Changes", self)
        self.action_changes.setToolTip("Show which files have changed between selected snapshots")
        self.action_changes.triggered.connect(self.on_viewchanges_clicked)
        self.toolbar.addAction(self.action_changes)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)

        # Tab widget for configs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_stack_visible_child_changed)
        self.splitter.addWidget(self.tabs)

        # Userdata section
        self.userdata_group = QGroupBox("Userdata")
        self.userdata_layout = QVBoxLayout(self.userdata_group)
        self.userdatatreeview = QTreeView()
        self.userdatatreeview.setHeaderHidden(True)
        self.userdata_model = QStandardItemModel(0, 2)
        self.userdatatreeview.setModel(self.userdata_model)
        self.userdata_layout.addWidget(self.userdatatreeview)
        self.splitter.addWidget(self.userdata_group)

        # Statusbar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.configView = {}
        self.update_controlls_and_userdatatreeview()

    def load_configs(self):
        """Load snapper configurations"""
        try:
            configs = snapper.ListConfigs()
            print(f"Configs loaded: {configs}")

            # 处理不同返回格式
            if not configs:
                return

            # 确保configs是列表
            if not isinstance(configs, list):
                configs = [configs]

            for config in configs:
                # 处理config可能是字符串、列表或元组的情况
                if isinstance(config, (list, tuple)):
                    # 如果是列表/元组，取第一个元素作为配置名
                    name = str(config[0]) if config else ""
                else:
                    # 如果是字符串，直接使用
                    name = str(config)

                if name:  # 确保配置名不为空
                    view = snapshotsView(name)
                    self.configView[name] = view
                    self.tabs.addTab(view, name)
                    view.selectionModel().selectionChanged.connect(
                        self.on_snapshots_selection_changed
                    )
        except Exception as e:
            print(f"Error loading configs: {e}")

    def get_current_config(self):
        """Get current selected configuration name"""
        current_index = self.tabs.currentIndex()
        if current_index >= 0:
            return self.tabs.tabText(current_index)
        return ""

    def on_stack_visible_child_changed(self, index):
        self.update_controlls_and_userdatatreeview()

    def on_snapshots_selection_changed(self, selected, deselected):
        self.update_controlls_and_userdatatreeview()

    def update_controlls_and_userdatatreeview(self):
        config = self.get_current_config()
        if not config or config not in self.configView:
            self.action_delete.setEnabled(False)
            self.action_open.setEnabled(False)
            self.action_changes.setEnabled(False)
            self.userdata_model.clear()
            return

        view = self.configView[config]
        selection = view.selectionModel()
        has_selection = selection.hasSelection()
        selected_rows = selection.selectedRows()

        self.action_delete.setEnabled(has_selection)
        self.action_open.setEnabled(has_selection)

        if len(selected_rows) > 1:
            self.action_changes.setEnabled(True)
        elif len(selected_rows) == 1:
            # Check if it's a pre snapshot with children
            index = selected_rows[0]
            if view.model().hasChildren(index):
                self.action_changes.setEnabled(True)
            else:
                self.action_changes.setEnabled(False)
        else:
            self.action_changes.setEnabled(False)

        # 更新userdata
        self.userdata_model.clear()
        if len(selected_rows) == 1:
            try:
                snapshot_id = view.model().data(selected_rows[0], Qt.UserRole)
                snapshot_data = snapper.GetSnapshot(config, snapshot_id)

                # 处理snapshot_data可能是不同格式的情况
                userdata = {}
                if isinstance(snapshot_data, (list, tuple)) and len(snapshot_data) > 7:
                    # 如果是列表/元组，第8个元素是userdata
                    userdata = snapshot_data[7] if len(snapshot_data) > 7 else {}
                elif isinstance(snapshot_data, dict):
                    # 如果是字典，直接取userdata字段
                    userdata = snapshot_data.get('userdata', {})

                # 显示userdata
                if isinstance(userdata, dict):
                    for key, value in userdata.items():
                        self.userdata_model.appendRow([
                            QStandardItem(str(key)),
                            QStandardItem(str(value))
                        ])
            except Exception as e:
                print(f"Error loading userdata: {e}")

    def on_create_snapshot(self):
        dialog = createSnapshot(self, self.get_current_config())
        if dialog.exec():
            snapper.CreateSingleSnapshot(dialog.config,
                                         dialog.description,
                                         dialog.cleanup,
                                         dialog.userdata)

    def on_create_config(self):
        dialog = createConfig(self)
        if dialog.exec():
            snapper.CreateConfig(dialog.name,
                                 dialog.subvolume,
                                 dialog.fstype,
                                 dialog.template)

    def on_delete_snapshot(self):
        config = self.get_current_config()
        view = self.configView[config]
        selected_rows = view.selectionModel().selectedRows()
        
        snapshots = []
        for index in selected_rows:
            snap_id = view.model().data(index, Qt.UserRole)
            if snap_id not in snapshots:
                snapshots.append(snap_id)
            # If has children (post snapshots), add them too
            if view.model().hasChildren(index):
                for i in range(view.model().rowCount(index)):
                    child_id = view.model().data(view.model().index(i, 0, index), Qt.UserRole)
                    if child_id not in snapshots:
                        snapshots.append(child_id)
        
        if snapshots:
            dialog = deleteDialog(self, config, snapshots)
            if dialog.exec() and dialog.to_delete:
                snapper.DeleteSnapshots(config, dialog.to_delete)

    def on_open_snapshot_folder(self):
        config = self.get_current_config()
        view = self.configView[config]
        selected_rows = view.selectionModel().selectedRows()
        for index in selected_rows:
            snap_id = view.model().data(index, Qt.UserRole)
            mountpoint = snapper.GetMountPoint(config, snap_id)
            # Check if mounted (index 6 in snapshot columns is cleanup, but let's check snapper)
            # In original code: if model[treeiter][6] != '':
            snapshot_data = snapper.GetSnapshot(config, snap_id)
            if snapshot_data[6] != '':
                 snapper.MountSnapshot(config, snap_id, 'true')
            
            subprocess.Popen(['xdg-open', mountpoint])
            self.statusbar.showMessage("The mount point for the snapshot %s from %s is %s" %
                                      (snap_id, config, mountpoint))

    def on_viewchanges_clicked(self):
        config = self.get_current_config()
        view = self.configView[config]
        selected_rows = view.selectionModel().selectedRows()
        
        if len(selected_rows) > 1:
            begin = view.model().data(selected_rows[0], Qt.UserRole)
            end = view.model().data(selected_rows[-1], Qt.UserRole)
            self.changes_win = changesWindow(config, begin, end)
            self.changes_win.show()
        elif len(selected_rows) == 1:
            index = selected_rows[0]
            if view.model().hasChildren(index):
                begin = view.model().data(index, Qt.UserRole)
                end = view.model().data(view.model().index(0, 0, index), Qt.UserRole)
                self.changes_win = changesWindow(config, begin, end)
                self.changes_win.show()

    def init_dbus_signal_handlers(self):
        """Initialize DBus signal connections"""
        # 暂时禁用信号连接直到DBus问题解决
        print("DBus signals temporarily disabled")
        return

        # 原来的代码注释掉
        """
        signals = {
            "SnapshotCreated": b"on_dbus_snapshot_created(QString,int)",
            "SnapshotModified": b"on_dbus_snapshot_modified(QString,int)",
            "SnapshotsDeleted": b"on_dbus_snapshots_deleted(QString,QList<int>)",
            "ConfigCreated": b"on_dbus_config_created(QString)",
            "ConfigModified": b"on_dbus_config_modified()",
            "ConfigDeleted": b"on_dbus_config_deleted()"
        }
        for sig, slot in signals.items():
            snapper.connect_to_signal(sig, self, slot)
        """

    @Slot(str, int)
    def on_dbus_snapshot_created(self, config, snapshot):
        self.statusbar.showMessage("Snapshot %s created for %s" % (str(snapshot), config))
        if config in self.configView:
            self.configView[config].add_snapshot_to_tree(snapshot)

    @Slot(str, int)
    def on_dbus_snapshot_modified(self, config, snapshot):
        print("Snapshot SnapshotModified")

    @Slot(str, list)
    def on_dbus_snapshots_deleted(self, config, snapshots):
        snaps_str = " ".join(map(str, snapshots))
        self.statusbar.showMessage("Snapshots deleted from %s: %s" % (config, snaps_str))
        if config in self.configView:
            for deleted in snapshots:
                self.configView[config].remove_snapshot_from_tree(deleted)

    @Slot(str)
    def on_dbus_config_created(self, config):
        view = snapshotsView(config)
        self.configView[config] = view
        self.tabs.addTab(view, config)
        view.selectionModel().selectionChanged.connect(self.on_snapshots_selection_changed)
        self.statusbar.showMessage("Created new configuration %s" % config, 5000)

    @Slot()
    def on_dbus_config_modified(self, *args):
        print("Config Modified")

    @Slot()
    def on_dbus_config_deleted(self, *args):
        print("Config Deleted")

    def closeEvent(self, event):
        for config_name, view in self.configView.items():
            # Original code iterates all snapshots and unmounts if cleanup != ''
            # We can try to replicate that if needed
            pass
        super().closeEvent(event)
