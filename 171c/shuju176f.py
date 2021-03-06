import os
import lcm
import lcmtypes
import matplotlib
import threading
import time
import sys
import numpy as np

matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
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
        self.plt.clear()
        self.canvas.draw()
        self.plt1.clear()
        self.canvas1.draw()

    def create_main_frame(self):
        self.main_frame = QWidget()

        self.dpi = 100
        self.fig = Figure((6.5, 3.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        self.fig1 = Figure((6.5, 3.0), dpi=self.dpi)
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.main_frame)
        self.label_2 = QLabel(self)
        self.label_2.setMinimumSize(QtCore.QSize(700, 500))
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_2.setPixmap(QtGui.QPixmap('0.jpg'))
        self.label_3 = QLabel(self)
        self.label_3.setMaximumSize(QtCore.QSize(700, 75))
        self.label_4 = QLabel(self)
        self.label_4.setMaximumSize(QtCore.QSize(700, 25))

        self.fileButton = QPushButton("读文件")
        self.fileButton.setMaximumWidth(250)
        self.fileLineEdit = QLineEdit()
        self.fileButton.clicked.connect(lambda: self.read_log(self.fileLineEdit.text()))
        self.textbox = QLineEdit()
        self.textbox.setMaximumWidth(250)
        self.textbox2 = QLineEdit()
        self.textbox2.setMaximumWidth(140)

        self.plt = self.fig.add_subplot(111)
        self.plt1 = self.fig1.add_subplot(111)
        self.plt1.set_xticks([-15, -10, -5, 0, 5, 10, 15])
        self.plt1.set_yticks((0, 20, 40, 60, 80, 100))

        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        self.mpl_toolbar1 = NavigationToolbar(self.canvas1, self.main_frame)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMaximumWidth(400)
        self.slider_label = QLabel('时间戳编号：')
        self.slider_label.setMaximumWidth(100)
        self.reviewEdit = QTextEdit()
        self.reviewEdit.setMaximumSize(QtCore.QSize(250,290))
        self.slidervaluechange.connect(self.sliderValuechange)

        self.tab1 = QScrollArea()
        self.tab1.setWidget(QWidget())
        background_color = QColor()
        background_color.setNamedColor('#E6E6FA')
        self.tab1.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Window, background_color)
        self.tab1.setPalette(palette)
        self.tab1.setAlignment(Qt.AlignCenter)
        self.tab1.setMaximumSize(QtCore.QSize(250,500))
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
        self.text_browser_16 = QPushButton("横摆角速度")
        self.text_browser_17 = QPushButton("纵向加速度")
        self.text_browser_18 = QPushButton("横向加速度")
        self.text_browser_19 = QPushButton("车速")
        self.text_browser_20 = QPushButton("航向角")
        self.text_browser_21 = QPushButton("翻滚角")
        self.text_browser_22 = QPushButton("俯仰角")
        self.text_browser_23 = QPushButton("横摆角速度")
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
        self.Button32.setMaximumWidth(250)
        self.Button38 = QPushButton("视觉回放")
        self.Button38.setMaximumWidth(250)
        self.Button41 = QPushButton("ESR数据回放")
        self.Button41.setMaximumWidth(250)
        self.Button54 = QPushButton("定位当前时间戳编号")
        self.Button54.setMaximumWidth(250)
        self.Button55 = QPushButton("视频回放")
        self.Button55.setMaximumWidth(250)
        self.Button56 = QPushButton("暂停")
        self.Button56.setMaximumWidth(250)
        self.Button57 = QPushButton("开始")
        self.Button57.setMaximumWidth(250)
        self.Button58 = QPushButton("停止播放")
        self.Button58.setMaximumWidth(250)
        self.Button59 = QPushButton("前进一步")
        self.Button59.setMaximumWidth(250)
        self.Button60 = QPushButton("后退一步")
        self.Button60.setMaximumWidth(250)
        self.Button61 = QPushButton("从当前位置播放")
        self.Button61.setMaximumWidth(250)

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
        self.text_browser_16.clicked.connect(self.VEHICLE_STATUS_yawRate)
        self.text_browser_17.clicked.connect(self.VEHICLE_STATUS_accelerationLon)
        self.text_browser_18.clicked.connect(self.VEHICLE_STATUS_accelerationLat)
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
        self.Button38.clicked.connect(self.draw_line)
        self.Button41.clicked.connect(self.draw_ESR)
        self.Button54.clicked.connect(self.point)
        self.Button55.clicked.connect(self.show_image)
        self.Button56.clicked.connect(self.pause)
        self.Button57.clicked.connect(self.resume)
        self.Button58.clicked.connect(self.stope_image)
        self.Button59.clicked.connect(self.one_step_up)
        self.Button60.clicked.connect(self.one_step_donw)
        self.Button61.clicked.connect(self.show_image_n)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.mpl_toolbar)
        vbox1.addWidget(self.canvas)
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
                   self.text_browser_13, self.text_browser_14, self.text_browser_15, self.text_browser_16,
                   self.text_browser_17, self.text_browser_18, self.text_browser_19, self.text_browser_20,
                   self.text_browser_21, self.text_browser_22, self.text_browser_23, self.text_browser_24,
                   self.text_browser_25, self.text_browser_26, self.text_browser_27, self.text_browser_28,
                   self.text_browser_29, self.text_browser_30, self.text_browser_31, self.text_browser_33,
                   self.text_browser_34, self.text_browser_36, self.text_browser_37, self.text_browser_39,
                   self.text_browser_40, self.text_browser_42, self.text_browser_43, self.text_browser_44,
                   self.text_browser_45, self.text_browser_46, self.text_browser_47, self.text_browser_48,
                   self.text_browser_49, self.text_browser_50, self.text_browser_51, self.text_browser_52]:
            vbox.addWidget(w)
            vbox.setAlignment(w, Qt.AlignVCenter)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.tab1)
        vbox2.addWidget(self.fileButton)
        vbox2.addWidget(self.Button32)
        vbox2.addWidget(self.Button38)
        vbox2.addWidget(self.Button41)
        vbox2.addWidget(self.textbox)
        vbox2.addWidget(self.Button54)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.Button55)
        hbox3.addWidget(self.Button56)
        hbox3.addWidget(self.Button57)
        hbox3.addWidget(self.Button58)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.slider)
        hbox4.addLayout(h1box)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(self.Button60)
        hbox5.addWidget(self.Button61)
        hbox5.addWidget(self.Button59)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.label_2)
        hbox1.addLayout(vbox2)

        vbox3 = QVBoxLayout()
        vbox3.addLayout(hbox1)
        vbox3.addWidget(self.label_4)
        vbox3.addLayout(hbox4)
        vbox3.addLayout(hbox3)
        vbox3.addLayout(hbox5)
        vbox3.addWidget(self.reviewEdit)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox3)
        
        self.main_frame.setLayout(hbox)
        self.setGeometry(150, 40, 1600, 980)
        self.setCentralWidget(self.main_frame)

    def SPEED_CMD_aim_spe(self):
        f = open('speed_cmd.txt', 'r')
        aim_speed = []
        time = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    aim_speed.append(float(a[1]))

                if len(a) == 4:
                    time.append(float(a[0]))

            else:
                done = 1
        f.close
        self.plt.plot(time,aim_speed, color='r', label='目标车速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def SPEED_CMD_mode(self):
        f = open('speed_cmd.txt', 'r')
        mode = []
        time = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    mode.append(float(a[2]))
                if len(a) == 4:
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.plt.plot(time, mode, color='k', label='驾驶模式', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def SPEED_CMD_t(self):
        f = open('speed_cmd.txt', 'r')
        time = []
        t = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 4:
                    t.append(float(a[3]))
                if len(a) == 4:
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.plt.plot(time, t, color='g', label='达到目标速度时间', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def STEER_CMD_steer_pos(self):
        f = open('steer_cmd.txt', 'r')
        time = []
        steer_pos = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 3:
                    steer_pos.append(float(a[1]))
                if len(a) == 3:
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.plt.plot(time, steer_pos, color='m', label='决策方向盘转角', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def STEER_CMD_steer_spe(self):
        f = open('steer_cmd.txt', 'r')
        time = []
        steer_spe = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 3:
                    steer_spe.append(float(a[2]))
                if len(a) == 3:
                    time.append(float(a[0]))
            else:
                done = 1
        f.close
        self.plt.plot(time, steer_spe, color='tan', label='决策方向盘转速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_nauto(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        mode = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    mode.append(int(a[1]))

            else:
                done = 1
        f.close
        self.plt.plot(time,mode, color='b', label='驾驶模式开关状态', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_steerPos(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        steerPos = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    steerPos.append(float(a[2]))

            else:
                done = 1
        f.close
        self.plt.plot(time, steerPos, color='yellow', label='方向盘转角', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_steerSpe(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        steerspe = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    steerspe.append(float(a[3]))

            else:
                done = 1
        f.close
        self.plt.plot(time, steerspe, color='darkviolet', label='方向盘转速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_light(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        light = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    light.append(float(a[4]))

            else:
                done = 1
        f.close
        self.plt.plot(time, light, color='aqua', label='转向灯', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_speLeft(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        speed = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    speed.append(float(a[5]))

            else:
                done = 1
        f.close
        self.plt.plot(time, speed, color='y', label='左轮速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_speRight(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        speed = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    speed.append(float(a[6]))

            else:
                done = 1
        f.close
        self.plt.plot(time, speed, color='c', label='右轮速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_vot(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        vot = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    vot.append(float(a[7]))

            else:
                done = 1
        f.close
        self.plt.plot(time, vot, color='brown', label='电压', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_shift(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        shift = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    shift.append(float(a[8]))

            else:
                done = 1
        f.close
        self.plt.plot(time, shift, color='lime', label='挡位', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_disLeft(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        dis = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    dis.append(float(a[9]))

            else:
                done = 1
        f.close
        self.plt.plot(time, dis, color='gold', label='左轮距离', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_disRight(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        dis = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    dis.append(float(a[10]))

            else:
                done = 1
        f.close
        self.plt.plot(time, dis, color='orange', label='右轮距离', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_yawRate(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        yawrate = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    yawrate.append(float(a[11]))

            else:
                done = 1
        f.close
        self.plt.plot(time, yawrate, color='coral', label='横摆角速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_accelerationLon(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        accelerationLon = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    accelerationLon.append(float(a[12]))

            else:
                done = 1
        f.close
        self.plt.plot(time, accelerationLon, color='peru', label='纵向加速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def VEHICLE_STATUS_accelerationLat(self):
        f = open('vehicle_status.txt', 'r')
        time = []
        accelerationLat = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    accelerationLat.append(float(a[13]))

            else:
                done = 1
        f.close
        self.plt.plot(time, accelerationLat, color='pink', label='横向加速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_velocity(self):
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
        self.plt.plot(time, velocity, color='violet', label='车速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_yaw(self):
        f = open('gps_data.txt', 'r')
        time = []
        yaw = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    yaw.append(float(a[3]))

            else:
                done = 1
        f.close
        self.plt.plot(time, yaw, color='plum', label='航向角', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_roll(self):
        f = open('gps_data.txt', 'r')
        time = []
        roll = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    roll.append(float(a[4]))

            else:
                done = 1
        f.close
        self.plt.plot(time, roll, color='purple', label='翻滚角', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_pitch(self):
        f = open('gps_data.txt', 'r')
        time = []
        pitch = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    pitch.append(float(a[5]))

            else:
                done = 1
        f.close
        self.plt.plot(time, pitch, color='indigo', label='俯仰角', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_yawRate(self):
        f = open('gps_data.txt', 'r')
        time = []
        yawRate = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    yawRate.append(float(a[6]))

            else:
                done = 1
        f.close
        self.plt.plot(time, yawRate, color='navy', label='横摆角速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_velocityNorth(self):
        f = open('gps_data.txt', 'r')
        time = []
        velocityNorth = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    velocityNorth.append(float(a[7]))

            else:
                done = 1
        f.close
        self.plt.plot(time, velocityNorth, color='teal', label='北向车速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_velocityEast(self):
        f = open('gps_data.txt', 'r')
        time = []
        velocityEast = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    velocityEast.append(float(a[8]))

            else:
                done = 1
        f.close
        self.plt.plot(time, velocityEast, color='gray', label='东向车速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_velocityDown(self):
        f = open('gps_data.txt', 'r')
        time = []
        velocityDown = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    velocityDown.append(float(a[9]))

            else:
                done = 1
        f.close
        self.plt.plot(time, velocityDown, color='darkred', label='垂直地面速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_locationStatus(self):
        f = open('gps_data.txt', 'r')
        time = []
        locationStatus = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    locationStatus.append(float(a[11]))

            else:
                done = 1
        f.close
        self.plt.plot(time, locationStatus, color='tomato', label='定位模式', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_confidenceLevel(self):
        f = open('gps_data.txt', 'r')
        time = []
        confidenceLevel = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    confidenceLevel.append(float(a[12]))

            else:
                done = 1
        f.close
        self.plt.plot(time, confidenceLevel, color='sienna', label='可信度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_satelliteNumber(self):
        f = open('gps_data.txt', 'r')
        time = []
        satelliteNumber = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    satelliteNumber.append(float(a[13]))

            else:
                done = 1
        f.close
        self.plt.plot(time, satelliteNumber, color='khaki', label='卫星数量', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def GPS_DATA_longittude_latitude(self):
        f = open('gps_data.txt', 'r')
        latitude = []
        longittude = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    latitude.append(float(a[2]))

                if len(a) == 14:
                    longittude.append(float(a[1]))

            else:
                done = 1
        f.close
        self.plt.plot(latitude, longittude, color='seagreen', label='经纬度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_change_lane(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        change_lane = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    change_lane.append(float(a[9]))

            else:
                done = 1
        f.close
        self.plt.plot(time, change_lane, color='deepskyblue', label='换道状态', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_left_lane(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        left_lane = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    left_lane.append(float(a[0]))

            else:
                done = 1
        f.close
        self.plt.plot(time, left_lane, color='crimson', label='左车道线', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_right_lane(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        right_lane = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    right_lane.append(float(a[4]))

            else:
                done = 1
        f.close
        self.plt.plot(time, right_lane, color='orchid', label='右车道线', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_left_line_length(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        left_lane_length = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    left_lane_length.append(float(a[10]))

            else:
                done = 1
        f.close
        self.plt.plot(time, left_lane_length, color='dodgerblue', label='左车道线长度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_right_line_length(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        right_lane_length = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    right_lane_length.append(float(a[11]))

            else:
                done = 1
        f.close
        self.plt.plot(time, right_lane_length, color='thistle', label='右车道线长度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_lane_width(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        lane_width = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    lane_width.append(float(a[12]))

            else:
                done = 1
        f.close
        self.plt.plot(time, lane_width, color='mediumspringgreen', label='车道宽度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_count(self):
        f = open('camera_line_msg.txt', 'r')
        time = []
        object_count = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[8]))

                if len(a) == 14:
                    object_count.append(float(a[13]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_count, color='mediumslateblue', label='目标个数', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_id(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_id = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_id.append(float(a[3]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_id, color='maroon', label='目标的ID', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_type(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_type = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_type.append(float(a[4]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_type, color='sienna', label='目标类别', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_brake(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_brake = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_brake.append(float(a[5]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_brake, color='chocolate', label='刹车状态', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_turn(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_turn = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_turn.append(float(a[6]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_turn, color='saddlebrown', label='转向灯状态', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_speedLon(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_speedLon = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_speedLon.append(float(a[7]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_speedLon, color='peachpuff', label='纵向相对运动速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_speedLat(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_speedLat = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_speedLat.append(float(a[8]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_speedLat, color='sandybrown', label='横向相对运动速度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_angle(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_angle = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_angle.append(float(a[9]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_angle, color='bisque', label='车头朝向', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_confidence(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_confidence = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_confidence.append(float(a[10]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_confidence, color='burlywood', label='目标可信度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_width(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_width = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_width.append(float(a[11]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_width, color='darkgoldenrod', label='目标宽度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_height(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_height = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_height.append(float(a[12]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_height, color='chartreuse', label='目标高度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def camera_object_length(self):
        f = open('camera_object_msg.txt', 'r')
        time = []
        object_length = []
        done = 0
        while not done:
            line = f.readline()
            line = line.strip('\n')
            if line != '':
                a = line.split(' ')
                if len(a) == 14:
                    time.append(float(a[0]))

                if len(a) == 14:
                    object_length.append(float(a[13]))

            else:
                done = 1
        f.close
        self.plt.plot(time, object_length, color='dodgerblue', label='目标长度', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()

    def draw_line(self):
        self.s = 0
        self.slider.setRange(0, len(self.event_msg)-1)
        self.slider.setValue(0)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.reviewEdit.setText(' ')

    def draw_ESR(self):
        self.s = 1
        self.slider.setRange(0, len(self.event_msg)-1)
        self.slider.setValue(0)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.reviewEdit.setText(' ')

    def show_camera(self):
        if d:
            x = []
            y = []
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
                    j = msg.lines[2].length
                    ar = msg.lines[2].a
                    br = msg.lines[2].b
                    cr = msg.lines[2].c
                    dr = msg.lines[2].d
                    for obj in objects:
                        x.append(obj.centerPoint.x)
                        y.append(obj.centerPoint.y)
                    if i == 0.0:
                        Xl = 0
                        Yl = 0
                        Xr = 0
                        Yr = 0
                    else:
                        m = np.arange(i)
                        Xl = m
                        Yl = al + bl * m + cl * (m ** 2) + dl * (m ** 3)
                        n = np.arange(j)
                        Xr = n
                        Yr = ar + br * n + cr * (n ** 2) + dr * (n ** 3)
                    self.plt1.clear()
                    self.plt1.plot(x, y, 'b.', label='视觉目标')
                    self.plt1.plot(0, 0, 'r.', label='本车')
                    self.plt1.plot(Yl, Xl, color='yellow', label='左车道线', marker='.')
                    self.plt1.plot(Yr,Xr, color='g', label='右车道线', marker='.')
                    self.plt1.set_xticks([-35, -25, -15, -5, 0, 5, 15, 25, 35])
                    self.plt1.set_yticks((0, 20, 40, 60, 80, 100))
                    self.plt1.legend(loc='best')
                    self.canvas1.draw()
                    self.reviewEdit.setText('左车道线识别长度为：%f m\n右车道线识别长度为：%f m\n时间：%d'
                                            % (msg.lines[1].length, msg.lines[2].length, msg.utime))
                    self.textbox2.setText('%d ' % self.t)

    def show_ESR(self):
        if d:
            x = []
            y = []
            t = self.t
            if t < len(self.event_msg):
                self.log.seek(self.event_msg[t - 1][2])
                event_readed = self.log.next()
                if event_readed.channel == "ESR_REAR_WHOLE_DATA":
                    msg = lcmtypes.objects_t.decode(event_readed.data)
                    objects = msg.objects
                    for obj in objects:
                        x.append(obj.x)
                        y.append(obj.y)
                    self.plt1.clear()
                    self.plt1.plot(x, y, 'r.')
                    self.plt1.set_xticks([-35, -25, -15, -5, 0, 5, 15, 25, 35])
                    self.plt1.set_yticks((-100, -80, -60, -40, -20, 0))
                    self.canvas1.draw()
                    self.reviewEdit.setText('目标个数：%d 个' % msg.object_number)
                    self.textbox2.setText('%d' % self.t)

    def point(self):
        time_num = list(map(int, self.textbox2.text().split()))
        self.read_num = time_num[0]
        self.textbox.setText('时间戳编号将跳转至%d' % time_num[0])

    def create_menu(self):
        self.file_menu = self.menuBar().addMenu("&文件")

        load_file_action = self.create_action("&保存图像",
                                              shortcut="Ctrl+S", slot=self.save_plot,
                                              tip="Save the plot")
        quit_action = self.create_action("&退出", slot=self.close,
                                         shortcut="Ctrl+Q", tip="Close the application")
        one_step_up = self.create_action("&前进一步", slot=self.one_step_up,
                                         shortcut="Alt+6", tip="Close the application")
        one_step_donw = self.create_action("&后退一步", slot=self.one_step_donw,
                                         shortcut="Alt+4", tip="Close the application")
        pause = self.create_action("&暂停", slot=self.pause,
                                           shortcut="F9", tip="Close the application")
        resume = self.create_action("&开始", slot=self.resume,
                                           shortcut="F11", tip="Close the application")
        stope_image = self.create_action("&停止播放", slot=self.stope_image,
                                    shortcut="P", tip="Close the application")

        self.add_actions(self.file_menu,
                         (load_file_action, one_step_up, one_step_donw, resume, pause, stope_image, None, quit_action))

        self.help_menu = self.menuBar().addMenu("&帮助")
        about_action = self.create_action("&关于",
                                          shortcut='F1', slot=self.on_about,
                                          tip='关于本软件')

        self.add_actions(self.help_menu, (about_action,))

    def sliderValuechange(self):
        self.t = self.read_num
        self.log.seek(self.event_msg[self.t - 1][2])
        event_readed = self.log.next()
        if self.s == 0:
            if event_readed.channel == "camera":
                self.number_c = self.number_c + 1
                if self.number_c % 2 == 0:
                    self.show_camera()
        else:
            if event_readed.channel == "ESR_REAR_WHOLE_DATA":
                self.number_E = self.number_E + 1
                if self.number_E % 10 == 0:
                    self.show_ESR()
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
                        time.sleep(0.04)
                except ValueError:
                    if self.__running.isSet():
                        self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
                        msg = lcmtypes.image_fragment_t.decode(event_readed.data)
                        im = msg.image
                        self.textbox2.setText('%d ' % self.read_num)
                        time.sleep(0.04)
            if event_readed.channel == "camera":
                time.sleep(0.001)
            if event_readed.channel == "ESR_REAR_WHOLE_DATA":
                    time.sleep(0.001)
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
            time.sleep(0.041)
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
                self.slider.setValue(self.t)
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

        b = open('esr_msg.txt', 'a+')
        b.write('')
        b.close

        e = open('camera_object_msg.txt', 'a+')
        e.write('')
        e.close

        self.textbox.setText('正在读取数据，请稍候...')
        if os.path.exists(filePath):
            path = QFileDialog.getOpenFileName(self,"Open File Dialog",filePath)
        else:
            path = QFileDialog.getOpenFileName(self,"Open File Dialog","/")

        self.log = lcm.EventLog(path[0], "r")

        f = open('camera_line_msg.txt', 'a+')
        y = open('steer_cmd.txt', 'a+')
        n = open('speed_cmd.txt', 'a+')
        g = open('vehicle_status.txt', 'a+')
        a = open('gps_data.txt', 'a+')
        b = open('esr_msg.txt', 'a+')
        e = open('camera_object_msg.txt', 'a+')

        for event in self.log:
            msg = [event.eventnum, event.timestamp, self.log.tell()]
            self.event_msg.append(msg)
            if event.channel == "camera":
                msg = lcmtypes.camera_info_t.decode(event.data)
                f.write(str(msg.lines[1].a) + ' ')
                f.write(str(msg.lines[1].b) + ' ')
                f.write(str(msg.lines[1].c) + ' ')
                f.write(str(msg.lines[1].d) + ' ')
                f.write(str(msg.lines[2].a) + ' ')
                f.write(str(msg.lines[2].b) + ' ')
                f.write(str(msg.lines[2].c) + ' ')
                f.write(str(msg.lines[2].d) + ' ')
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
                g.write(str(msg.disRight) + ' ')
                g.write(str(msg.yawRate) + ' ')
                g.write(str(msg.accelerationLon) + ' ')
                g.write(str(msg.accelerationLat) + '\n')

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

            if event.channel == "ESR_REAR_WHOLE_DATA":
                msg = lcmtypes.objects_t.decode(event.data)
                b.write(str(msg.object_number) + ' ')
                objects = msg.objects
                for obj in objects:
                    b.write(str(obj.x) + ' ')
                    b.write(str(obj.y) + ' ')
                    b.write(str(obj.angle) + '\n')

            if event.channel == "camera":
                msg = lcmtypes.camera_info_t.decode(event.data)
                objects = msg.objects
                e.write(str(msg.utime) + ' ')
                for obj in objects:
                    e.write(str(obj.centerPoint.x) + ' ')
                    e.write(str(obj.centerPoint.y) + ' ')
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
        b.close
        e.close
        self.textbox.setText('数据读取完毕')

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
        self.plt.plot(time, velocity, color='violet', label='车速', marker='.')
        self.plt.legend(loc='best')
        self.canvas.draw()


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()

if __name__ == "__main__":
        main()
