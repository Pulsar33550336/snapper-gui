import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: qsTr("SnapperGUI (QML)")

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            ToolButton {
                text: qsTr("Create Snapshot")
                icon.name: "document-new"
                onClicked: createSnapshotDialog.open()
            }
            ToolButton {
                text: qsTr("Delete")
                icon.name: "edit-delete"
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

            selectionModel: ItemSelectionModel {
                model: snapper.snapshots
            }

            delegate: Rectangle {
                implicitHeight: 30
                implicitWidth: 100
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

    Dialog {
        id: createSnapshotDialog
        title: qsTr("Create Snapshot")
        standardButtons: Dialog.Ok | Dialog.Cancel
        ColumnLayout {
            TextField { id: descField; placeholderText: qsTr("Description") }
            TextField { id: cleanupField; placeholderText: qsTr("Cleanup (number/timeline/empty)") }
        }
        onAccepted: {
            snapper.createSnapshot(snapper.currentConfig, descField.text, cleanupField.text, {})
            descField.text = ""
            cleanupField.text = ""
        }
    }
}
