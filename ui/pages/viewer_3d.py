import pyqtgraph.opengl as gl
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QVector3D


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
        self.view.setCameraPosition(distance=100, elevation=30, azimuth=45)
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
        x = gl.GLLinePlotItem(pos=np.array([[0,0,0],[80,0,0]]), color=(1,0,0,0.6), width=2)
        y = gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,80,0]]), color=(0,1,0,0.6), width=2)
        z = gl.GLLinePlotItem(pos=np.array([[0,0,0],[0,0,80]]), color=(0,0,1,0.6), width=2)
        self.view.addItem(x)
        self.view.addItem(y)
        self.view.addItem(z)

    def add_grid(self):
        """X-Y平面浅色网格"""
        size = 100
        steps = 20
        color = (0.8, 0.8, 0.85, 0.3)
        lines = []
        for i in np.linspace(-size, size, steps+1):
            lines.append(np.array([[i, -size, 0], [i, size, 0]]))
            lines.append(np.array([[-size, i, 0], [size, i, 0]]))
        for line in lines:
            self.view.addItem(gl.GLLinePlotItem(pos=line, color=color, width=1))

    def update_scale_label(self):
        """地图式动态比例尺"""
        dist = self.view.opts['distance']
        scale = (10.0 * 100.0) / dist
        r = self.round_num(scale)
        self.scaleLabel.setText(f"  {r} μm  ")

    def round_num(self, v):
        if v < 1: return round(v,1)
        if v < 10: return round(v)
        if v < 50: return int(round(v/5)*5)
        return int(round(v/10)*10)

    def create_hollow_cylinder_mesh(self, r_inner, r_outer, length, rows=10, cols=30):
        """生成空心圆柱壳层的网格数据（兼容所有pyqtgraph版本）"""
        theta = np.linspace(0, 2 * np.pi, cols, endpoint=False)
        z = np.linspace(-length/2, length/2, rows)
        theta, z = np.meshgrid(theta, z)

        # 内外圆柱顶点
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)
        x_inner = r_inner * np.cos(theta)
        y_inner = r_inner * np.sin(theta)

        # 拼接所有顶点
        vertices = np.vstack([
            np.dstack([x_outer, y_outer, z]).reshape(-1, 3),
            np.dstack([x_inner, y_inner, z]).reshape(-1, 3)
        ])

        # 生成三角面
        faces = []
        num_vertices_per_cyl = rows * cols
        for i in range(rows-1):
            for j in range(cols):
                j_next = (j + 1) % cols
                # 外圆柱面
                faces.append([i*cols + j, i*cols + j_next, (i+1)*cols + j_next])
                faces.append([i*cols + j, (i+1)*cols + j_next, (i+1)*cols + j])
                # 内圆柱面
                offset = num_vertices_per_cyl
                faces.append([offset + i*cols + j, offset + (i+1)*cols + j_next, offset + i*cols + j_next])
                faces.append([offset + i*cols + j, offset + (i+1)*cols + j, offset + (i+1)*cols + j_next])
                # 上下端面
                if i == 0:
                    faces.append([j, offset + j, offset + j_next])
                    faces.append([j, offset + j_next, j_next])
                if i == rows-2:
                    faces.append([(i+1)*cols + j, (i+1)*cols + j_next, offset + (i+1)*cols + j_next])
                    faces.append([(i+1)*cols + j, offset + (i+1)*cols + j_next, offset + (i+1)*cols + j])

        # 🔥 修复：兼容旧版pyqtgraph API
        mesh = gl.MeshData()
        mesh.setVertexes(vertices)
        mesh.setFaces(np.array(faces))
        return mesh

    def update_tsv_model(self, params):
        """绘制完整TSV阵列（一整块硅衬底 + 网格状TSV）"""
        self.tsv_params = params
        # 只删除旧TSV模型，保留坐标轴和网格
        for item in self.view.items:
            if hasattr(item,'name') and 'tsv_' in item.name:
                self.view.removeItem(item)

        pitch = params["pitch"]
        # 绘制5×5的代表性阵列（展示网格规律，不会卡顿）
        array_size = 5
        positions = []
        for i in range(array_size):
            for j in range(array_size):
                x = (i - array_size/2 + 0.5) * pitch
                y = (j - array_size/2 + 0.5) * pitch
                positions.append((x, y))

        # 1. 绘制一整块大硅衬底（所有TSV都在里面）
        substrate_size = array_size * pitch + 10
        substrate = gl.GLBoxItem(
            size=QVector3D(substrate_size, substrate_size, params["substrate_thick"]),
            color=params["materials"]["硅 (Si)"]["color"]
        )
        substrate.translate(-substrate_size/2, -substrate_size/2, -params["substrate_thick"]/2)
        substrate.name = "tsv_substrate"
        self.view.addItem(substrate)

        # 2. 绘制每个TSV单元（都嵌入在大衬底里）
        for idx, (x, y) in enumerate(positions):
            self.draw_single_tsv(x, y, params, idx)

    def draw_single_tsv(self, x, y, p, idx):
        """绘制单个TSV（真实空心壳层结构 + 体积上色）"""
        mat = p["materials"]
        r = p["diameter"] / 2
        h_sub = p["substrate_thick"]
        h_pad = p["pad_thick"]
        pad_size = p["pad_size"]
        t_sio2 = p["sio2_liner"]
        t_tan = p["tan_barrier"]
        t_ta = p["ta_barrier"]

        # 1. 底部正方形Pad
        bottom_pad = gl.GLBoxItem(
            size=QVector3D(pad_size, pad_size, h_pad),
            color=mat["铜 (Cu)"]["color"]
        )
        bottom_pad.translate(x - pad_size/2, y - pad_size/2, -h_sub - h_pad/2)
        bottom_pad.name = f"tsv_{idx}_bottom_pad"
        self.view.addItem(bottom_pad)

        # 2. SiO₂介质隔离层（空心壳层，有真实厚度）
        sio2_r_outer = r + t_ta + t_tan + t_sio2
        sio2_r_inner = r + t_ta + t_tan
        sio2_mesh = self.create_hollow_cylinder_mesh(sio2_r_inner, sio2_r_outer, h_sub)
        sio2_item = gl.GLMeshItem(
            meshdata=sio2_mesh,
            color=(0.95, 0.95, 1.0, 0.6),  # 半透明，能看到内部
            shader='shaded', smooth=True
        )
        sio2_item.translate(x, y, -h_sub/2)
        sio2_item.name = f"tsv_{idx}_sio2"
        self.view.addItem(sio2_item)

        # 3. TaN扩散阻挡层（空心壳层）
        tan_r_outer = r + t_ta + t_tan
        tan_r_inner = r + t_ta
        tan_mesh = self.create_hollow_cylinder_mesh(tan_r_inner, tan_r_outer, h_sub)
        tan_item = gl.GLMeshItem(
            meshdata=tan_mesh,
            color=(0.5, 0.5, 0.5, 0.8),
            shader='shaded', smooth=True
        )
        tan_item.translate(x, y, -h_sub/2)
        tan_item.name = f"tsv_{idx}_tan"
        self.view.addItem(tan_item)

        # 4. Ta扩散阻挡层（空心壳层）
        ta_r_outer = r + t_ta
        ta_r_inner = r
        ta_mesh = self.create_hollow_cylinder_mesh(ta_r_inner, ta_r_outer, h_sub)
        ta_item = gl.GLMeshItem(
            meshdata=ta_mesh,
            color=(0.6, 0.6, 0.6, 0.8),
            shader='shaded', smooth=True
        )
        ta_item.translate(x, y, -h_sub/2)
        ta_item.name = f"tsv_{idx}_ta"
        self.view.addItem(ta_item)

        # 5. TSV铜柱（实心核心）
        cu_cyl = gl.MeshData.cylinder(rows=10, cols=30, radius=[r, r], length=h_sub)
        cu_item = gl.GLMeshItem(
            meshdata=cu_cyl,
            color=mat["铜 (Cu)"]["color"],
            shader='shaded', smooth=True
        )
        cu_item.translate(x, y, -h_sub/2)
        cu_item.name = f"tsv_{idx}_cu"
        self.view.addItem(cu_item)

        # 6. 顶部正方形Pad
        top_pad = gl.GLBoxItem(
            size=QVector3D(pad_size, pad_size, h_pad),
            color=mat["铜 (Cu)"]["color"]
        )
        top_pad.translate(x - pad_size/2, y - pad_size/2, h_pad/2)
        top_pad.name = f"tsv_{idx}_top_pad"
        self.view.addItem(top_pad)

        # 7. 低K介质层（包裹顶部Pad）
        lowk_size = pad_size + 2
        lowk_box = gl.GLBoxItem(
            size=QVector3D(lowk_size, lowk_size, h_pad),
            color=(0.8, 0.9, 0.8, 0.6)  # 半透明
        )
        lowk_box.translate(x - lowk_size/2, y - lowk_size/2, h_pad/2)
        lowk_box.name = f"tsv_{idx}_lowk"
        self.view.addItem(lowk_box)