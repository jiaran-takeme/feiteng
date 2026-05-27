from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout
)
from ui.pages.param_page import ParamPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSV热应力仿真软件")
        self.setGeometry(100, 100, 1000, 700)

        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        # 添加参数页
        self.param_page = ParamPage()
        self.stacked.addWidget(self.param_page)