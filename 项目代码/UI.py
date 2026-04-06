from PySide6 import QtWidgets, QtCore, QtGui


class IconWithText(QtWidgets.QWidget):
    clicked = QtCore.Signal()

    def __init__(self, text, icon_path, btn_size=(390, 200), icon_size=(280, 170)):
        super().__init__()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ===== 按钮（只放图标）=====
        self.button = QtWidgets.QPushButton()
        self.button.setFixedSize(*btn_size)

        self.button.setIcon(QtGui.QIcon(icon_path))
        self.button.setIconSize(QtCore.QSize(*icon_size))

        self.button.setStyleSheet(
            """
        QPushButton {
            background-color: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            padding-top: -10px;
        }
        QPushButton:hover {
            background-color: rgba(90, 141, 238, 40);
            border-radius: 10px;
        }
        QPushButton:pressed {
            background-color: rgba(90, 141, 238, 80);
        }
        """
        )

        # ===== 文字（在按钮下面）=====
        self.label = QtWidgets.QLabel(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet(
            """
            margin: 0px;
            padding: 0px;
            font-size:14px;
            color: white; 
            """
        )
        # ===== 组合 =====
        layout.addWidget(self.button, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(
            self.label, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter
        )

        # 点击信号透传
        self.button.clicked.connect(self.clicked.emit)


class Ui_MainWindow(object):
    def setupUI(self, MainWindow):

        MainWindow.resize(920, 600)
        MainWindow.setWindowTitle("路面缺陷检测分析")

        # Qt 中 QMainWindow 不能直接放布局，必须先设置 centralWidget
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralWidget)

        # 堆叠页面
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralWidget)

        mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        mainLayout.addWidget(self.stackedWidget)

        # ================== Page0：首页 ==================
        self.page_home = QtWidgets.QWidget()
        self.page_home.setObjectName("homePage")
        self.page_home.setStyleSheet(
            """
        #homePage {
            background-image: url(icon/bg2.png);
            background-repeat: no-repeat;
            background-position: top;
        }
        """
        )
        homeLayout = QtWidgets.QVBoxLayout(self.page_home)
        # homeLayout.setSpacing(50)

        # ===== 按钮 =====
        self.btnVideoOD = IconWithText(
            "视频检测", "icon/TV.png", (390, 200), (280, 170)
        )
        self.btnVideoOD.setFixedHeight(200)
        self.btnRealTimOD = IconWithText(
            "实时检测", "icon/RT.png", (390, 200), (280, 170)
        )
        self.btnRealTimOD.setFixedHeight(200)

        self.btn3 = IconWithText("裂缝分析", "icon/MAG.png", (170, 140), (150, 110))
        self.btn3.setFixedHeight(140)

        self.btn4 = IconWithText("管理", "icon/GL.png", (170, 140), (150, 110))
        self.btn4.setFixedHeight(140)

        self.btn5 = IconWithText("时间", "icon/TM.png", (170, 140), (150, 110))
        self.btn5.setFixedHeight(140)

        self.btn6 = IconWithText("设置", "icon/SET.png", (170, 140), (150, 110))
        self.btn6.setFixedHeight(140)

        btns = [
            self.btnVideoOD,
            self.btnRealTimOD,
            self.btn3,
            self.btn4,
            self.btn5,
            self.btn6,
        ]
        for btn in btns:
            btn.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

        # ===== 上面一行（2个）=====
        homeTopLayout = QtWidgets.QHBoxLayout()
        homeTopLayout.setSpacing(30)
        homeTopLayout.addWidget(self.btnVideoOD)
        homeTopLayout.addWidget(self.btnRealTimOD)

        # ===== 下面一行（3个）=====
        homeBottomLayout = QtWidgets.QHBoxLayout()
        homeBottomLayout.setSpacing(30)
        homeBottomLayout.addWidget(self.btn3)
        homeBottomLayout.addWidget(self.btn4)
        homeBottomLayout.addWidget(self.btn5)
        homeBottomLayout.addWidget(self.btn6)
        # homeBottomLayout.addWidget(self.btn7)

        # ===== 加入主布局 =====
        homeLayout.addStretch(5)  # 上留白（可选）
        homeLayout.addLayout(homeTopLayout)
        homeLayout.addSpacing(50)  # 两行之间间距
        homeLayout.addLayout(homeBottomLayout)
        homeLayout.addStretch(5)  # 下留白（让布局更居中）
        self.stackedWidget.addWidget(self.page_home)

        # ================== Page1检测界面 ==================
        self.page_detect = QtWidgets.QWidget()
        self.stackedWidget.addWidget(self.page_detect)

        # ↓↓↓ UI page_detect ↓↓↓
        mainLayout2 = QtWidgets.QHBoxLayout(self.page_detect)

        groupBox = QtWidgets.QGroupBox()
        groupBox.setMinimumSize(600, 600)
        groupBox.setMaximumSize(700, 600)
        leftLayout = QtWidgets.QVBoxLayout(groupBox)

        topLayout = QtWidgets.QHBoxLayout()

        self.label_ori_video = QtWidgets.QLabel()
        self.label_treated = QtWidgets.QLabel()

        self.label_ori_video.setMinimumSize(300, 300)
        self.label_treated.setMinimumSize(300, 300)

        self.label_ori_video.setStyleSheet("border:1px solid #D7E2F9;")
        self.label_treated.setStyleSheet("border:1px solid #D7E2F9;")

        topLayout.addWidget(self.label_ori_video)
        topLayout.addWidget(self.label_treated)
        leftLayout.addLayout(topLayout)

        self.textLog = QtWidgets.QTextBrowser()
        leftLayout.addWidget(self.textLog)

        mainLayout2.addWidget(groupBox)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.setSpacing(60)
        rightLayout.setContentsMargins(30, 30, 30, 30)

        self.videoBtn = QtWidgets.QPushButton("视频文件")
        self.videoBtn.setFixedSize(120, 50)
        self.camBtn = QtWidgets.QPushButton("开始")
        self.camBtn.setFixedSize(120, 50)
        self.stopBtn = QtWidgets.QPushButton("停止")
        self.stopBtn.setFixedSize(120, 50)

        # 返回按钮（很关键）
        self.backBtn = QtWidgets.QPushButton("主页")
        self.backBtn.setFixedSize(120, 50)

        btns = [self.videoBtn, self.camBtn, self.stopBtn, self.backBtn]
        for btn in btns:
            btn.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )
        rightLayout.addWidget(self.videoBtn)
        rightLayout.addWidget(self.camBtn)
        rightLayout.addWidget(self.stopBtn)
        rightLayout.addWidget(self.backBtn)

        mainLayout2.addLayout(rightLayout)

        # ================== Page2 管理界面 ==================
        self.page_manager = QtWidgets.QWidget()
        self.stackedWidget.addWidget(self.page_manager)

        managerLayout = QtWidgets.QVBoxLayout(self.page_manager)

        # ===== 顶部栏 =====
        topBar = QtWidgets.QHBoxLayout()

        self.btnBackManager = QtWidgets.QPushButton("返回")
        self.btnBackManager.setFixedSize(90, 40)
        self.labelPath = QtWidgets.QLabel("")

        topBar.addWidget(self.btnBackManager)
        topBar.addWidget(self.labelPath)

        managerLayout.addLayout(topBar)

        # ===== 中间区域 =====
        middleLayout = QtWidgets.QHBoxLayout()

        # 左侧：目录树
        self.treeView = QtWidgets.QTreeView()
        middleLayout.addWidget(self.treeView, 2)

        # 右侧：文件展示
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setViewMode(QtWidgets.QListView.IconMode)
        self.listWidget.setIconSize(QtCore.QSize(100, 100))
        self.listWidget.setResizeMode(QtWidgets.QListView.Adjust)

        middleLayout.addWidget(self.listWidget, 5)

        managerLayout.addLayout(middleLayout)

        # ===== 底部操作 =====
        bottomLayout = QtWidgets.QHBoxLayout()

        self.btnDelete = QtWidgets.QPushButton("删除")
        self.btnExport = QtWidgets.QPushButton("导出")
        self.btnRefresh = QtWidgets.QPushButton("刷新")
        self.btnDelete.setFixedSize(100, 40)
        self.btnExport.setFixedSize(100, 40)
        self.btnRefresh.setFixedSize(100, 40)

        bottomLayout.addWidget(self.btnDelete)
        bottomLayout.addWidget(self.btnExport)
        bottomLayout.addWidget(self.btnRefresh)

        managerLayout.addLayout(bottomLayout)

        # ================== Page3 时间界面 ==================
        self.page_time = QtWidgets.QWidget()
        self.stackedWidget.addWidget(self.page_time)

        self.page_time.setStyleSheet(
            """
            background-image: url(icon/bg2.png);
            background-repeat: no-repeat;
            background-position: bottom;
        """
        )

        layout = QtWidgets.QGridLayout(self.page_time)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # ===== 左上：返回 =====
        self.btnBackTime = QtWidgets.QPushButton("返回")
        self.btnBackTime.setFixedSize(90, 40)
        # self.btnBackTime.setStyleSheet("""
        #     QPushButton {
        #         background-color: transparent;
        #         border: none;
        #         padding: 0px;
        #         margin: 0px;
        #         color:white;
        #     }
        #     """)
        layout.addWidget(
            self.btnBackTime, 0, 0, alignment=QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
        )

        # ===== 右上：日期 =====
        self.labelDate = QtWidgets.QLabel("2026-04-01")
        self.labelDate.setStyleSheet(
            "font-size:20px; color:white; background-color: transparent;"
        )
        layout.addWidget(
            self.labelDate, 0, 2, alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignTop
        )
        self.labelDate.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.labelDate.setAutoFillBackground(False)

        # ===== 中间：时间（核心）=====
        self.labelTime = QtWidgets.QLabel("00:00:00")
        self.labelTime.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTime.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.labelTime.setAutoFillBackground(False)
        self.labelTime.setStyleSheet(
            """
            font-size:100px;
            font-weight:bold;
            color:#5A8DEE;
        """
        )
        # layout.addWidget(self.labelTime, 1, 1, alignment=QtCore.Qt.AlignRight)
        layout.addWidget(self.labelTime, 1, 0, 1, 3, alignment=QtCore.Qt.AlignCenter)

        # ===== 左下：温度 =====
        self.labelTemp = QtWidgets.QLabel("温度: 23°C")
        self.labelTemp.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.labelTemp.setAutoFillBackground(False)
        self.labelTemp.setStyleSheet(
            "font-size:20px; color:white; background-color: transparent;"
        )

        # ===== 右下：位置 =====
        self.labelLocation = QtWidgets.QLabel("位置: 中国-山东")
        self.labelLocation.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.labelLocation.setAutoFillBackground(False)
        self.labelLocation.setStyleSheet(
            "font-size:20px; color:white; background-color: transparent;"
        )

        # ===== 右下容器 =====
        bottomRightLayout = QtWidgets.QVBoxLayout()
        bottomRightLayout.setSpacing(5)

        bottomRightLayout.addWidget(self.labelTemp, alignment=QtCore.Qt.AlignRight)
        bottomRightLayout.addWidget(self.labelLocation, alignment=QtCore.Qt.AlignRight)

        layout.addLayout(
            bottomRightLayout,
            2,
            2,
            alignment=QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom,
        )

        # 拉伸比例（让中间最大）
        layout.setRowStretch(1, 10)
        layout.setColumnStretch(1, 10)

        # ================== Page4 设置界面 ==================
        self.page_setting = QtWidgets.QWidget()
        self.stackedWidget.addWidget(self.page_setting)

        layout = QtWidgets.QVBoxLayout(self.page_setting)

        # ===== 返回 =====
        self.btnBackSetting = QtWidgets.QPushButton("返回")
        self.btnBackSetting.setFixedSize(100, 40)
        layout.addWidget(self.btnBackSetting, alignment=QtCore.Qt.AlignLeft)
        layout.addStretch()

        # ===== 中间容器 =====
        centerWidget = QtWidgets.QWidget()
        centerWidget.setFixedWidth(500)
        centerWidget.setStyleSheet(
            """
        QLabel {
            font-size: 20px;
        }
        QComboBox {
            font-size: 20px;
        }
        """
        )

        grid = QtWidgets.QGridLayout(centerWidget)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setSpacing(50)
        # grid.setHorizontalSpacing(50)
        # grid.setVerticalSpacing(50)

        # ===== 版本号 =====
        self.labelVersion = QtWidgets.QLabel("版本号: v1.0.0")
        grid.addWidget(QtWidgets.QLabel("版本信息"), 0, 0)
        grid.addWidget(self.labelVersion, 0, 1)

        # layout.addWidget(self.labelVersion)

        # ===== 模型选择 =====
        self.comboModel = QtWidgets.QComboBox()
        self.comboModel.addItems(["yolov8n.pt", "yolo11n.pt"])
        # layout.addWidget(QtWidgets.QLabel("模型设置"))
        grid.addWidget(QtWidgets.QLabel("模型设置"), 1, 0)
        grid.addWidget(self.comboModel, 1, 1)
        # layout.addWidget(self.comboModel)

        # ===== 置信度 =====
        self.sliderConf = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sliderConf.setRange(1, 100)
        self.sliderConf.setValue(60)

        self.labelConf = QtWidgets.QLabel("0.60")
        grid.addWidget(QtWidgets.QLabel("置信度设置"), 2, 0)

        confLayout = QtWidgets.QHBoxLayout()
        confLayout.addWidget(self.sliderConf)
        confLayout.addWidget(self.labelConf)

        grid.addLayout(confLayout, 2, 1)

        # ===== NMS =====
        self.sliderNMS = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sliderNMS.setRange(1, 100)
        self.sliderNMS.setValue(45)

        self.labelNMS = QtWidgets.QLabel("0.45")
        grid.addWidget(QtWidgets.QLabel("NMS设置"), 3, 0)

        nmsLayout = QtWidgets.QHBoxLayout()
        nmsLayout.addWidget(self.sliderNMS)
        nmsLayout.addWidget(self.labelNMS)

        grid.addLayout(nmsLayout, 3, 1)

        grid.setAlignment(QtCore.Qt.AlignLeft)

        layout.addWidget(centerWidget, alignment=QtCore.Qt.AlignCenter)

        layout.addStretch()
        layout.addStretch()
        # ===== 保存按钮 =====
        # self.btnSaveSetting = QtWidgets.QPushButton("保存设置")
        # self.btnSaveSetting.setFixedSize(100, 40)
        # # layout.addWidget(self.btnSaveSetting)
        # layout.addWidget(self.btnSaveSetting, alignment=QtCore.Qt.AlignCenter)
        # # layout.setAlignment(self.btnSaveSetting, QtCore.Qt.AlignCenter)

        # ================== Page3 裂缝分析 ==================
        self.page_crack = QtWidgets.QWidget()
        self.page_crack.setContentsMargins(10, 10, 10, 30)
        self.stackedWidget.addWidget(self.page_crack)

        layout = QtWidgets.QVBoxLayout(self.page_crack)

        # ===== 上部：图片显示 =====
        imgLayout = QtWidgets.QHBoxLayout()

        self.label_crack_ori = QtWidgets.QLabel("原图")
        self.label_crack_res = QtWidgets.QLabel("分割结果")

        for lab in [self.label_crack_ori, self.label_crack_res]:
            lab.setMinimumSize(300, 300)
            lab.setStyleSheet("border:1px solid #D7E2F9;")
            lab.setAlignment(QtCore.Qt.AlignCenter)

        imgLayout.addWidget(self.label_crack_ori)
        imgLayout.addWidget(self.label_crack_res)

        layout.addLayout(imgLayout)

        # ===== 下部：按钮 =====
        btnLayout = QtWidgets.QHBoxLayout()

        self.btn_select_img = QtWidgets.QPushButton("选择图片")
        self.btn_select_img.setFixedSize(100, 40)
        self.btn_run_seg = QtWidgets.QPushButton("开始分析")
        self.btn_run_seg.setFixedSize(100, 40)
        self.btn_back_crack = QtWidgets.QPushButton("返回")
        self.btn_back_crack.setFixedSize(100, 40)

        btnLayout.addWidget(self.btn_select_img)
        btnLayout.addWidget(self.btn_run_seg)
        btnLayout.addWidget(self.btn_back_crack)

        layout.addLayout(btnLayout)

        # 默认显示首页
        self.stackedWidget.setCurrentWidget(self.page_home)
