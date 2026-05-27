import pyqtgraph.opengl as gl
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor


class TSV3DViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.tsv_params = None
        self.add_coords()
        self.add_grid()

        # 定时器更新比例尺
        self.scale_timer = QTimer()
        self.scale_timer.timeout.connect(self.update_scale_label)
        self.scale_timer.start(100)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view = gl.GLViewWidget()
        self.view.setBackgroundColor(QColor(245, 245, 245))
        self.view.setCameraPosition(distance=80, elevation=30, azimuth=45)
        layout.addWidget(self.view, stretch=1)

        # 左下角动态比例尺
        self.scaleLabel = QLabel()
        self.scaleLabel.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #999;
                padding: 3px 6px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.scaleLabel, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

    def add_coords(self):
        """半透明XYZ坐标轴"""
        x = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [60, 0, 0]]), color=(1, 0, 0, 0.6), width=2)
        y = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 60, 0]]), color=(0, 1, 0, 0.6), width=2)
        z = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 0, 60]]), color=(0, 0, 1, 0.6), width=2)
        self.view.addItem(x)
        self.view.addItem(y)
        self.view.addItem(z)

    def add_grid(self):
        """X-Y平面浅色网格"""
        size = 80
        steps = 16
        color = (0.8, 0.8, 0.85, 0.3)
        lines = []
        for i in np.linspace(-size, size, steps + 1):
            lines.append(np.array([[i, -size, 0], [i, size, 0]]))
            lines.append(np.array([[-size, i, 0], [size, i, 0]]))
        for line in lines:
            self.view.addItem(gl.GLLinePlotItem(pos=line, color=color, width=1))

    def update_scale_label(self):
        """地图式动态比例尺"""
        dist = self.view.opts['distance']
        scale = (10.0 * 80.0) / dist
        r = self.round_num(scale)
        self.scaleLabel.setText(f"  {r} μm  ")

    def round_num(self, v):
        if v < 1: return round(v, 1)
        if v < 10: return round(v)
        if v < 50: return int(round(v / 5) * 5)
        return int(round(v / 10) * 10)

    def update_tsv_model(self, params):
        """按文档分层绘制真实TSV结构"""
        self.tsv_params = params
        # 只删除旧TSV模型，保留坐标轴和网格
        for item in self.view.items:
            if hasattr(item, 'name') and 'tsv_' in item.name:
                self.view.removeItem(item)

        pitch = params["pitch"]
        positions = self.get_positions(pitch)

        # 绘制每个TSV单元
        for idx, (x, y) in enumerate(positions):
            self.draw_single_tsv(x, y, params, idx)

    def draw_single_tsv(self, x, y, p, idx):
        """绘制单个完整TSV结构（从下往上）"""
        mat = p["materials"]
        r = p["diameter"] / 2
        h_sub = p["substrate_thick"]
        h_pad = p["pad_thick"]
        t_sio2 = p["sio2_liner"]
        t_tan = p["tan_barrier"]
        t_ta = p["ta_barrier"]

        # 1. 硅衬底（最底层，整个平面）
        if idx == 0:  # 只画一次衬底
            substrate = gl.MeshData.cylinder(
                rows=10, cols=40, radius=[60, 60], length=h_sub
            )
            sub_item = gl.GLMeshItem(
                meshdata=substrate,
                color=mat["硅 (Si)"]["color"],
                shader='shaded', smooth=True
            )
            sub_item.translate(0, 0, -h_sub / 2)
            sub_item.name = "tsv_substrate"
            self.view.addItem(sub_item)

        # 2. 底部Pad（衬底下方）
        pad_r = p["pad_size"] / 2
        bottom_pad = gl.MeshData.cylinder(
            rows=5, cols=20, radius=[pad_r, pad_r], length=h_pad
        )
        bp_item = gl.GLMeshItem(
            meshdata=bottom_pad,
            color=mat["铜 (Cu)"]["color"],
            shader='shaded', smooth=True
        )
        bp_item.translate(x, y, -h_sub - h_pad / 2)
        bp_item.name = f"tsv_{idx}_bottom_pad"
        self.view.addItem(bp_item)

        # 3. SiO₂介质隔离层（包裹TSV孔）
        sio2_r = r + t_sio2 + t_tan + t_ta
        sio2_cyl = gl.MeshData.cylinder(
            rows=10, cols=30, radius=[sio2_r, sio2_r], length=h_sub
        )
        sio2_item = gl.GLMeshItem(
            meshdata=sio2_cyl,
            color=mat["二氧化硅 (SiO₂)"]["color"],
            shader='shaded', smooth=True
        )
        sio2_item.translate(x, y, -h_sub / 2)
        sio2_item.name = f"tsv_{idx}_sio2"
        self.view.addItem(sio2_item)

        # 4. TaN扩散阻挡层
        tan_r = r + t_tan + t_ta
        tan_cyl = gl.MeshData.cylinder(
            rows=10, cols=30, radius=[tan_r, tan_r], length=h_sub
        )
        tan_item = gl.GLMeshItem(
            meshdata=tan_cyl,
            color=mat["氮化钽 (TaN)"]["color"],
            shader='shaded', smooth=True
        )
        tan_item.translate(x, y, -h_sub / 2)
        tan_item.name = f"tsv_{idx}_tan"
        self.view.addItem(tan_item)

        # 5. Ta扩散阻挡层
        ta_r = r + t_ta
        ta_cyl = gl.MeshData.cylinder(
            rows=10, cols=30, radius=[ta_r, ta_r], length=h_sub
        )
        ta_item = gl.GLMeshItem(
            meshdata=ta_cyl,
            color=mat["钽 (Ta)"]["color"],
            shader='shaded', smooth=True
        )
        ta_item.translate(x, y, -h_sub / 2)
        ta_item.name = f"tsv_{idx}_ta"
        self.view.addItem(ta_item)

        # 6. TSV铜柱（核心填充）
        cu_cyl = gl.MeshData.cylinder(
            rows=10, cols=30, radius=[r, r], length=h_sub
        )
        cu_item = gl.GLMeshItem(
            meshdata=cu_cyl,
            color=mat["铜 (Cu)"]["color"],
            shader='shaded', smooth=True
        )
        cu_item.translate(x, y, -h_sub / 2)
        cu_item.name = f"tsv_{idx}_cu"
        self.view.addItem(cu_item)

        # 7. 顶部Pad（衬底上方）
        top_pad = gl.MeshData.cylinder(
            rows=5, cols=20, radius=[pad_r, pad_r], length=h_pad
        )
        tp_item = gl.GLMeshItem(
            meshdata=top_pad,
            color=mat["铜 (Cu)"]["color"],
            shader='shaded', smooth=True
        )
        tp_item.translate(x, y, h_pad / 2)
        tp_item.name = f"tsv_{idx}_top_pad"
        self.view.addItem(tp_item)

        # 8. 低K介质层（包裹顶部Pad）
        lowk_r = pad_r + 1
        lowk_cyl = gl.MeshData.cylinder(
            rows=5, cols=20, radius=[lowk_r, lowk_r], length=h_pad
        )
        lowk_item = gl.GLMeshItem(
            meshdata=lowk_cyl,
            color=mat["低K介质层"]["color"],
            shader='shaded', smooth=True
        )
        lowk_item.translate(x, y, h_pad / 2)
        lowk_item.name = f"tsv_{idx}_lowk"
        self.view.addItem(lowk_item)

    def get_positions(self, pitch):
        mode = self.tsv_params["arrangement"] if self.tsv_params else "单个"
        if mode == "单个":
            return [[0, 0]]
        elif mode == "正方形":
            return [
                [-pitch / 2, -pitch / 2],
                [pitch / 2, -pitch / 2],
                [pitch / 2, pitch / 2],
                [-pitch / 2, pitch / 2]
            ]
        elif mode == "六边形":
            a = np.linspace(0, np.pi * 2, 6, endpoint=False)
            return [[pitch * np.cos(x), pitch * np.sin(x)] for x in a]
        return [[0, 0]]