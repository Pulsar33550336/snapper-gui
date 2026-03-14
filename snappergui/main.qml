import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: "SnapperGUI (QML)"

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton {
                text: "Create Snapshot"
                icon.name: "list-add"
                onClicked: createSnapshotDialog.open()
            }
            ToolButton {
                text: "Delete"
                icon.name: "list-remove"
                enabled: snapshotView.currentRow >= 0
                onClicked: {
                    var id = snapper.snapshots.data(snapper.snapshots.index(snapshotView.currentRow, 0), 257) // IDRole
                    snapper.deleteSnapshots(snapper.currentConfig, [id])
                }
            }
            Item { Layout.fillWidth: true }
            ComboBox {
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

            delegate: Rectangle {
                implicitHeight: 30
                color: snapshotView.currentRow === row ? "lightblue" : "white"
                Text {
                    anchors.centerIn: parent
                    text: {
                        if (column === 0) return model.snapshotId
                        if (column === 1) return model.snapshotType
                        if (column === 2) return model.snapshotPreId
                        if (column === 3) return model.snapshotDate
                        if (column === 4) return model.snapshotUser
                        if (column === 5) return model.snapshotDescription
                        if (column === 6) return model.snapshotCleanup
                        return ""
                    }
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
            Text { text: "Userdata"; font.bold: true }
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: snapshotView.currentRow >= 0 ? snapper.snapshots.getUserdata(snapshotView.currentRow) : []
                delegate: RowLayout {
                    Text { text: modelData.key + ":"; font.bold: true }
                    Text { text: modelData.value }
                }
            }
        }
    }

    Dialog {
        id: createSnapshotDialog
        title: "Create Snapshot"
        standardButtons: Dialog.Ok | Dialog.Cancel
        ColumnLayout {
            TextField { id: descField; placeholderText: "Description" }
            TextField { id: cleanupField; placeholderText: "Cleanup (number/timeline/empty)" }
        }
        onAccepted: {
            snapper.createSnapshot(snapper.currentConfig, descField.text, cleanupField.text, {})
            descField.text = ""
            cleanupField.text = ""
        }
    }
}
