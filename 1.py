#!/usr/bin/env python3
# test_qml_translation_fixed.py
import sys
import os
from PySide6.QtCore import QTranslator, QLocale, QCoreApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

# 设置中文环境
os.environ['LANG'] = 'zh_CN.UTF-8'
os.environ['LC_ALL'] = 'zh_CN.UTF-8'

print("=" * 60)
print("开始测试 QML 翻译")
print("=" * 60)

# 创建应用
app = QApplication(sys.argv)

# 获取系统区域设置
locale = QLocale.system()
print(f"系统区域设置: {locale.name()}")

# 加载翻译
translator = QTranslator()
i18n_path = os.path.join(os.path.dirname(__file__), "snappergui", "i18n")
qm_file = os.path.join(i18n_path, "zh_CN.qm")

print(f"翻译文件: {qm_file}")
print(f"文件存在: {os.path.exists(qm_file)}")

if translator.load(qm_file):
    app.installTranslator(translator)
    print("✅ 翻译加载成功")

    # 测试 C++ 侧翻译
    test_text = app.translate("main", "Create Snapshot")
    print(f"  C++ 测试 (main): 'Create Snapshot' -> '{test_text}'")

    # 测试其他上下文
    for ctx in ["SnapperGUI", "snapshotsView", "changesWindow"]:
        t = app.translate(ctx, "Create Snapshot")
        if t != "Create Snapshot":
            print(f"  C++ 测试 ({ctx}): 'Create Snapshot' -> '{t}'")
else:
    print("❌ 翻译加载失败")
    sys.exit(1)

# 创建 QML 引擎
engine = QQmlApplicationEngine()

# 连接警告信号
def on_warning(warnings):
    for warning in warnings:
        print(f"⚠️ QML 警告: {warning.toString()}")
engine.warnings.connect(on_warning)

# 创建一个简单的 QML 组件来测试翻译
qml_code = '''
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 500
    height: 400
    title: qsTr("翻译测试窗口")

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 15

        Label {
            text: "直接测试:"
            font.bold: true
        }

        Label {
            text: "Create Snapshot → " + qsTr("Create Snapshot")
            color: qsTr("Create Snapshot") == "Create Snapshot" ? "red" : "green"
        }
        Label {
            text: "Delete → " + qsTr("Delete")
            color: qsTr("Delete") == "Delete" ? "red" : "green"
        }
        Label {
            text: "Properties → " + qsTr("Properties")
            color: qsTr("Properties") == "Properties" ? "red" : "green"
        }
        Label {
            text: "Userdata → " + qsTr("Userdata")
            color: qsTr("Userdata") == "Userdata" ? "red" : "green"
        }

        Rectangle {
            height: 2
            color: "gray"
            Layout.fillWidth: true
        }

        Label {
            text: "按钮测试:"
            font.bold: true
        }

        Button {
            text: qsTr("Create Snapshot")
            Layout.fillWidth: true
            onClicked: console.log("按钮点击")
        }

        Label {
            text: "系统语言: " + Qt.locale().name
            color: "blue"
            Layout.topMargin: 20
        }
    }

    Component.onCompleted: {
        console.log("=" * 40)
        console.log("QML 测试结果:")
        console.log("  Create Snapshot ->", qsTr("Create Snapshot"))
        console.log("  Delete ->", qsTr("Delete"))
        console.log("  Properties ->", qsTr("Properties"))
        console.log("=" * 40)
    }
}
'''

print("\n加载 QML 代码...")
component = engine.loadData(qml_code.encode('utf-8'))

if not engine.rootObjects():
    print("❌ 无法加载 QML")
    sys.exit(1)

print("✅ QML 加载成功")

# 调试信息
print("\n" + "=" * 60)
print("调试信息:")
print("=" * 60)

# 1. 检查翻译器是否安装
print(f"已安装翻译器数量: {len(app.translators())}")

# 2. 检查 QML 导入路径
print("\nQML 导入路径:")
for path in engine.importPathList():
    print(f"  {path}")

# 3. 尝试直接测试每个上下文的翻译
print("\n测试所有上下文的翻译:")
contexts = ["main", "SnapperGUI", "snapshotsView", "changesWindow",
            "createSnapshot", "createConfig", "deleteDialog", "propertiesDialog"]
for ctx in contexts:
    t1 = app.translate(ctx, "Create Snapshot")
    t2 = app.translate(ctx, "Delete")
    if t1 != "Create Snapshot" or t2 != "Delete":
        print(f"✅ 上下文 '{ctx}': 有翻译")
        if t1 != "Create Snapshot":
            print(f"   'Create Snapshot' -> '{t1}'")
        if t2 != "Delete":
            print(f"   'Delete' -> '{t2}'")

# 4. 检查翻译文件内容
print("\n翻译文件内容统计:")
from xml.etree import ElementTree
try:
    ts_file = os.path.join(os.path.dirname(__file__), "snappergui", "i18n", "zh_CN.ts")
    if os.path.exists(ts_file):
        tree = ElementTree.parse(ts_file)
        root = tree.getroot()
        contexts = root.findall(".//context")
        total_msgs = 0
        for ctx in contexts:
            name = ctx.find("name").text
            msgs = ctx.findall("message")
            total_msgs += len(msgs)
            print(f"  上下文 '{name}': {len(msgs)} 条翻译")
        print(f"  总计: {total_msgs} 条翻译")
except Exception as e:
    print(f"  无法读取 ts 文件: {e}")

print("\n" + "=" * 60)
print("观察窗口中的文本:")
print("- 红色文本表示未翻译")
print("- 绿色文本表示已翻译")
print("=" * 60)

# 运行应用
sys.exit(app.exec())