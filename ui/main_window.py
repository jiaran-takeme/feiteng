from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QSplitter
)
from PyQt6.QtCore import Qt
from ui.pages.param_page import ParamPage
from ui.pages.viewer_3d import TSV3DViewer
from ui.components.log_widget import LogWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSV热应力仿真软件")
        self.setGeometry(100, 100, 1200, 800)

        # 日志组件
        self.log_widget = LogWidget()

        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 主窗口边距清空
        main_layout.setSpacing(0)

        # 顶部左右分割器
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        top_splitter.setStyleSheet("QSplitter::handle { background-color: #ccc; }")
        main_layout.addWidget(top_splitter, stretch=8)

        # 左侧参数面板
        self.param_page = ParamPage(self)
        top_splitter.addWidget(self.param_page)

        # 右侧3D预览（强制占满右侧）
        self.viewer_3d = TSV3DViewer()
        top_splitter.addWidget(self.viewer_3d)

        # 强制分割器1:1比例（窗口缩放时保持比例）
        top_splitter.setSizes([600, 600])
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 1)

        # 底部日志
        main_layout.addWidget(self.log_widget, stretch=2)

        # 绑定信号
        self.param_page.param_changed.connect(self.viewer_3d.update_tsv_model)
        self.log_widget.append_log("系统启动成功 ✅")

    def log_message(self, msg):
        self.log_widget.append_log(msg)