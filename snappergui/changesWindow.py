import os
import time
import difflib
import collections
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTreeView, QTextEdit, QStatusBar, QSplitter,
                             QLabel, QRadioButton, QButtonGroup)
from PySide6 import QtWidgets
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QFont
from PySide6.QtCore import Qt, QTimer

from snappergui import snapper

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

class DiffHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.fmt_add = QTextCharFormat()
        self.fmt_add.setForeground(QColor("#4ec94e"))
        self.fmt_add.setBackground(QColor("#1a3d1a"))

        self.fmt_del = QTextCharFormat()
        self.fmt_del.setForeground(QColor("#e06c6c"))
        self.fmt_del.setBackground(QColor("#3d1a1a"))

        self.fmt_hdr = QTextCharFormat()
        self.fmt_hdr.setForeground(QColor("#61afef"))

        self.fmt_meta = QTextCharFormat()
        self.fmt_meta.setForeground(QColor("#888888"))

    def highlightBlock(self, text):
        if text.startswith("+++ ") or text.startswith("--- "):
            self.setFormat(0, len(text), self.fmt_meta)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self.fmt_hdr)
        elif text.startswith("+"):
            self.setFormat(0, len(text), self.fmt_add)
        elif text.startswith("-"):
            self.setFormat(0, len(text), self.fmt_del)

class StatusFlags:
    CREATED     =   1
    DELETED     =   2
    TYPE        =   4
    CONTENT     =   8
    PERMISSIONS =  16
    OWNER       =  32
    GROUP       =  64
    XATTRS      = 128
    ACL         = 256

class changesWindow(QMainWindow):
    TreeNode = collections.namedtuple("TreeNode", "path, children, status, is_dir")

    def __init__(self, config, begin, end):
        super(changesWindow, self).__init__()
        self.setWindowTitle(f"Changes: {begin} -> {end}")
        self.resize(800, 600)

        self.config = config
        self.snapshot_begin = begin
        self.snapshot_end = end
        self.beginpath = snapper.GetMountPoint(config, begin)
        self.endpath = snapper.GetMountPoint(config, end)

        self.setup_ui()
        QTimer.singleShot(0, self.load_changes)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Title Label
        self.title_label = QLabel(f"{self.snapshot_begin} -> {self.snapshot_end}")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        self.main_layout.addWidget(self.title_label)

        # Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Left: Paths Tree
        self.pathstreeview = QTreeView()
        self.path_model = QStandardItemModel()
        self.path_model.setHorizontalHeaderLabels(["Name"])
        self.pathstreeview.setModel(self.path_model)
        self.pathstreeview.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.splitter.addWidget(self.pathstreeview)

        # Right: File View and controls
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)

        # View selection
        self.controls_layout = QHBoxLayout()
        self.btn_group = QButtonGroup(self)

        self.rb_begin = QRadioButton(str(self.snapshot_begin))
        self.rb_diff = QRadioButton("Diff")
        self.rb_end = QRadioButton(str(self.snapshot_end))
        self.rb_diff.setChecked(True)

        self.btn_group.addButton(self.rb_begin, 0)
        self.btn_group.addButton(self.rb_diff, 1)
        self.btn_group.addButton(self.rb_end, 2)

        self.controls_layout.addWidget(self.rb_begin)
        self.controls_layout.addWidget(self.rb_diff)
        self.controls_layout.addWidget(self.rb_end)
        self.btn_group.idClicked.connect(self.on_view_mode_changed)

        self.right_layout.addLayout(self.controls_layout)

        # Text View
        self.fileview = QTextEdit()
        self.fileview.setReadOnly(True)
        self.fileview.setFont(QFont("Monospace", 10))
        self.right_layout.addWidget(self.fileview)
        self.highlighter = DiffHighlighter(self.fileview.document())  # 加这行

        self.splitter.addWidget(self.right_widget)

        # Statusbar
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

    def load_changes(self):
        self.statusbar.showMessage("Loading changes...")
        snapper.CreateComparison(self.config, self.snapshot_begin, self.snapshot_end)
        dbus_array = snapper.GetFiles(self.config, self.snapshot_begin, self.snapshot_end)

        files_tree = changesWindow.TreeNode("/", {}, 0, True)
        for entry in dbus_array:
            print(entry)
            self.add_path_to_tree(str(entry['name']), int(entry['status']), files_tree)

        self.populate_path_model(files_tree)
        self.statusbar.showMessage(f"{len(dbus_array)} files changed.")
        snapper.DeleteComparison(self.config, self.snapshot_begin, self.snapshot_end)

    def add_path_to_tree(self, path, status, tree):
        is_dir = os.path.isdir(self.beginpath + path) or os.path.isdir(self.endpath + path)
        parts = path.lstrip('/').split('/')
        node = tree
        for part in parts[:-1]:
            if part not in node.children:
                node.children[part] = changesWindow.TreeNode("", {}, 0, True)
            existing = node.children[part]
            if existing.children is None:
                node.children[part] = changesWindow.TreeNode(existing.path, {}, existing.status, True)
            node = node.children[part]

        last_part = parts[-1]
        if is_dir:
            existing = node.children.get(last_part)
            existing_children = existing.children if existing and existing.children is not None else {}
            node.children[last_part] = changesWindow.TreeNode("", existing_children, status, True)
        else:
            node.children[last_part] = changesWindow.TreeNode(path, None, status, False)

    def populate_path_model(self, tree, parent_item=None):
        if parent_item is None:
            parent_item = self.path_model.invisibleRootItem()

        # Sort children: directories first, then alphabetically
        sorted_names = sorted(tree.children.keys(), key=lambda n: (not tree.children[n].is_dir, n))

        for name in sorted_names:
            child = tree.children[name]
            item = QStandardItem(name)
            item.setData(child.path, Qt.UserRole)
            item.setToolTip(self.file_status_to_string(child.status))

            # Color coding
            if child.status & StatusFlags.CREATED:
                item.setForeground(QColor(0, 145, 0)) # Green
            elif child.status & StatusFlags.DELETED:
                item.setForeground(QColor(153, 0, 0)) # Red
            elif child.status > 0:
                item.setForeground(QColor(125, 120, 0)) # Yellow-ish

            parent_item.appendRow(item)
            if child.is_dir and child.children:
                self.populate_path_model(child, item)

    def file_status_to_string(self, status):
        if status & StatusFlags.CREATED: return "Created"
        if status & StatusFlags.DELETED: return "Deleted"
        if status > 0:
            mods = []
            if status & StatusFlags.ACL: mods.append("acl")
            if status & StatusFlags.CONTENT: mods.append("content")
            if status & StatusFlags.GROUP: mods.append("group")
            if status & StatusFlags.OWNER: mods.append("owner")
            if status & StatusFlags.XATTRS: mods.append("xattrs")
            if status & StatusFlags.TYPE: mods.append("inode type")
            if status & StatusFlags.PERMISSIONS: mods.append("permissions")
            return "Modified: " + ", ".join(mods)
        return "No changes"

    def on_selection_changed(self, selected, deselected):
        self.update_file_view()

    def on_view_mode_changed(self, id):
        self.update_file_view()

    def update_file_view(self):
        selection = self.pathstreeview.selectionModel().selectedRows()
        if not selection:
            self.fileview.clear()
            return

        index = selection[0]
        rel_path = index.data(Qt.UserRole)
        if not rel_path:
            self.fileview.clear()
            return

        fromfile = self.beginpath + rel_path
        tofile = self.endpath + rel_path

        fromlines, from_binary = self.get_lines_from_file(fromfile)
        tolines, to_binary = self.get_lines_from_file(tofile)

        mode = self.btn_group.checkedId()

        if mode == 0:  # Begin
            self.highlighter.setDocument(None)
            if from_binary:
                self.fileview.setPlainText("[Binary file]")
            else:
                self.fileview.setPlainText("".join(fromlines) if fromlines else "")
        elif mode == 2:  # End
            self.highlighter.setDocument(None)
            if to_binary:
                self.fileview.setPlainText("[Binary file]")
            else:
                self.fileview.setPlainText("".join(tolines) if tolines else "")
        else:  # Diff
            if from_binary or to_binary:
                self.highlighter.setDocument(None)
                self.fileview.setPlainText("[Binary file]")
                return
            self.highlighter.setDocument(self.fileview.document())
            if fromlines is None: fromlines = []
            if tolines is None: tolines = []

            fromdate = time.ctime(os.stat(fromfile).st_mtime) if os.path.exists(fromfile) else ""
            todate = time.ctime(os.stat(tofile).st_mtime) if os.path.exists(tofile) else ""

            diff = difflib.unified_diff(
                fromlines, tolines,
                fromfile=fromfile, tofile=tofile,
                fromfiledate=fromdate, tofiledate=todate
            )
            self.fileview.setPlainText("".join(diff))

    def get_lines_from_file(self, path):
        try:
            with open(path, 'rb') as f:
                chunk = f.read(8192)
                if b'\x00' in chunk:  # 有 null 字节，认定为二进制
                    return None, True
            with open(path, 'r', errors='replace') as f:
                return f.readlines(), False
        except:
            return None, False