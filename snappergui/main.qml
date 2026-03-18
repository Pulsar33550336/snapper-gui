import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 1000
    height: 700
    title: qsTr("SnapperGUI (QML)")

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton {
                text: qsTr("Create Snapshot")
                icon.name: "list-add"
                onClicked: createSnapshotDialog.open()
            }
            ToolButton {
                text: qsTr("Open Folder")
                icon.name: "folder-open"
                enabled: snapshotView.currentRow >= 0
                onClicked: {
                    var id = snapper.snapshots.getSnapshotId(snapshotView.currentRow)
                    snapper.openSnapshotFolder(snapper.currentConfig, id)
                }
            }
            ToolButton {
                text: qsTr("Delete")
                icon.name: "list-remove"
                enabled: snapshotView.currentRow >= 0
                onClicked: deleteConfirmDialog.open()
            }
            ToolButton {
                text: qsTr("Changes")
                icon.name: "text-x-generic"
                enabled: snapshotView.currentRow >= 0
                onClicked: {
                    if (snapshotView.currentRow > 0) {
                        var endId = snapper.snapshots.getSnapshotId(snapshotView.currentRow)
                        var beginId = snapper.snapshots.getSnapshotId(snapshotView.currentRow - 1)
                        changesWindow.open(snapper.currentConfig, beginId, endId)
                    }
                }
            }
            ToolButton {
                text: qsTr("Properties")
                icon.name: "document-properties"
                onClicked: propertiesDialog.open()
            }
            ToolButton {
                text: qsTr("New Config")
                icon.name: "gtk-add"
                onClicked: createConfigDialog.open()
            }
            Item { Layout.fillWidth: true }
            ComboBox {
                id: configCombo
                model: snapper.configs
                onCurrentTextChanged: snapper.currentConfig = currentText
                Component.onCompleted: snapper.currentConfig = currentText
            }
        }
    }

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        TableView {
            id: snapshotView
            SplitView.fillHeight: true
            SplitView.preferredHeight: 400
            clip: true
            columnSpacing: 1
            rowSpacing: 1
            model: snapper.snapshots
            selectionModel: ItemSelectionModel {
                model: snapper.snapshots
            }

            delegate: Rectangle {
                implicitHeight: 30
                implicitWidth: (column === 5) ? 300 : (column === 3 ? 150 : 100)
                color: snapshotView.currentRow === row ? "lightblue" : "white"
                border.color: "#eee"
                Text {
                    anchors.centerIn: parent
                    text: display
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: snapshotView.currentRow = row
                }
            }

            property int currentRow: -1
        }

        ColumnLayout {
            SplitView.preferredHeight: 200
            Text {
                text: qsTr("Userdata")
                font.bold: true
                Layout.leftMargin: 10
                Layout.topMargin: 5
            }
            ListView {
                id: userdataList
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.leftMargin: 10
                model: snapshotView.currentRow >= 0 ? snapper.snapshots.getUserdata(snapshotView.currentRow) : []
                delegate: RowLayout {
                    Text { text: modelData.key + ":"; font.bold: true }
                    Text { text: modelData.value }
                }
            }
        }
    }

    footer: StatusBar {
        RowLayout {
            Label {
                id: statusLabel
                text: qsTr("Ready")
            }
        }
    }

    Connections {
        target: snapper
        function onMessage(msg) {
            statusLabel.text = msg
        }
    }

    Dialog {
        id: createSnapshotDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        title: qsTr("Create Snapshot")
        standardButtons: Dialog.Ok | Dialog.Cancel
        ColumnLayout {
            TextField { id: descField; placeholderText: qsTr("Description"); Layout.fillWidth: true }
            TextField { id: cleanupField; placeholderText: qsTr("Cleanup (number/timeline/empty)"); Layout.fillWidth: true }
        }
        onAccepted: {
            snapper.createSnapshot(snapper.currentConfig, descField.text, cleanupField.text, {})
            descField.text = ""
            cleanupField.text = ""
        }
    }

    Dialog {
        id: createConfigDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        title: qsTr("Create Configuration")
        standardButtons: Dialog.Ok | Dialog.Cancel
        GridLayout {
            columns: 2
            Label { text: qsTr("Name:") }
            TextField { id: cfgName; Layout.fillWidth: true }
            Label { text: qsTr("Subvolume (path):") }
            TextField { id: cfgSubvol; Layout.fillWidth: true }
            Label { text: qsTr("Filesystem Type:") }
            ComboBox { id: cfgFs; model: ["btrfs", "ext4", "lvm"] }
            Label { text: qsTr("Template:") }
            TextField { id: cfgTpl; text: "default"; Layout.fillWidth: true }
        }
        onAccepted: snapper.createConfig(cfgName.text, cfgSubvol.text, cfgFs.currentText, cfgTpl.text)
    }

    Dialog {
        id: deleteConfirmDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        title: qsTr("Delete Snapshot")
        standardButtons: Dialog.Yes | Dialog.No
        Text {
            text: qsTr("Are you sure you want to delete the selected snapshot?")
        }
        onAccepted: {
            var id = snapper.snapshots.getSnapshotId(snapshotView.currentRow)
            snapper.deleteSnapshots(snapper.currentConfig, [id])
        }
    }

    Dialog {
        id: propertiesDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 600
        height: 500
        title: qsTr("Configuration Properties: ") + snapper.currentConfig
        standardButtons: Dialog.Ok | Dialog.Cancel

        property var configAttrs: ({})

        onAboutToShow: {
            var data = snapper.getConfig(snapper.currentConfig)
            configAttrs = data.attrs || {}
        }

        ScrollView {
            anchors.fill: parent
            ColumnLayout {
                spacing: 10
                width: parent.width - 20
                Layout.margins: 10

                GroupBox {
                    title: qsTr("Basic Settings")
                    Layout.fillWidth: true
                    GridLayout {
                        columns: 2
                        anchors.fill: parent
                        Label { text: "SUBVOLUME" }
                        TextField { text: propertiesDialog.configAttrs["SUBVOLUME"] || ""; onTextChanged: propertiesDialog.configAttrs["SUBVOLUME"] = text; Layout.fillWidth: true }
                        Label { text: "FSTYPE" }
                        TextField { text: propertiesDialog.configAttrs["FSTYPE"] || ""; onTextChanged: propertiesDialog.configAttrs["FSTYPE"] = text; Layout.fillWidth: true }
                        Label { text: "ALLOW_USERS" }
                        TextField { text: propertiesDialog.configAttrs["ALLOW_USERS"] || ""; onTextChanged: propertiesDialog.configAttrs["ALLOW_USERS"] = text; Layout.fillWidth: true }
                        Label { text: "ALLOW_GROUPS" }
                        TextField { text: propertiesDialog.configAttrs["ALLOW_GROUPS"] || ""; onTextChanged: propertiesDialog.configAttrs["ALLOW_GROUPS"] = text; Layout.fillWidth: true }
                    }
                }

                GroupBox {
                    title: qsTr("Timeline Cleanup")
                    Layout.fillWidth: true
                    GridLayout {
                        columns: 4
                        anchors.fill: parent
                        Label { text: "Enabled" }
                        CheckBox { checked: propertiesDialog.configAttrs["TIMELINE_CLEANUP"] === "yes"; onToggled: propertiesDialog.configAttrs["TIMELINE_CLEANUP"] = checked ? "yes" : "no" }
                        Label { text: "Hourly" }
                        TextField { text: propertiesDialog.configAttrs["TIMELINE_LIMIT_HOURLY"] || ""; onTextChanged: propertiesDialog.configAttrs["TIMELINE_LIMIT_HOURLY"] = text }
                        Label { text: "Daily" }
                        TextField { text: propertiesDialog.configAttrs["TIMELINE_LIMIT_DAILY"] || ""; onTextChanged: propertiesDialog.configAttrs["TIMELINE_LIMIT_DAILY"] = text }
                        Label { text: "Weekly" }
                        TextField { text: propertiesDialog.configAttrs["TIMELINE_LIMIT_WEEKLY"] || ""; onTextChanged: propertiesDialog.configAttrs["TIMELINE_LIMIT_WEEKLY"] = text }
                    }
                }
            }
        }
        onAccepted: snapper.setConfig(snapper.currentConfig, configAttrs)
    }

    Window {
        id: changesWindow
        transientParent: root
        title: qsTr("Changes Viewer")
        width: 800
        height: 600
        visible: false

        property string config: ""
        property int begin: -1
        property int end: -1
        property string selectedPath: ""

        function open(cfg, b, e) {
            config = cfg
            begin = b
            end = e
            title = qsTr("Changes: %1 -> %2").arg(b).arg(e)
            snapper.comparison.compare(cfg, b, e)
            visible = true
        }

        SplitView {
            anchors.fill: parent
            orientation: Qt.Horizontal
            ListView {
                id: fileList
                SplitView.preferredWidth: 200
                model: snapper.comparison
                clip: true
                delegate: ItemDelegate {
                    width: parent.width
                    text: model.path
                    onClicked: changesWindow.selectedPath = model.path
                    highlighted: changesWindow.selectedPath === model.path
                }
            }
            ColumnLayout {
                RowLayout {
                    RadioButton { id: rbBegin; text: qsTr("Begin"); checked: false }
                    RadioButton { id: rbDiff; text: qsTr("Diff"); checked: true }
                    RadioButton { id: rbEnd; text: qsTr("End"); checked: false }
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    TextArea {
                        id: diffArea
                        readOnly: true
                        font.family: "Monospace"
                        text: {
                            var mode = rbBegin.checked ? 0 : (rbEnd.checked ? 2 : 1)
                            if (changesWindow.selectedPath === "") return ""
                            return snapper.getDiff(changesWindow.config, changesWindow.begin, changesWindow.end, mode, changesWindow.selectedPath)
                        }
                    }
                }
            }
        }
    }
}
