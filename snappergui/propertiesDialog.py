from snappergui import snapper
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QSpinBox, QCheckBox, QTabWidget,
                             QScrollArea, QWidget, QGridLayout, QGroupBox,
                             QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

class PropertiesTab(QWidget):
    def __init__(self, config_data):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        
        self.widgets = {}
        settings = config_data[2]
        
        row = 0
        # Basic Settings
        self.add_setting("SUBVOLUME", self.tr("Subvolume"), settings.get("SUBVOLUME", ""), row, 0)
        self.add_setting("FSTYPE", self.tr("Filesystem"), settings.get("FSTYPE", ""), row, 2)
        row += 1
        self.add_setting("ALLOW_USERS", self.tr("Users"), settings.get("ALLOW_USERS", ""), row, 0)
        self.add_setting("ALLOW_GROUPS", self.tr("Groups"), settings.get("ALLOW_GROUPS", ""), row, 2)
        row += 1
        self.add_bool_setting("TIMELINE_CREATE", self.tr("Timeline Create"), settings.get("TIMELINE_CREATE", "no"), row, 0)
        row += 1
        
        # Timeline Group
        timeline_group = QGroupBox(self.tr("Timeline Cleanup"))
        timeline_grid = QGridLayout(timeline_group)
        self.add_bool_setting("TIMELINE_CLEANUP", self.tr("Enabled"), settings.get("TIMELINE_CLEANUP", "no"), 0, 0, timeline_grid)
        self.add_setting("TIMELINE_LIMIT_HOURLY", self.tr("Hourly"), settings.get("TIMELINE_LIMIT_HOURLY", "10"), 1, 0, timeline_grid)
        self.add_setting("TIMELINE_LIMIT_DAILY", self.tr("Daily"), settings.get("TIMELINE_LIMIT_DAILY", "10"), 1, 2, timeline_grid)
        self.add_setting("TIMELINE_LIMIT_WEEKLY", self.tr("Weekly"), settings.get("TIMELINE_LIMIT_WEEKLY", "0"), 2, 0, timeline_grid)
        self.add_setting("TIMELINE_LIMIT_MONTHLY", self.tr("Monthly"), settings.get("TIMELINE_LIMIT_MONTHLY", "10"), 2, 2, timeline_grid)
        self.add_setting("TIMELINE_LIMIT_YEARLY", self.tr("Yearly"), settings.get("TIMELINE_LIMIT_YEARLY", "10"), 3, 0, timeline_grid)
        self.add_spin_setting("TIMELINE_MIN_AGE", self.tr("Min. Age"), settings.get("TIMELINE_MIN_AGE", "0"), 3, 2, timeline_grid)
        self.grid.addWidget(timeline_group, row, 0, 1, 4)
        row += 1
        
        # Number Group
        number_group = QGroupBox(self.tr("Number Cleanup"))
        number_grid = QGridLayout(number_group)
        self.add_bool_setting("NUMBER_CLEANUP", self.tr("Enabled"), settings.get("NUMBER_CLEANUP", "no"), 0, 0, number_grid)
        self.add_setting("NUMBER_LIMIT", self.tr("Limit"), settings.get("NUMBER_LIMIT", "50"), 1, 0, number_grid)
        self.add_setting("NUMBER_LIMIT_IMPORTANT", self.tr("Limit Impor."), settings.get("NUMBER_LIMIT_IMPORTANT", "10"), 1, 2, number_grid)
        self.add_spin_setting("NUMBER_MIN_AGE", self.tr("Min. Age"), settings.get("NUMBER_MIN_AGE", "0"), 2, 0, number_grid)
        self.grid.addWidget(number_group, row, 0, 1, 4)
        row += 1
        
        # Empty Pre/Post Group
        empty_group = QGroupBox(self.tr("Empty Pre/Post Cleanup"))
        empty_grid = QGridLayout(empty_group)
        self.add_bool_setting("EMPTY_PRE_POST_CLEANUP", self.tr("Enabled"), settings.get("EMPTY_PRE_POST_CLEANUP", "no"), 0, 0, empty_grid)
        self.add_spin_setting("EMPTY_PRE_POST_MIN_AGE", self.tr("Min. Age"), settings.get("EMPTY_PRE_POST_MIN_AGE", "0"), 1, 0, empty_grid)
        self.grid.addWidget(empty_group, row, 0, 1, 4)
        row += 1
        
        # Misc
        self.add_bool_setting("BACKGROUND_COMPARISON", self.tr("Backg. Comparison"), settings.get("BACKGROUND_COMPARISON", "no"), row, 0)
        self.add_bool_setting("SYNC_ACL", self.tr("Sync Acl"), settings.get("SYNC_ACL", "no"), row, 2)
        
        self.scroll.setWidget(self.content)
        self.layout.addWidget(self.scroll)

    def add_setting(self, key, label, value, r, c, grid=None):
        if grid is None: grid = self.grid
        grid.addWidget(QLabel(label), r, c)
        w = QLineEdit(str(value))
        grid.addWidget(w, r, c+1)
        self.widgets[key] = w

    def add_bool_setting(self, key, label, value, r, c, grid=None):
        if grid is None: grid = self.grid
        w = QCheckBox(label)
        w.setChecked(value == "yes")
        grid.addWidget(w, r, c, 1, 2)
        self.widgets[key] = w

    def add_spin_setting(self, key, label, value, r, c, grid=None):
        if grid is None: grid = self.grid
        grid.addWidget(QLabel(label), r, c)
        w = QSpinBox()
        w.setRange(0, 5000)
        try: w.setValue(int(value))
        except: pass
        grid.addWidget(w, r, c+1)
        self.widgets[key] = w

    def get_current_value(self, key):
        w = self.widgets[key]
        if isinstance(w, QLineEdit): return w.text()
        if isinstance(w, QCheckBox): return "yes" if w.isChecked() else "no"
        if isinstance(w, QSpinBox): return str(w.value())
        return ""

class propertiesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Configurations properties"))
        self.resize(600, 500)
        self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        self.tab_widgets = {}
        configs = snapper.ListConfigs()
        for config in configs:
            name = str(config[0])
            tab = PropertiesTab(config)
            self.tabs.addTab(tab, name)
            self.tab_widgets[name] = tab
            
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.on_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_changed_settings(self, config_name):
        changed = {}
        current_config = None
        for c in snapper.ListConfigs():
            if str(c[0]) == config_name:
                current_config = c
                break
        
        if not current_config: return changed
        
        tab = self.tab_widgets[config_name]
        for k, v in current_config[2].items():
            if k in tab.widgets:
                current_val = tab.get_current_value(k)
                if current_val != v:
                    changed[k] = current_val
        return changed

    def on_accept(self):
        config_name = self.tabs.tabText(self.tabs.currentIndex())
        changed = self.get_changed_settings(config_name)
        if changed:
            try:
                snapper.SetConfig(config_name, changed)
                self.accept()
            except Exception as e:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Could not edit configuration: %1").replace("%1", str(e)))
        else:
            self.accept()
