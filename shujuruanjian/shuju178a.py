import os
import lcm
import lcmtypes
import matplotlib
import threading
import time
import sys
import numpy as np
import struct

matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus']=False
class AppForm(QMainWindow):
    slidervaluechange = pyqtSignal()    # pyqt5信号发射器
    global d
    d = False
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('数据处理与分析')
        self.create_menu()
        self.create_main_frame()
        self.textbox.setText(' ')
        self.textbox2.setText(' ')
        self.number_E = 0   # 计数器
        self.number_c = 0  # 计数器
        self.event_msg = []

    def save_plot(self):
        file_choices = "PNG (*.png)|*.png"

        path = QFileDialog.getSaveFileName(self,
                                           '保存', '',
                                           file_choices)
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)

    def on_about(self):
        msg = """ 本软件基于PYTHON的PyQt5和matplotlib库：

         * 点击“读文件”按钮读取lcm文件，选择所需数据以图像形式展现在坐标轴上，其中大部分数据为其与时间的关系图像，部分例外（如经纬度图像）。
         * 图像呈现功能由matplotlib完成。
         * 生成每个数据的图像可随意组合、放大或缩小，图像可以保存（视频除外）。
         * 已实现车道线回放，ESR数据回放，视觉目标回放，及视频回放等功能。
         * 点击“车道线回放”按钮可以看到车辆识别出的车道线图像，拖动右下角滑块条可以查看各个时间点车辆所识别出的车道线图像。
         * 其中车道线回放和视觉目标回放可以与视频同步回放，点击“车道线回放”或“视觉目标回放”按钮，然后加载视频文件，再点击“视频回放”按钮，即可观看视频。
         * 观看视频时拖动滑块条可跳转播放位置。打开视频后，视频自动播放，按下“暂停”按钮后可暂停，点击“开始”按钮继续播放。
         * 特别注意，退出前请务必点击“停止播放”按钮，以确保关闭时能完全关闭软件的所有线程。
         * 如发现问题请联系我们。
        """
        QMessageBox.about(self, "关于本软件", msg.strip())

    def on_pick(self, event):
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points

        QMessageBox.information(self, "Click!", msg)

    def clear(self):
        self.ax.clear()
        self.canvas.draw()

    def get_peaks(self, x, y, n, x0=None, x1=None):
        if x0 is None:
            x0 = x[0]
        if x1 is None:
            x1 = x[-1]
        index0 = np.searchsorted(x, x0)
        index1 = np.searchsorted(x, x1, side="right")
        step = (index1 - index0) // n
        if step == 0:
            step = 1
        index1 += 2 * step
        if index0 < 0:
            index0 = 0
        if index1 > len(x) - 1:
            index1 = len(x) - 1
        x = x[index0:index1 + 1]
        y = y[index0:index1 + 1]
        y = y[:len(y) // step * step]
        yy = y.reshape(-1, step)
        index = np.c_[np.argmin(yy, axis=1), np.argmax(yy, axis=1)]
        index.sort(axis=1)
        index += np.arange(0, len(y), step).reshape(-1, 1)
        index = index.reshape(-1)
        return x[index], y[index]

    def create_main_frame(self):
        self.main_frame = QWidget()

        self.dpi = 100
        self.fig = plt.figure(None, (4.5, 3.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.fig1 = plt.figure(None, (8.0, 4.8), dpi=self.dpi)
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.main_frame)
        self.fig2 = plt.figure(None, (4.5, 3.0), dpi=self.dpi)
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setParent(self.main_frame)
        self.label_2 = QLabel(self)
        self.label_2.setMinimumSize(QtCore.QSize(640, 500))
        self.label_2.setMaximumSize(QtCore.QSize(650, 600))
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_2.setPixmap(QtGui.QPixmap('0.jpg'))
        self.label_2.setAutoFillBackground(True)  # 设置背景充满，为设置背景颜色的必要条件
        pe = QPalette()
        pe.setColor(QPalette.Window, Qt.black)
        self.label_2.setPalette(pe)
        self.label_4 = QLabel(self)
        self.label_4.setMaximumSize(QtCore.QSize(650, 25))
        self.label1 = QLabel(self)
        self.label1.setMaximumSize(QtCore.QSize(450, 1))
        self.label2 = QLabel(self)
        self.label2.setMaximumSize(QtCore.QSize(450, 1))

        self.fileButton = QPushButton("读文件")
        self.fileButton.setMaximumWidth(200)
        self.fileLineEdit = QLineEdit()
        self.fileButton.clicked.connect(lambda: self.read_log(self.fileLineEdit.text()))
        self.textbox = QLineEdit()
        self.textbox.setMaximumWidth(200)
        self.textbox2 = QLineEdit()
        self.textbox2.setMaximumWidth(140)

        self.ax = self.fig.add_subplot(111)
        self.plt1 = self.fig1.add_subplot(111)
        self.ax1 = self.fig2.add_subplot(111)

        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.mpl_toolbar.setMaximumWidth(450)
        self.mpl_toolbar1 = NavigationToolbar(self.canvas1, self.main_frame)
        self.mpl_toolbar2 = NavigationToolbar(self.canvas2, self.main_frame)
        self.mpl_toolbar2.setMaximumWidth(450)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(600)
        self.slider_label = QLabel('时间戳编号：')
        self.slider_label.setMaximumWidth(100)
        self.reviewEdit1 = QTextEdit()
        self.reviewEdit1.setMaximumSize(QtCore.QSize(420,190))
        self.reviewEdit2 = QTextEdit()
        self.reviewEdit2.setMaximumSize(QtCore.QSize(420, 190))
        self.slidervaluechange.connect(self.sliderValuechange)
        self.pbar = QProgressBar(self)
        self.pbar.setMaximumWidth(200)
        self.pbar.setValue(0)

        self.tab1 = QScrollArea()
        self.tab1.setWidget(QWidget())
        background_color = QColor()
        background_color.setNamedColor('#E6E6FA')
        self.tab1.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Window, background_color)
        self.tab1.setPalette(palette)
        self.tab1.setAlignment(Qt.AlignCenter)
        self.tab1.setMaximumSize(QtCore.QSize(200,500))
        self.tab1.setMinimumSize(QtCore.QSize(200, 400))
        self.tab1.setWidgetResizable(True)
        self.text_browser_1 = QPushButton("目标速度")
        self.text_browser_2 = QPushButton("驾驶模式")
        self.text_browser_3 = QPushButton("达到目标速度时间")
        self.text_browser_4 = QPushButton("决策方向盘转角")
        self.text_browser_5 = QPushButton("决策方向盘转速")
        self.text_browser_6 = QPushButton("驾驶模式开关状态")
        self.text_browser_7 = QPushButton("方向盘转角")
        self.text_browser_8 = QPushButton("方向盘转速")
        self.text_browser_9 = QPushButton("转向灯")
        self.text_browser_10 = QPushButton("左轮速度")
        self.text_browser_11 = QPushButton("右轮速度")
        self.text_browser_12 = QPushButton("电压")
        self.text_browser_13 = QPushButton("挡位")
        self.text_browser_14 = QPushButton("左轮距离")
        self.text_browser_15 = QPushButton("右轮距离")
        # self.text_browser_18 = QPushButton("加速度")
        self.text_browser_19 = QPushButton("车速")
        self.text_browser_20 = QPushButton("航向角")
        self.text_browser_21 = QPushButton("翻滚角")
        self.text_browser_22 = QPushButton("俯仰角")
        self.text_browser_23 = QPushButton("横摆角速度GPS")
        self.text_browser_24 = QPushButton("北向车速")
        self.text_browser_25 = QPushButton("东向车速")
        self.text_browser_26 = QPushButton("垂直地面速度")
        self.text_browser_27 = QPushButton("定位模式")
        self.text_browser_28 = QPushButton("可信度")
        self.text_browser_29 = QPushButton("卫星数量")
        self.text_browser_30 = QPushButton("经纬度")
        self.text_browser_31 = QPushButton("换道状态")
        self.text_browser_33 = QPushButton("左车道线")
        self.text_browser_34 = QPushButton("右车道线")
        self.text_browser_36 = QPushButton("左车道线长度")
        self.text_browser_37 = QPushButton("右车道线长度")
        self.text_browser_39 = QPushButton("车道宽度")
        self.text_browser_40 = QPushButton("目标个数")
        self.text_browser_42 = QPushButton("目标的ID")
        self.text_browser_43 = QPushButton("目标类别")
        self.text_browser_44 = QPushButton("刹车状态")
        self.text_browser_45 = QPushButton("转向灯状态")
        self.text_browser_46 = QPushButton("纵向相对运动速度")
        self.text_browser_47 = QPushButton("横向相对运动速度")
        self.text_browser_48 = QPushButton("车头朝向")
        self.text_browser_49 = QPushButton("目标可信度")
        self.text_browser_50 = QPushButton("目标宽度")
        self.text_browser_51 = QPushButton("目标高度")
        self.text_browser_52 = QPushButton("目标长度")
        self.Button32 = QPushButton("清除图像")
        self.Button32.setMaximumWidth(200)
        self.Button54 = QPushButton("定位当前时间戳编号")
        self.Button54.setMaximumWidth(200)
        self.Button55 = QPushButton("视频回放")
        self.Button55.setMaximumWidth(202)
        self.Button56 = QPushButton("暂停")
        self.Button56.setMaximumWidth(202)
        self.Button57 = QPushButton("继续")
        self.Button57.setMaximumWidth(202)
        self.Button58 = QPushButton("停止播放")
        self.Button58.setMaximumWidth(202)
        self.Button59 = QPushButton("前进一步")
        self.Button59.setMaximumWidth(160)
        self.Button60 = QPushButton("后退一步")
        self.Button60.setMaximumWidth(160)
        self.Button61 = QPushButton("开始播放")
        self.Button61.setMaximumWidth(160)
        self.Button62 = QPushButton("前进")
        self.Button62.setMaximumWidth(160)
        self.Button63 = QPushButton("后退")
        self.Button63.setMaximumWidth(160)
        self.Button64 = QPushButton("更新图像")
        self.Button64.setMaximumWidth(200)
        self.Button65 = QPushButton("精确到当前时间")
        self.Button65.setMaximumWidth(200)

        self.text_browser_1.clicked.connect(self.SPEED_CMD_aim_spe)
        self.text_browser_2.clicked.connect(self.SPEED_CMD_mode)
        self.text_browser_3.clicked.connect(self.SPEED_CMD_t)
        self.text_browser_4.clicked.connect(self.STEER_CMD_steer_pos)
        self.text_browser_5.clicked.connect(self.STEER_CMD_steer_spe)
        self.text_browser_6.clicked.connect(self.VEHICLE_STATUS_nauto)
        self.text_browser_7.clicked.connect(self.VEHICLE_STATUS_steerPos)
        self.text_browser_8.clicked.connect(self.VEHICLE_STATUS_steerSpe)
        self.text_browser_9.clicked.connect(self.VEHICLE_STATUS_light)
        self.text_browser_10.clicked.connect(self.VEHICLE_STATUS_speLeft)
        self.text_browser_11.clicked.connect(self.VEHICLE_STATUS_speRight)
        self.text_browser_12.clicked.connect(self.VEHICLE_STATUS_vot)
        self.text_browser_13.clicked.connect(self.VEHICLE_STATUS_shift)
        self.text_browser_14.clicked.connect(self.VEHICLE_STATUS_disLeft)
        self.text_browser_15.clicked.connect(self.VEHICLE_STATUS_disRight)
        # self.text_browser_18.clicked.connect(self.VEHICLE_STATUS_accelerationLat)
        self.text_browser_19.clicked.connect(self.GPS_DATA_velocity)
        self.text_browser_20.clicked.connect(self.GPS_DATA_yaw)
        self.text_browser_21.clicked.connect(self.GPS_DATA_roll)
        self.text_browser_22.clicked.connect(self.GPS_DATA_pitch)
        self.text_browser_23.clicked.connect(self.GPS_DATA_yawRate)
        self.text_browser_24.clicked.connect(self.GPS_DATA_velocityNorth)
        self.text_browser_25.clicked.connect(self.GPS_DATA_velocityEast)
        self.text_browser_26.clicked.connect(self.GPS_DATA_velocityDown)
        self.text_browser_27.clicked.connect(self.GPS_DATA_locationStatus)
        self.text_browser_28.clicked.connect(self.GPS_DATA_confidenceLevel)
        self.text_browser_29.clicked.connect(self.GPS_DATA_satelliteNumber)
        self.text_browser_30.clicked.connect(self.GPS_DATA_longittude_latitude)
        self.text_browser_31.clicked.connect(self.camera_change_lane)
        self.text_browser_33.clicked.connect(self.camera_left_lane)
        self.text_browser_34.clicked.connect(self.camera_right_lane)
        self.text_browser_36.clicked.connect(self.camera_left_line_length)
        self.text_browser_37.clicked.connect(self.camera_right_line_length)
        self.text_browser_39.clicked.connect(self.camera_lane_width)
        self.text_browser_40.clicked.connect(self.camera_object_count)
        self.text_browser_42.clicked.connect(self.camera_object_id)
        self.text_browser_43.clicked.connect(self.camera_object_type)
        self.text_browser_44.clicked.connect(self.camera_object_brake)
        self.text_browser_45.clicked.connect(self.camera_object_turn)
        self.text_browser_46.clicked.connect(self.camera_object_speedLon)
        self.text_browser_47.clicked.connect(self.camera_object_speedLat)
        self.text_browser_48.clicked.connect(self.camera_object_angle)
        self.text_browser_49.clicked.connect(self.camera_object_confidence)
        self.text_browser_50.clicked.connect(self.camera_object_width)
        self.text_browser_51.clicked.connect(self.camera_object_height)
        self.text_browser_52.clicked.connect(self.camera_object_length)
        self.Button32.clicked.connect(self.clear)
        self.Button54.clicked.connect(self.point)
        self.Button55.clicked.connect(self.show_image)
        self.Button56.clicked.connect(self.pause)
        self.Button57.clicked.connect(self.resume)
        self.Button58.clicked.connect(self.stope_image)
        self.Button59.clicked.connect(self.one_step_up)
        self.Button60.clicked.connect(self.one_step_donw)
        self.Button61.clicked.connect(self.show_image_n)
        self.Button62.clicked.connect(self.step_up)
        self.Button63.clicked.connect(self.step_donw)
        self.Button64.clicked.connect(self.update_pltdata)
        self.Button65.clicked.connect(self.ax_point)

        v1box = QVBoxLayout()
        v1box.addWidget(self.label1)
        v1box.addWidget(self.mpl_toolbar)
        v1box.addWidget(self.canvas)
        v2box = QVBoxLayout()
        v2box.addWidget(self.label2)
        v2box.addWidget(self.mpl_toolbar2)
        v2box.addWidget(self.canvas2)

        hbox2 = QHBoxLayout()
        hbox2.addLayout(v1box)
        hbox2.addLayout(v2box)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(hbox2)
        vbox1.addWidget(self.mpl_toolbar1)
        vbox1.addWidget(self.canvas1)

        h1box = QHBoxLayout()
        h1box.addWidget(self.slider_label)
        h1box.addWidget(self.textbox2)

        self.tab1.setWidget(QWidget())
        vbox = QVBoxLayout(self.tab1.widget())
        self.tab1.setWidgetResizable(True)
        for w in [ self.text_browser_1, self.text_browser_2, self.text_browser_3, self.text_browser_4,
                   self.text_browser_5, self.text_browser_6, self.text_browser_7, self.text_browser_8,
                   self.text_browser_9, self.text_browser_10, self.text_browser_11, self.text_browser_12,
                   self.text_browser_13, self.text_browser_14, self.text_browser_15, #self.text_browser_18,
                   self.text_browser_19, self.text_browser_20, self.text_browser_21, self.text_browser_22,
                   self.text_browser_23, self.text_browser_24, self.text_browser_25, self.text_browser_26,
                   self.text_browser_27, self.text_browser_28, self.text_browser_29, self.text_browser_30,
                   self.text_browser_31, self.text_browser_33, self.text_browser_34, self.text_browser_36,
                   self.text_browser_37, self.text_browser_39, self.text_browser_40, self.text_browser_42,
                   self.text_browser_43, self.text_browser_44, self.text_browser_45, self.text_browser_46,
                   self.text_browser_47, self.text_browser_48, self.text_browser_49, self.text_browser_50,
                   self.text_browser_51, self.text_browser_52]:
            vbox.addWidget(w)
            vbox.setAlignment(w, Qt.AlignVCenter)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.tab1)
        vbox2.addWidget(self.fileButton)
        vbox2.addWidget(self.Button64)
        vbox2.addWidget(self.Button65)
        vbox2.addWidget(self.Button32)
        vbox2.addWidget(self.textbox)
        vbox2.addWidget(self.Button54)
        vbox2.addWidget(self.pbar)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.Button55)
        hbox3.addWidget(self.Button56)
        hbox3.addWidget(self.Button57)
        hbox3.addWidget(self.Button58)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.slider)
        hbox4.addLayout(h1box)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.Button61)
        hbox5.addWidget(self.Button63)
        hbox5.addWidget(self.Button60)
        hbox5.addWidget(self.Button59)
        hbox5.addWidget(self.Button62)
        
        hbox6 = QHBoxLayout()
        hbox6.addWidget(self.reviewEdit1)
        hbox6.addWidget(self.reviewEdit2)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.label_2)
        hbox1.addLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.addLayout(hbox1)
        vbox3.addWidget(self.label_4)
        vbox3.addLayout(hbox4)
        vbox3.addLayout(hbox3)
        vbox3.addLayout(hbox5)
        vbox3.addLayout(hbox6)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox3)

        self.main_frame.setLayout(hbox)
        self.setGeometry(50, 40, 1800, 980)
        self.setCentralWidget(self.main_frame)

        def SPEED_CMD_aim_spe(self):
        self.ax1.clear()
        f = open('speed_cmd.txt', 'r')
        aim_speed = []
        time = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    aim_speed.append(float(a[1]))
                    time.append(float(a[0]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(aim_speed)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0],n[1], color='r', label='目标车速', marker='.')
        self.line_1, = self.ax1.plot(n[0], n[1], color='r', label='目标车速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax.legend(loc='best')
        self.ax1.legend(loc='best')
        self.canvas.draw()
        self.canvas2.draw()

    def SPEED_CMD_mode(self):
        self.ax1.clear()
        f = open('speed_cmd.txt', 'r')
        mode = []
        time = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    mode.append(float(a[2]))
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(mode)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='k', label='驾驶模式', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='k', label='驾驶模式', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def SPEED_CMD_t(self):
        self.ax1.clear()
        f = open('speed_cmd.txt', 'r')
        time = []
        t = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    t.append(float(a[3]))
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(t)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='g', label='达到目标速度时间', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='g', label='达到目标速度时间', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def STEER_CMD_steer_pos(self):
        self.ax1.clear()
        f = open('steer_cmd.txt', 'r')
        time = []
        steer_pos = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 3:
                    steer_pos.append(float(a[1]))
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(steer_pos)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='m', label='决策方向盘转角', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='m', label='决策方向盘转角', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def STEER_CMD_steer_spe(self):
        self.ax1.clear()
        f = open('steer_cmd.txt', 'r')
        time = []
        steer_spe = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 3:
                    steer_spe.append(float(a[2]))
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(steer_spe)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='tan', label='决策方向盘转速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='tan', label='决策方向盘转速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_nauto(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        mode = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    mode.append(int(a[1]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(mode)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='b', label='驾驶模式开关状态', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='b', label='驾驶模式开关状态', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_steerPos(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        steerPos = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    steerPos.append(float(a[2]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(steerPos)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='yellow', label='方向盘转角', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='yellow', label='方向盘转角', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_steerSpe(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        steerspe = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    steerspe.append(float(a[3]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(steerspe)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='darkviolet', label='方向盘转速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='darkviolet', label='方向盘转速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_light(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        light = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    light.append(float(a[4]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(light)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='aqua', label='转向灯', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='aqua', label='转向灯', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_speLeft(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        speed = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    speed.append(float(a[5]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(speed)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='y', label='左轮速度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='y', label='左轮速度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_speRight(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        speed = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    speed.append(float(a[6]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(speed)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='c', label='右轮速度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='c', label='右轮速度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_vot(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        vot = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    vot.append(float(a[7]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(vot)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='brown', label='电压', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='brown', label='电压', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_shift(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        shift = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    shift.append(float(a[8]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(shift)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='lime', label='挡位', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='lime', label='挡位', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_disLeft(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        dis = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    dis.append(float(a[9]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(dis)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='gold', label='左轮距离', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='gold', label='左轮距离', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def VEHICLE_STATUS_disRight(self):
        self.ax1.clear()
        f = open('vehicle_status.txt', 'r')
        time = []
        dis = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 11:
                    time.append(float(a[0]))
                    dis.append(float(a[10]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(dis)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='orange', label='右轮距离', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='orange', label='右轮距离', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    # def VEHICLE_STATUS_accelerationLat(self):
    #     self.ax1.clear()
    #     f = open('gps_data.txt', 'r')
    #     time = []
    #     accelerationLat = []
    #     self.x_k = []
    #     self.y_k = []
    #     done = 0
    #     while not done:
    #         line = f.readline()
    #         line = line.strip('\n')
    #         if line != '':
    #             a = line.split(' ')
    #             if len(a) == 15:
    #                 time.append(float(a[0]))
    #                 accelerationLat.append(float(a[14]))
    #
    #         else:
    #             done = 1
    #     f.close
    #     self.x = np.array(time)
    #     self.y = np.array(accelerationLat)
    #     n = self.get_peaks(self.x, self.y, 500)
    #     self.line, = self.ax.plot(n[0], n[1], color='pink', label='加速度', marker='.')
    #     self.ax.legend(loc='best')
    #     self.canvas.draw()
    #     self.line_1, = self.ax1.plot(n[0], n[1], color='pink', label='加速度', marker='.')
    #     self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
    #     self.ax1.legend(loc='best')
    #     self.canvas2.draw()

    def GPS_DATA_velocity(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        velocity = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    velocity.append(float(a[10]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(velocity)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='violet', label='车速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='violet', label='车速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_yaw(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        yaw = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    yaw.append(float(a[3]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(yaw)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='plum', label='航向角', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='plum', label='航向角', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_roll(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        roll = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    roll.append(float(a[4]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(roll)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='purple', label='翻滚角', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='purple', label='翻滚角', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_pitch(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        pitch = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    pitch.append(float(a[5]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(pitch)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='indigo', label='俯仰角', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='indigo', label='俯仰角', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_yawRate(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        yawRate = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    yawRate.append(float(a[6]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(yawRate)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='navy', label='横摆角速度GPS', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='navy', label='横摆角速度GPS', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_velocityNorth(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        velocityNorth = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    velocityNorth.append(float(a[7]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(velocityNorth)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='teal', label='北向车速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='teal', label='北向车速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_velocityEast(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        velocityEast = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    velocityEast.append(float(a[8]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(velocityEast)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='gray', label='东向车速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='gray', label='东向车速', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_velocityDown(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        velocityDown = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    velocityDown.append(float(a[9]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(velocityDown)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='darkred', label='垂直地面速度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='darkred', label='垂直地面速度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_locationStatus(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        locationStatus = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    locationStatus.append(float(a[11]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(locationStatus)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='tomato', label='定位模式', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='tomato', label='定位模式', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_confidenceLevel(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        confidenceLevel = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    confidenceLevel.append(float(a[12]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(confidenceLevel)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='sienna', label='可信度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='sienna', label='可信度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_satelliteNumber(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        time = []
        satelliteNumber = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                    satelliteNumber.append(float(a[13]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(satelliteNumber)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='khaki', label='卫星数量', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='khaki', label='卫星数量', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def GPS_DATA_longittude_latitude(self):
        self.ax1.clear()
        f = open('gps_data.txt', 'r')
        latitude = []
        longittude = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    latitude.append(float(a[2]))
                    longittude.append(float(a[1]))

            else:
                done = 1
        f.close
        self.x = np.array(latitude)
        self.y = np.array(longittude)
        # n = self.get_peaks(self.y, self.x, 500)
        self.line, = self.ax.plot(self.y, self.x, color='seagreen', label='经纬度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        # self.line_1, = self.ax1.plot(n[0], n[1], color='seagreen', label='经纬度', marker='.')
        # self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        # self.ax1.legend(loc='best')
        # self.canvas2.draw()

    def camera_change_lane(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        change_lane = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    change_lane.append(float(a[3]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(change_lane)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='deepskyblue', label='换道状态', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='deepskyblue', label='换道状态', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_left_lane(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        left_lane = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    left_lane.append(float(a[0]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(left_lane)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='crimson', label='左车道线', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='crimson', label='左车道线', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_right_lane(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        right_lane = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    right_lane.append(float(a[1]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(right_lane)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='orchid', label='右车道线', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='orchid', label='右车道线', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_left_line_length(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        left_lane_length = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    left_lane_length.append(float(a[4]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(left_lane_length)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='dodgerblue', label='左车道线长度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='dodgerblue', label='左车道线长度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_right_line_length(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        right_lane_length = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    right_lane_length.append(float(a[5]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(right_lane_length)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='thistle', label='右车道线长度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='thistle', label='右车道线长度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_lane_width(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        lane_width = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    lane_width.append(float(a[6]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(lane_width)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='mediumspringgreen', label='车道宽度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='mediumspringgreen', label='车道宽度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_count(self):
        self.ax1.clear()
        f = open('camera_line_msg.txt', 'r')
        time = []
        object_count = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 8:
                    time.append(float(a[2]))
                    object_count.append(float(a[7]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_count)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='mediumslateblue', label='目标个数', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='mediumslateblue', label='目标个数', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_id(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_id = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_id.append(float(a[1]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_id)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='maroon', label='目标的ID', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='maroon', label='目标的ID', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_type(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_type = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_type.append(float(a[2]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_type)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='sienna', label='目标类别', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='sienna', label='目标类别', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_brake(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_brake = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_brake.append(float(a[3]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_brake)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='chocolate', label='刹车状态', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='chocolate', label='刹车状态', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_turn(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_turn = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_turn.append(float(a[4]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_turn)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='saddlebrown', label='转向灯状态', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='saddlebrown', label='转向灯状态', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_speedLon(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_speedLon = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_speedLon.append(float(a[5]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_speedLon)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='peachpuff', label='纵向相对运动速度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='peachpuff', label='纵向相对运动速度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_speedLat(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_speedLat = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_speedLat.append(float(a[6]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_speedLat)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='sandybrown', label='横向相对运动速度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='sandybrown', label='横向相对运动速度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_angle(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_angle = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_angle.append(float(a[7]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_angle)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='bisque', label='车头朝向', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='bisque', label='车头朝向', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_confidence(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_confidence = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_confidence.append(float(a[8]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_confidence)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='burlywood', label='目标可信度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='burlywood', label='目标可信度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_width(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_width = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_width.append(float(a[9]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_width)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='darkgoldenrod', label='目标宽度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='darkgoldenrod', label='目标宽度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_height(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_height = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_height.append(float(a[10]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_height)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='chartreuse', label='目标高度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='chartreuse', label='目标高度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()

    def camera_object_length(self):
        self.ax1.clear()
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_length = []
        self.x_k = []
        self.y_k = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 12:
                    time.append(float(a[0]))
                    object_length.append(float(a[11]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(object_length)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='dodgerblue', label='目标长度', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='dodgerblue', label='目标长度', marker='.')
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.ax1.legend(loc='best')
        self.canvas2.draw()
        
    def show_camera(self):
        self.xc = []
        self.yc = []
        t = self.t
        if t < len(self.event_msg):
            self.log.seek(self.event_msg[t - 1][2])
            event_readed = self.log.next()
            if event_readed.channel == "camera":
                msg = lcmtypes.camera_info_t.decode(event_readed.data)
                objects = msg.objects
                i = msg.lines[1].length
                al = msg.lines[1].a
                bl = msg.lines[1].b
                cl = msg.lines[1].c
                dl = msg.lines[1].d
                il = msg.lines[0].length
                all = msg.lines[0].a
                bll = msg.lines[0].b
                cll = msg.lines[0].c
                dll = msg.lines[0].d
                j = msg.lines[2].length
                ar = msg.lines[2].a
                br = msg.lines[2].b
                cr = msg.lines[2].c
                dr = msg.lines[2].d
                jr = msg.lines[3].length
                arr = msg.lines[3].a
                brr = msg.lines[3].b
                crr = msg.lines[3].c
                drr = msg.lines[3].d
                c = msg.center_line.length
                ac = msg.center_line.a
                bc = msg.center_line.b
                cc = msg.center_line.c
                dc = msg.center_line.d
                for obj in objects:
                    self.xc.append(obj.centerPoint.x)
                    self.yc.append(obj.centerPoint.y)
                if i == 0.0:
                    self.Xl = []
                    self.Yl = []
                    self.Xr = []
                    self.Yr = []
                    self.Xll = []
                    self.Yll = []
                    self.Xrr = []
                    self.Yrr = []
                    self.Xc = []
                    self.Yc = []
                else:
                    m = np.arange(i)
                    self.Xl = m
                    self.Yl = al + bl * m + cl * (m ** 2) + dl * (m ** 3)
                    ml = np.arange(il)
                    self.Xll = ml
                    self.Yll = all + bll * ml + cll * (ml ** 2) + dll * (ml ** 3)
                    n = np.arange(j)
                    self.Xr = n
                    self.Yr = ar + br * n + cr * (n ** 2) + dr * (n ** 3)
                    nr = np.arange(jr)
                    self.Xrr = nr
                    self.Yrr = arr + brr * nr + crr * (nr ** 2) + drr * (nr ** 3)
                    mc = np.arange(c)
                    self.Xc = mc
                    self.Yc = ac + bc * mc + cc * (mc ** 2) + dc * (mc ** 3)
                self.line3.set_data(self.xc, self.yc)
                self.line4.set_data(self.Yl, self.Xl)
                self.line5.set_data(self.Yr, self.Xr)
                self.line6.set_data(self.Yll, self.Xll)
                self.line7.set_data(self.Yrr, self.Xrr)
                self.line8.set_data(self.Yc, self.Xc)
                # self.plt1.legend(loc='best')
                self.canvas1.draw()
                self.reviewEdit1.setText('左车道线识别长度为：%f m\n右车道线识别长度为：%f m\n左外侧车道线识别长度为：%f m\n'
                                         '右外侧车道线识别长度为：%f m\n中心线识别长度为：%f m\n时间：%d'
                                    % (msg.lines[1].length, msg.lines[2].length, msg.lines[0].length, msg.lines[3].length, msg.center_line.length, msg.utime))
                self.textbox2.setText('%d ' % self.t)

    def show_ESR(self):
        t = self.t
        if t < len(self.event_msg):
            self.log.seek(self.event_msg[t - 1][2])
            event_readed = self.log.next()
            utime = event_readed.timestamp
            if event_readed.channel == "ESR_REAR_WHOLE_DATA":
                self.x1 = []
                self.y1 = []
                msg = lcmtypes.objects_t.decode(event_readed.data)
                objects = msg.objects
                for obj in objects:
                    self.x1.append(obj.x)
                    self.y1.append(obj.y)
                    self.be = msg.object_number
                self.line1.set_data(self.x1, self.y1)
            if event_readed.channel == "ESR_FRONT_WHOLE_DATA":
                self.x2 = []
                self.y2 = []
                msg = lcmtypes.objects_t.decode(event_readed.data)
                objects = msg.objects
                for obj in objects:
                    self.x2.append(obj.x)
                    self.y2.append(obj.y)
                    self.fe = msg.object_number
                self.line2.set_data(self.x2, self.y2)
            self.canvas1.draw()
            self.reviewEdit2.setText('ESR数据:\n后方目标个数：%d 个\n前方目标个数：%d 个\n时间戳：%d ' % (self.be, self.fe, utime))
            self.textbox2.setText('%d' % self.t)
            
    def show_lidar_obj(self):
        t = self.t
        if t < len(self.event_msg):
            self.XL = []
            self.YL = []
            self.log.seek(self.event_msg[t - 1][2])
            event_readed = self.log.next()
            if event_readed.channel == "LIDAR_OBJECT_SIDE":
                msg = lcmtypes.lidar_object_t.decode(event_readed.data)
                self.XL.append(msg.leftObject.objectCenterPosition.x)
                self.YL.append(msg.leftObject.objectCenterPosition.y)
                self.XL.append(msg.rightObject.objectCenterPosition.x)
                self.YL.append(msg.rightObject.objectCenterPosition.y)
            self.line9.set_data(self.XL, self.YL)
            self.canvas1.draw()
            self.textbox2.setText('%d' % t)
            
    def point(self):
        time_num = list(map(int, self.textbox2.text().split()))
        self.read_num = time_num[0]
        self.textbox.setText('时间戳编号将跳转至%d' % time_num[0])

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&文件")

        load_file_action = self.create_action("&保存图像",
                                              shortcut="Ctrl+S", slot=self.save_plot,
                                              tip="保存图像")
        quit_action = self.create_action("&退出", slot=self.close,
                                         shortcut="Ctrl+Q", tip="Close the application")
        one_step_up = self.create_action("&前进一步", slot=self.one_step_up,
                                         shortcut="Alt+Right", tip="Close the application")
        one_step_donw = self.create_action("&后退一步", slot=self.one_step_donw,
                                         shortcut="Alt+Left", tip="Close the application")
        pause = self.create_action("&暂停", slot=self.pause,
                                           shortcut="F9", tip="Close the application")
        resume = self.create_action("&继续", slot=self.resume,
                                           shortcut="F11", tip="Close the application")
        stope_image = self.create_action("&停止播放", slot=self.stope_image,
                                    shortcut="P", tip="Close the application")
        show_image_n = self.create_action("&开始播放", slot=self.show_image_n,
                                         shortcut="Space", tip="Close the application")
        step_up = self.create_action("&前进一步", slot=self.step_up,
                                         shortcut="Right", tip="Close the application")
        step_donw = self.create_action("&后退一步", slot=self.step_donw,
                                           shortcut="Left", tip="Close the application")
        ax_point = self.create_action("&精确到当前时间", slot=self.ax_point,
                                       shortcut="J", tip="Close the application")

        self.add_actions(self.file_menu,
                         (load_file_action, one_step_up, one_step_donw, resume, pause, stope_image, show_image_n, step_up, step_donw, ax_point, None, quit_action))

        self.help_menu = self.menuBar().addMenu("&帮助")
        about_action = self.create_action("&关于",
                                          shortcut='F1', slot=self.on_about,
                                          tip='关于这个软件')

        self.add_actions(self.help_menu, (about_action,))

    def sliderValuechange(self):
        self.t = self.read_num
        self.log.seek(self.event_msg[self.t - 1][2])
        event_readed = self.log.next()
        if event_readed.channel == "camera":
            # self.number_c = self.number_c + 1
            # if self.number_c % 2 == 0:
            self.show_camera()
        elif event_readed.channel == "ESR_REAR_WHOLE_DATA":
            self.show_ESR()
        elif event_readed.channel == "ESR_FRONT_WHOLE_DATA":
            # self.number_E = self.number_E + 1
            # if self.number_E % 5 == 0:
            self.show_ESR()
        elif event_readed.channel == "LIDAR_OBJECT_SIDE":
            self.show_lidar_obj()
    # 接收信号更新回放图像

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '提示',
                                     "确定要退出?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def read_data(self):
        global im
        global d
        if self.read_num <= len(self.event_msg):
            self.log.seek(self.event_msg[self.read_num-1][2])
            event_readed = self.log.next()
            self.v = self.v + 1
            self.slidervaluechange.emit()  # 发送信号
            if event_readed.channel == 'CAMLANE':
                try:
                    if self.__running.isSet():
                        self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
                        im = lcmtypes.image_t.decode(event_readed.data)
                        self.textbox2.setText('%d ' % self.read_num)
                        time.sleep(0.03)
                except ValueError:
                    if self.__running.isSet():
                        self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.textbox2.setText('%d ' % self.read_num)
                        time.sleep(0.03)
            elif event_readed.channel == "camera":
                time.sleep(0.0005)
            elif event_readed.channel == "ESR_REAR_WHOLE_DATA":
                time.sleep(0.0005)
            elif event_readed.channel == "ESR_FRONT_WHOLE_DATA":
                time.sleep(0.0005)
            elif event_readed.channel == "LIDAR_OBJECT_SIDE":
                time.sleep(0.0005)
        if self.v >= len(self.event_msg)-1:
            d = False
            self.textbox.setText('播放结束')

    def stope_image(self):
        global d
        d = False
        self.textbox.setText('播放结束')

    def image_change(self):
        self.v = self.slider.value()

    def show_image(self):
        sys.setrecursionlimit(100000000)
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()
        self.v = 0
        self.slider.sliderMoved.connect(self.image_change)
        self.textbox.setText('播放中')
        self.event_msg[-1][2] = 0
        global im
        global d
        d = True
        im = None
        read_pic = threading.Thread(target=self.run, name='run')
        read_pic.setDaemon(True)
        read_pic.start()
        self.update()

    def update(self):
        im2 = QtGui.QPixmap()
        while d:
            time.sleep(0.035)
            if im != None:
                im2.loadFromData(im)
                self.label_2.setPixmap(im2)
                QApplication.processEvents()

    def one_step_up(self):
        global h
        global d
        h = True
        d = False
        one_step_updata = threading.Thread(target=self.one_step_updata, name='one_step_updata')
        one_step_updata.setDaemon(True)
        one_step_updata.start()
        self.one_step_run()

    def one_step_run(self):
        global h
        global im
        im = None
        while h:
            self.read_num = self.read_num + 1
            self.t = self.read_num
            self.textbox2.setText('%d ' % self.t)
            self.slidervaluechange.emit()  # 发送信号
            if self.read_num <= len(self.event_msg):
                self.log.seek(self.event_msg[self.read_num-1][2])
                event_readed = self.log.next()
                if event_readed.channel == 'CAMLANE':
                    try:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        h = False
                    except ValueError:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        h = False
                    self.slider.setValue(self.read_num)
            time.sleep(0.001)

    def one_step_updata(self):
        while h:
            im2 = QtGui.QPixmap()
            time.sleep(0.04)
            if im != None:
                im2.loadFromData(im)
                self.label_2.setPixmap(im2)
                QApplication.processEvents()

    def one_step_donw(self):
        global h
        global d
        h = True
        d = False
        one_step_updata = threading.Thread(target=self.one_step_updata, name='one_step_updata')
        one_step_updata.setDaemon(True)
        one_step_updata.start()
        self.one_step_back()

    def one_step_back(self):
        global h
        global im
        im = None
        while h:
            self.read_num = self.read_num - 1
            self.t = self.read_num
            self.textbox2.setText('%d ' % self.t)
            self.slidervaluechange.emit()  # 发送信号
            if self.read_num <= len(self.event_msg):
                self.log.seek(self.event_msg[self.read_num-1][2])
                event_readed = self.log.next()
                if event_readed.channel == 'CAMLANE':
                    try:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        h = False
                    except ValueError:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        h = False
                    self.slider.setValue(self.read_num)
            time.sleep(0.001)

    def step_up(self):
        global h
        global d
        h = True
        d = False
        self.numb = 0
        self.step_run()
        self.step_updata()

    def step_run(self):
        global h
        global im
        im = None
        while h:
            self.read_num = self.read_num + 1
            self.t = self.read_num
            self.textbox2.setText('%d ' % self.t)
            self.slidervaluechange.emit()  # 发送信号
            if self.read_num <= len(self.event_msg):
                self.log.seek(self.event_msg[self.read_num-1][2])
                event_readed = self.log.next()
                if event_readed.channel == 'CAMLANE':
                    try:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.numb = self.numb + 1
                    except ValueError:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.numb = self.numb + 1
                elif event_readed.channel == "camera":
                    time.sleep(0.001)
                elif event_readed.channel == "ESR_REAR_WHOLE_DATA":
                    time.sleep(0.001)
                elif event_readed.channel == "ESR_FRONT_WHOLE_DATA":
                    time.sleep(0.001)
                elif event_readed.channel == "LIDAR_OBJECT_SIDE":
                    time.sleep(0.001)
            if self.numb == 100:
                h = False
                self.slider.setValue(self.read_num)

    def step_donw(self):
        global h
        global d
        h = True
        d = False
        self.numb = 0
        self.step_back()
        self.step_updata()

    def step_back(self):
        global h
        global im
        im = None
        while h:
            self.read_num = self.read_num - 1
            self.t = self.read_num
            self.textbox2.setText('%d ' % self.t)
            self.slidervaluechange.emit()  # 发送信号
            if self.read_num <= len(self.event_msg):
                self.log.seek(self.event_msg[self.read_num-1][2])
                event_readed = self.log.next()
                if event_readed.channel == 'CAMLANE':
                    try:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.numb = self.numb + 1
                    except ValueError:
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.numb = self.numb + 1
                elif event_readed.channel == "camera":
                    time.sleep(0.001)
                elif event_readed.channel == "ESR_REAR_WHOLE_DATA":
                    time.sleep(0.001)
                elif event_readed.channel == "ESR_FRONT_WHOLE_DATA":
                    time.sleep(0.001)
                elif event_readed.channel == "LIDAR_OBJECT_SIDE":
                    time.sleep(0.001)
            if self.numb == 100:
                h = False
                self.step_updata()
                self.slider.setValue(self.read_num)

    def step_updata(self):
        im2 = QtGui.QPixmap()
        if im != None:
            im2.loadFromData(im)
            self.label_2.setPixmap(im2)
            QApplication.processEvents()

    def show_image_n(self):
        sys.setrecursionlimit(100000000)
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()
        self.v = self.read_num
        self.slider.setValue(self.read_num)
        self.textbox.setText('播放中')
        self.slider.sliderMoved.connect(self.image_change)
        global im
        global d
        d = True
        im = None
        read_pic = threading.Thread(target=self.run, name='run')
        read_pic.setDaemon(True)
        read_pic.start()
        self.update()

    def pause(self):
        self.__flag.clear()    # 设置为False, 让线程阻塞
        self.textbox.setText('暂停')

    def resume(self):
        self.__flag.set()    # 设置为True, 让线程停止阻塞
        self.textbox.setText('播放中')

    def run(self):
        while d:
            self.read_num = self.v
            self.read_data()
            self.sliderValue = self.read_num
            n = int(len(self.event_msg)/100)
            if self.read_num % n == 0:
                self.slider.setValue(self.read_num)

    def read_log(self,filePath):
        f = open('camera_line_msg.txt', 'w+')
        f.write('')
        f.close

        y = open('steer_cmd.txt', 'w+')
        y.write('')
        y.close

        n = open('speed_cmd.txt', 'w+')
        n.write('')
        n.close

        g = open('vehicle_status.txt', 'w+')
        g.write('')
        g.close

        a = open('gps_data.txt', 'w+')
        a.write('')
        a.close

        e = open('camera_object_msg.txt', 'a+')
        e.write('')
        e.close

        self.textbox.setText('正在读取数据，请稍候...')
        if os.path.exists(filePath):
            path = QFileDialog.getOpenFileName(self,"Open File Dialog",filePath)
        else:
            path = QFileDialog.getOpenFileName(self,"Open File Dialog","/")

        with open(path[0],'rb') as e:
            seekn = e.seek(0, 2)
            q = []
            M = True
            while M:
                e.seek(seekn)
                f = e.read(1)
                q.append(f)
                seekn = seekn - 1
                if f == b'\xED':
                    W = q[-1] + q[-2] + q[-3] + q[-4]
                    if W == b'\xed\xa1\xda\x01':
                        M = False
            e.seek(seekn + 9)
            p = e.read(4)
            self.o = struct.unpack('>L', p)

        self.pbar.setRange(0, self.o[0])
        self.log = lcm.EventLog(path[0], "r")

        f = open('camera_line_msg.txt', 'a+')
        y = open('steer_cmd.txt', 'a+')
        n = open('speed_cmd.txt', 'a+')
        g = open('vehicle_status.txt', 'a+')
        a = open('gps_data.txt', 'a+')
        e = open('camera_object_msg.txt', 'a+')
        self.event_msg = []
        for event in self.log:
            self.pbar.setValue(event.eventnum)
            msg = [event.eventnum, event.timestamp, self.log.tell()]
            self.event_msg.append(msg)
            if event.channel == "camera":
                 msg = lcmtypes.camera_info_t.decode(event.data)
                f.write(str(msg.lines[1].a) + ' ')
                f.write(str(msg.lines[2].a) + ' ')
                f.write(str(msg.utime) + ' ')
                f.write(str(msg.change_lane) + ' ')
                f.write(str(msg.lines[1].length) + ' ')
                f.write(str(msg.lines[2].length) + ' ')
                f.write(str(msg.lane_width) + ' ')
                f.write(str(msg.object_count) + '\n')

            if event.channel == "STEER_CMD":
                msg = lcmtypes.steer_cmd_t.decode(event.data)
                y.write(str(msg.utime) + ' ')
                y.write(str(msg.steer_pos) + ' ')
                y.write(str(msg.steer_spe) + '\n')

            if event.channel == "SPEED_CMD":
                msg = lcmtypes.speed_cmd_t.decode(event.data)
                n.write(str(msg.utime) + ' ')
                n.write(str(msg.aim_spe) + ' ')
                n.write(str(msg.mode) + ' ')
                n.write(str(msg.t) + '\n')

            if event.channel == "VEHICLE_STATUS":
                msg = lcmtypes.vehicle_status_t.decode(event.data)
                g.write(str(msg.utime) + ' ')
                g.write(str(msg.nauto) + ' ')
                g.write(str(msg.steerPos) + ' ')
                g.write(str(msg.steerSpe) + ' ')
                g.write(str(msg.light) + ' ')
                g.write(str(msg.speLeft) + ' ')
                g.write(str(msg.speRight) + ' ')
                g.write(str(msg.vot) + ' ')
                g.write(str(msg.shift) + ' ')
                g.write(str(msg.disLeft) + ' ')
                g.write(str(msg.disRight) + '\n')

            if event.channel == "GPS_DATA":
                msg = lcmtypes.gps_imu_info_t.decode(event.data)
                a.write(str(msg.utime) + ' ')
                a.write(str(msg.longitude) + ' ')
                a.write(str(msg.latitude) + ' ')
                a.write(str(msg.yaw) + ' ')
                a.write(str(msg.roll) + ' ')
                a.write(str(msg.pitch) + ' ')
                a.write(str(msg.yawRate) + ' ')
                a.write(str(msg.velocityNorth) + ' ')
                a.write(str(msg.velocityEast) + ' ')
                a.write(str(msg.velocityDown) + ' ')
                a.write(str(msg.velocity) + ' ')
                a.write(str(msg.locationStatus) + ' ')
                a.write(str(msg.confidenceLevel) + ' ')
                a.write(str(msg.satelliteNumber) + '\n')
                # a.write(str(msg.accelerationLongitudinal) + '\n')

            if event.channel == "camera":
                msg = lcmtypes.camera_info_t.decode(event.data)
                objects = msg.objects
                e.write(str(msg.utime) + ' ')
                for obj in objects:
                    e.write(str(obj.id) + ' ')
                    e.write(str(obj.type) + ' ')
                    e.write(str(obj.brake) + ' ')
                    e.write(str(obj.turn) + ' ')
                    e.write(str(obj.speedLon) + ' ')
                    e.write(str(obj.speedLat) + ' ')
                    e.write(str(obj.angle) + ' ')
                    e.write(str(obj.confidence) + ' ')
                    e.write(str(obj.width) + ' ')
                    e.write(str(obj.height) + ' ')
                    e.write(str(obj.length) + '\n')

        f.close
        y.close
        n.close
        g.close
        a.close
        e.close
        self.textbox.setText('数据读取完毕')
        self.pbar.setValue(self.o[0])

        f = open('gps_data.txt', 'r')
        time = []
        velocity = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))
                if len(a) == 14:
                    velocity.append(float(a[10]))

            else:
                done = 1
        f.close
        self.x = np.array(time)
        self.y = np.array(velocity)
        n = self.get_peaks(self.x, self.y, 500)
        self.line, = self.ax.plot(n[0], n[1], color='violet', label='车速', marker='.')
        self.ax.legend(loc='best')
        self.canvas.draw()
        self.line_1, = self.ax1.plot(n[0], n[1], color='violet', label='车速', marker='.')
        self.ax1.legend(loc='best')
        self.canvas2.draw()
        
        self.plt1.clear()
        self.canvas1.draw()
        self.fe = 0
        self.be = 0
        self.x1 = []
        self.y1 = []
        self.x2 = []
        self.y2 = []
        self.xc = []
        self.yc = []
        self.Yl = []
        self.Xl = []
        self.Yr = []
        self.Xr = []
        self.Yll = []
        self.Xll = []
        self.Yrr = []
        self.Xrr = []
        self.Yc = []
        self.Xc = []
        self.XL = []
        self.YL = []
        self.x_k = []
        self.y_k = []
        self.line_2, = self.ax1.plot(self.x_k, self.y_k, color='k')
        self.line1, = self.plt1.plot(self.x1, self.y1, 'rx', label='ESR目标')
        self.line2, = self.plt1.plot(self.x2, self.y2, 'rx')
        self.line3, = self.plt1.plot(self.xc, self.yc, 'b.', label='视觉目标')
        self.plt1.plot(0, 0, 'r.', label='本车')
        self.line4, = self.plt1.plot(self.Yl, self.Xl, color='yellow', label='左车道线')
        self.line5, = self.plt1.plot(self.Yr, self.Xr, color='g', label='右车道线')
        self.line6, = self.plt1.plot(self.Yll, self.Xll, color='coral', label='左外侧车道线')
        self.line7, = self.plt1.plot(self.Yrr, self.Xrr, color='m', label='右外侧车道线')
        self.line8, = self.plt1.plot(self.Yc, self.Xc, color='c', label='中心线')
        self.line9, = self.plt1.plot(self.XL, self.YL, 'kp', label='16线目标')
        self.plt1.legend(loc='upper right')
        self.plt1.axis([-20, 20, -150, 150])
        self.canvas1.draw()
        self.slider.setRange(0, len(self.event_msg) - 1)
        self.slider.setValue(0)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)

    def update_pltdata(self):
        self.x0, self.x1 = self.ax.get_xlim()
        cha = self.x1 - self.x0
        n = self.get_peaks(self.x, self.y, 500, self.x0-cha, self.x1+cha)
        self.x2, self.x3 = self.ax1.get_xlim()
        cha1 = self.x3 - self.x2
        n1 = self.get_peaks(self.x, self.y, 500, self.x2 - cha1, self.x3 + cha1)
        self.line.set_data(n[0], n[1])
        self.line_1.set_data(n1[0], n1[1])
        self.line_2.set_data(self.x_k, self.y_k)
        self.ax.figure.canvas.draw()
        self.ax1.figure.canvas.draw()

    def ax_point(self):
        self.t = self.read_num
        self.x_k = []
        self.y_k = []
        self.log.seek(self.event_msg[self.t - 1][2])
        event_readed = self.log.next()
        y0, y1 = self.ax1.get_ylim()
        for i in range(1000):
            self.x_k.append(event_readed.timestamp)
            self.y_k.append(i)
        self.ax1.axis([event_readed.timestamp - 5000000, event_readed.timestamp + 5000000, y0, y1])
        self.line_2.set_data(self.x_k, self.y_k)
        self.canvas2.draw()


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
        main()
