from PySide6 import QtCore, QtGui, QtWidgets

from branding import APP_TITLE, apply_branding


class TileButton(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(
        self,
        title,
        subtitle,
        icon_path,
        accent="#6ea8ff",
        min_height=190,
        preferred_width=240,
        large=False,
        parent=None,
    ):
        super().__init__(parent)
        self._accent = accent
        self._hovered = False
        self._large = large
        self.setObjectName("tileButton")
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMinimumHeight(min_height)
        self.setMaximumWidth(preferred_width + (36 if large else 0))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 6)
        shadow.setColor(QtGui.QColor(60, 88, 132, 38))
        self.setGraphicsEffect(shadow)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(8)

        self.topRow = QtWidgets.QHBoxLayout()
        self.topRow.setContentsMargins(0, 0, 0, 0)
        self.topRow.setSpacing(8)

        self.iconCard = QtWidgets.QLabel()
        self.iconCard.setObjectName("tileIcon")
        self.iconCard.setAlignment(QtCore.Qt.AlignCenter)
        self.iconCard.setFixedSize(64 if large else 52, 64 if large else 52)
        self.iconCard.setPixmap(self._build_icon_pixmap(icon_path))

        self.badge = QtWidgets.QLabel("推荐" if large else "可用")
        self.badge.setObjectName("tileBadge")
        self.badge.setAlignment(QtCore.Qt.AlignCenter)

        self.topRow.addWidget(self.iconCard, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.topRow.addStretch(1)
        self.topRow.addWidget(self.badge, 0, QtCore.Qt.AlignTop)

        self.titleLabel = QtWidgets.QLabel(title)
        self.titleLabel.setObjectName("tileTitle")
        self.titleLabel.setWordWrap(True)

        self.subtitleLabel = QtWidgets.QLabel(subtitle)
        self.subtitleLabel.setObjectName("tileSubtitle")
        self.subtitleLabel.setWordWrap(True)

        self.footerRow = QtWidgets.QHBoxLayout()
        self.footerRow.setContentsMargins(0, 4, 0, 0)
        self.footerRow.setSpacing(8)

        self.accentDot = QtWidgets.QLabel()
        self.accentDot.setObjectName("tileAccentDot")
        self.accentDot.setFixedSize(8, 8)

        self.footerHint = QtWidgets.QLabel("")
        self.footerHint.setObjectName("tileFooterHint")

        self.footerRow.addWidget(self.accentDot, 0, QtCore.Qt.AlignVCenter)
        self.footerRow.addWidget(self.footerHint, 0, QtCore.Qt.AlignVCenter)
        self.footerRow.addStretch(1)

        self.layout.addLayout(self.topRow)
        self.layout.addStretch(1)
        self.layout.addWidget(self.titleLabel)
        self.layout.addWidget(self.subtitleLabel)
        self.layout.addLayout(self.footerRow)

        self._refresh_style()

    def _build_icon_pixmap(self, icon_path):
        size = self.iconCard.size()
        icon = QtGui.QIcon(icon_path)
        if not icon.isNull():
            return icon.pixmap(size)

        pixmap = QtGui.QPixmap(size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setBrush(QtGui.QColor(self._accent))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(pixmap.rect(), 22, 22)
        painter.end()
        return pixmap

    def _refresh_style(self):
        border = "rgba(255, 255, 255, 0.34)" if self._hovered else "rgba(255, 255, 255, 0.18)"
        gloss = "rgba(255, 255, 255, 0.18)" if self._hovered else "rgba(255, 255, 255, 0.10)"
        badge_bg = QtGui.QColor(self._accent)
        badge_bg.setAlpha(52 if self._hovered else 38)

        self.setStyleSheet(
            f"""
            QFrame#tileButton {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.92),
                    stop: 0.5 rgba(252, 253, 255, 0.90),
                    stop: 1 rgba(244, 248, 255, 0.88)
                );
                border: 1px solid rgba(215, 226, 242, 0.92);
                border-radius: 24px;
            }}
            QLabel#tileIcon {{
                border-radius: 18px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.98),
                    stop: 1 rgba(245, 248, 255, 0.95)
                );
                border: 1px solid rgba(220, 230, 244, 0.95);
            }}
            QLabel#tileBadge {{
                min-width: 68px;
                padding: 4px 8px;
                border-radius: 10px;
                background: {badge_bg.name(QtGui.QColor.HexArgb)};
                color: #ffffff;
                font-size: 9px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QLabel#tileTitle {{
                color: #223754;
                font-size: {"22px" if self._large else "16px"};
                font-weight: 700;
            }}
            QLabel#tileSubtitle {{
                color: #7286a3;
                font-size: 11px;
                line-height: 1.55;
            }}
            QLabel#tileAccentDot {{
                border-radius: 4px;
                background: {self._accent};
                border: 1px solid {gloss};
            }}
            QLabel#tileFooterHint {{
                color: #8a9db8;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.4px;
            }}
            """
        )

    def enterEvent(self, event):
        self._hovered = True
        self._refresh_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._refresh_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SurfaceFrame(QtWidgets.QFrame):
    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.setObjectName("surfaceFrame")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 12)
        shadow.setColor(QtGui.QColor(5, 10, 25, 80))
        self.setGraphicsEffect(shadow)

        self.rootLayout = QtWidgets.QVBoxLayout(self)
        self.rootLayout.setContentsMargins(22, 20, 22, 22)
        self.rootLayout.setSpacing(16)

        if title:
            header = QtWidgets.QVBoxLayout()
            header.setSpacing(4)

            self.titleLabel = QtWidgets.QLabel(title)
            self.titleLabel.setObjectName("surfaceTitle")
            header.addWidget(self.titleLabel)

            if subtitle:
                self.subtitleLabel = QtWidgets.QLabel(subtitle)
                self.subtitleLabel.setObjectName("surfaceSubtitle")
                self.subtitleLabel.setWordWrap(True)
                header.addWidget(self.subtitleLabel)

            self.rootLayout.addLayout(header)


class SectionHeader(QtWidgets.QWidget):
    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QtWidgets.QLabel(subtitle)
            subtitle_label.setObjectName("sectionSubtitle")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)


class StatCard(QtWidgets.QFrame):
    def __init__(self, label, value, tone="cool", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setProperty("tone", tone)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.label = QtWidgets.QLabel(label)
        self.label.setObjectName("statLabel")
        self.value = QtWidgets.QLabel(value)
        self.value.setObjectName("statValue")

        layout.addWidget(self.label)
        layout.addWidget(self.value)


class SideStatusCard(QtWidgets.QFrame):
    def __init__(self, icon_kind, title, value, parent=None):
        super().__init__(parent)
        self.setObjectName("sideStatusCard")
        self._icon_kind = icon_kind

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setObjectName("sideStatusIcon")
        self.iconLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.iconLabel.setFixedSize(34, 34)
        self.iconLabel.setPixmap(self._build_icon_pixmap())

        self.titleLabel = QtWidgets.QLabel(title)
        self.titleLabel.setObjectName("sideStatusTitle")
        self.titleLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.valueLabel = QtWidgets.QLabel(value)
        self.valueLabel.setObjectName("sideStatusValue")
        self.valueLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.valueLabel.setWordWrap(True)

        layout.addWidget(self.iconLabel, 0, QtCore.Qt.AlignHCenter)
        layout.addWidget(self.titleLabel)
        layout.addWidget(self.valueLabel)

    def _build_icon_pixmap(self):
        size = 34
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtGui.QColor("#4d7cff"))
        pen.setWidth(2)
        painter.setPen(pen)

        if self._icon_kind == "weather":
            painter.setBrush(QtGui.QColor("#ffd54f"))
            painter.drawEllipse(8, 6, 12, 12)
            painter.setBrush(QtGui.QColor("#ffffff"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#bcd0f0"), 1.5))
            painter.drawEllipse(12, 15, 14, 9)
            painter.drawEllipse(7, 17, 11, 8)
            painter.drawEllipse(18, 17, 9, 7)
        else:
            painter.setBrush(QtGui.QColor("#4d7cff"))
            path = QtGui.QPainterPath()
            path.moveTo(17, 5)
            path.cubicTo(10, 5, 7, 11, 7, 16)
            path.cubicTo(7, 23, 15, 28, 17, 30)
            path.cubicTo(19, 28, 27, 23, 27, 16)
            path.cubicTo(27, 11, 24, 5, 17, 5)
            painter.drawPath(path)
            painter.setBrush(QtGui.QColor("#ffffff"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(13, 11, 8, 8)

        painter.end()
        return pixmap


class Ui_MainWindow(object):
    def _build_home_weather_pixmap(self, size=56):
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(QtCore.Qt.NoPen)

        cloud_color = QtGui.QColor(255, 255, 255, 230)
        shadow_color = QtGui.QColor(163, 191, 232, 120)

        painter.setBrush(shadow_color)
        painter.drawEllipse(14, 28, 28, 16)
        painter.drawEllipse(24, 24, 22, 14)

        painter.setBrush(cloud_color)
        painter.drawEllipse(12, 18, 18, 18)
        painter.drawEllipse(22, 12, 22, 22)
        painter.drawEllipse(36, 18, 14, 14)
        painter.drawRoundedRect(14, 24, 34, 14, 7, 7)
        painter.end()
        return pixmap

    def _build_forecast_card(self, day_text, value_text):
        card = QtWidgets.QFrame()
        card.setObjectName("posterForecastCard")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        day_label = QtWidgets.QLabel(day_text)
        day_label.setObjectName("posterForecastDay")
        value_label = QtWidgets.QLabel(value_text)
        value_label.setObjectName("posterForecastValue")
        value_label.setWordWrap(True)

        layout.addWidget(day_label)
        layout.addWidget(value_label)
        return card, day_label, value_label

    def setupUI(self, MainWindow):
        MainWindow.resize(1360, 860)
        MainWindow.setMinimumSize(1120, 760)
        apply_branding(MainWindow, APP_TITLE)

        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        MainWindow.setCentralWidget(self.centralWidget)

        self.rootLayout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.rootLayout.setContentsMargins(22, 22, 22, 22)
        self.rootLayout.setSpacing(0)

        self.appShell = QtWidgets.QFrame()
        self.appShell.setObjectName("appShell")
        self.shellLayout = QtWidgets.QHBoxLayout(self.appShell)
        self.shellLayout.setContentsMargins(0, 0, 0, 0)
        self.shellLayout.setSpacing(0)
        self.rootLayout.addWidget(self.appShell)

        shellShadow = QtWidgets.QGraphicsDropShadowEffect(self.appShell)
        shellShadow.setBlurRadius(48)
        shellShadow.setOffset(0, 22)
        shellShadow.setColor(QtGui.QColor(5, 10, 25, 110))
        self.appShell.setGraphicsEffect(shellShadow)

        self.navRail = QtWidgets.QFrame()
        self.navRail.setObjectName("navRail")
        self.navRail.setFixedWidth(116)
        navLayout = QtWidgets.QVBoxLayout(self.navRail)
        navLayout.setContentsMargins(18, 20, 18, 20)
        navLayout.setSpacing(10)

        self.appBadge = QtWidgets.QPushButton()
        self.appBadge.setObjectName("appBadge")
        self.appBadge.setCursor(QtCore.Qt.PointingHandCursor)
        self.appBadge.setFixedSize(56, 56)
        self.appBadge.setIcon(QtGui.QIcon(self._build_sidebar_logo()))
        self.appBadge.setIconSize(QtCore.QSize(56, 56))

        self.navTitle = QtWidgets.QPushButton("主页")
        self.navTitle.setObjectName("navTitle")
        self.navTitle.setCursor(QtCore.Qt.PointingHandCursor)

        self.navSubTitle = QtWidgets.QPushButton("桌面端")
        self.navSubTitle.setObjectName("navSubTitle")
        self.navSubTitle.setCursor(QtCore.Qt.PointingHandCursor)

        navLayout.addWidget(self.appBadge, 0, QtCore.Qt.AlignHCenter)
        navLayout.addWidget(self.navTitle)
        navLayout.addWidget(self.navSubTitle)
        navLayout.addSpacing(10)

        self.navDivider = QtWidgets.QFrame()
        self.navDivider.setObjectName("navDivider")
        self.navDivider.setFixedHeight(1)
        navLayout.addWidget(self.navDivider)

        self.navDot1 = QtWidgets.QLabel()
        self.navDot1.setObjectName("navDotActive")
        self.navDot1.setFixedSize(10, 10)
        self.navDot2 = QtWidgets.QLabel()
        self.navDot2.setObjectName("navDot")
        self.navDot2.setFixedSize(10, 10)
        self.navDot3 = QtWidgets.QLabel()
        self.navDot3.setObjectName("navDot")
        self.navDot3.setFixedSize(10, 10)

        navLayout.addSpacing(6)
        navLayout.addWidget(self.navDot1, 0, QtCore.Qt.AlignHCenter)
        navLayout.addWidget(self.navDot2, 0, QtCore.Qt.AlignHCenter)
        navLayout.addWidget(self.navDot3, 0, QtCore.Qt.AlignHCenter)
        navLayout.addSpacing(10)

        self.weatherCard = SideStatusCard("weather", "天气", "天气获取中")
        self.gpsCard = SideStatusCard("gps", "定位", "定位中")
        navLayout.addWidget(self.weatherCard)
        navLayout.addWidget(self.gpsCard)
        navLayout.addStretch(1)

        self.navHint = QtWidgets.QLabel("")
        self.navHint.setObjectName("navHint")
        self.navHint.setAlignment(QtCore.Qt.AlignCenter)
        navLayout.addWidget(self.navHint)

        self.shellLayout.addWidget(self.navRail)

        self.contentFrame = QtWidgets.QFrame()
        self.contentFrame.setObjectName("contentFrame")
        self.contentLayout = QtWidgets.QVBoxLayout(self.contentFrame)
        self.contentLayout.setContentsMargins(18, 14, 18, 18)
        self.contentLayout.setSpacing(12)

        self.topHero = QtWidgets.QFrame()
        self.topHero.setObjectName("topHero")
        self.topHero.setMinimumHeight(100)
        heroLayout = QtWidgets.QHBoxLayout(self.topHero)
        heroLayout.setContentsMargins(24, 14, 24, 14)
        heroLayout.setSpacing(18)

        heroTextLayout = QtWidgets.QVBoxLayout()
        heroTextLayout.setSpacing(4)

        self.heroTag = QtWidgets.QLabel("")
        self.heroTag.setObjectName("heroTag")

        self.heroTitle = QtWidgets.QLabel("路面缺陷检测系统")
        self.heroTitle.setObjectName("heroTitle")

        self.heroDesc = QtWidgets.QLabel("")
        self.heroDesc.setObjectName("heroDesc")
        self.heroDesc.setWordWrap(True)

        heroTextLayout.addWidget(self.heroTag, 0, QtCore.Qt.AlignLeft)
        heroTextLayout.addWidget(self.heroTitle)
        heroTextLayout.addWidget(self.heroDesc)

        heroMetaLayout = QtWidgets.QVBoxLayout()
        heroMetaLayout.setSpacing(8)

        self.heroMode = QtWidgets.QLabel("")
        self.heroMode.setObjectName("heroMode")

        # self.heroModel = QtWidgets.QLabel("模型：等待加载")
        # self.heroModel.setObjectName("heroModel")

        heroMetaLayout.addWidget(self.heroMode, 0, QtCore.Qt.AlignRight)
        # heroMetaLayout.addWidget(self.heroModel, 0, QtCore.Qt.AlignRight)
        heroMetaLayout.addStretch(1)

        heroLayout.addLayout(heroTextLayout, 1)
        heroLayout.addLayout(heroMetaLayout)

        self.contentLayout.addWidget(self.topHero, 0)

        self.pageHost = QtWidgets.QFrame()
        self.pageHost.setObjectName("pageHost")
        pageHostLayout = QtWidgets.QVBoxLayout(self.pageHost)
        pageHostLayout.setContentsMargins(0, 0, 0, 0)
        pageHostLayout.setSpacing(0)

        self.stackedWidget = QtWidgets.QStackedWidget()
        self.stackedWidget.setObjectName("stackedWidget")
        pageHostLayout.addWidget(self.stackedWidget)
        self.contentLayout.addWidget(self.pageHost, 1)

        self.shellLayout.addWidget(self.contentFrame, 1)

        self._build_home_page()
        self._build_detect_page()
        self._build_manager_page()
        self._build_ai_page()
        self._build_setting_page()
        self._build_crack_page()
        self._build_crack_picker_page()

        self.stackedWidget.setCurrentWidget(self.page_home)
        self._apply_style(MainWindow)

    def _build_home_page(self):
        self.page_home = QtWidgets.QWidget()
        self.page_home.setObjectName("homePage")
        homeLayout = QtWidgets.QVBoxLayout(self.page_home)
        homeLayout.setContentsMargins(0, 0, 0, 0)
        homeLayout.setSpacing(30)

        topLayout = QtWidgets.QHBoxLayout()
        topLayout.setSpacing(16)

        self.homePoster = QtWidgets.QFrame()
        self.homePoster.setObjectName("homePoster")
        self.homePoster.setFixedHeight(208)
        posterLayout = QtWidgets.QVBoxLayout(self.homePoster)
        posterLayout.setContentsMargins(22, 16, 22, 18)
        posterLayout.setSpacing(14)

        posterBodyRow = QtWidgets.QHBoxLayout()
        posterBodyRow.setSpacing(18)

        posterCurrentWrap = QtWidgets.QVBoxLayout()
        posterCurrentWrap.setSpacing(14)

        self.posterWeatherIcon = QtWidgets.QLabel()
        self.posterWeatherIcon.setObjectName("posterWeatherIcon")
        self.posterWeatherIcon.setFixedSize(64, 64)
        self.posterWeatherIcon.setAlignment(QtCore.Qt.AlignCenter)
        self.posterWeatherIcon.setPixmap(self._build_home_weather_pixmap())

        posterTextLayout = QtWidgets.QVBoxLayout()
        posterTextLayout.setSpacing(8)

        self.posterEyebrow = QtWidgets.QLabel("天气概览")
        self.posterEyebrow.setObjectName("posterEyebrow")
        self.posterTitle = QtWidgets.QLabel("天气获取中")
        self.posterTitle.setObjectName("posterTitle")
        self.posterTitle.setWordWrap(False)

        posterTextLayout.addWidget(self.posterEyebrow, 0, QtCore.Qt.AlignLeft)
        posterTextLayout.addWidget(self.posterTitle, 0, QtCore.Qt.AlignLeft)
        posterTextLayout.addStretch(1)

        posterCurrentTop = QtWidgets.QHBoxLayout()
        posterCurrentTop.setSpacing(18)
        posterCurrentTop.addWidget(self.posterWeatherIcon, 0, QtCore.Qt.AlignTop)
        posterCurrentTop.addLayout(posterTextLayout, 1)

        self.posterNote = QtWidgets.QLabel("正在同步当前位置与天气信息。")
        self.posterNote.setObjectName("posterNote")
        self.posterNote.setWordWrap(True)
        self.posterNote.setMinimumHeight(44)

        self.posterForecast1, self.posterForecastDay1, self.posterForecastValue1 = self._build_forecast_card("明天", "天气获取中")
        self.posterForecast2, self.posterForecastDay2, self.posterForecastValue2 = self._build_forecast_card("后天", "天气获取中")
        forecastColumn = QtWidgets.QVBoxLayout()
        forecastColumn.setSpacing(14)
        forecastColumn.addWidget(self.posterForecast1)
        forecastColumn.addWidget(self.posterForecast2)
        forecastColumn.addStretch(1)

        posterCurrentWrap.addLayout(posterCurrentTop)
        posterCurrentWrap.addWidget(self.posterNote, 0, QtCore.Qt.AlignLeft)
        posterCurrentWrap.addStretch(1)

        posterBodyRow.addLayout(posterCurrentWrap, 3)
        posterBodyRow.addLayout(forecastColumn, 2)

        posterLayout.addLayout(posterBodyRow)
        posterLayout.addStretch(1)

        rightColumn = QtWidgets.QVBoxLayout()
        rightColumn.setSpacing(16)

        self.homeInfoCard = QtWidgets.QFrame()
        self.homeInfoCard.setObjectName("homeInfoCard")
        infoLayout = QtWidgets.QVBoxLayout(self.homeInfoCard)
        infoLayout.setContentsMargins(20, 18, 20, 18)
        infoLayout.setSpacing(6)

        self.homeClock = QtWidgets.QLabel("00 : 00 : 00")
        self.homeClock.setObjectName("homeClock")
        self.homeDate = QtWidgets.QLabel("当前位置")
        self.homeDate.setObjectName("homeDate")
        self.homeHint = QtWidgets.QLabel("")
        self.homeHint.setObjectName("homeHint")
        self.homeHint.setWordWrap(True)

        infoLayout.addStretch(1)
        infoLayout.addWidget(self.homeClock)
        infoLayout.addWidget(self.homeDate)
        infoLayout.addWidget(self.homeHint)

        statGrid = QtWidgets.QHBoxLayout()
        statGrid.setSpacing(14)
        self.statModel = StatCard("当前模型", "YOLO", tone="cool")
        self.statConf = StatCard("置信度", "0.60", tone="warm")
        self.statNms = StatCard("NMS", "0.45", tone="violet")
        statGrid.addWidget(self.statModel, 1)
        statGrid.addWidget(self.statConf, 1)
        statGrid.addWidget(self.statNms, 1)

        rightColumn.addWidget(self.homeInfoCard)
        rightColumn.addLayout(statGrid)
        rightColumn.addStretch(1)

        topLayout.addWidget(self.homePoster, 3, QtCore.Qt.AlignTop)
        topLayout.addLayout(rightColumn, 2)
        homeLayout.addLayout(topLayout)

        tileGrid = QtWidgets.QGridLayout()
        tileGrid.setHorizontalSpacing(20)
        tileGrid.setVerticalSpacing(42)
        tileGrid.setColumnStretch(0, 1)
        tileGrid.setColumnStretch(1, 1)
        tileGrid.setColumnStretch(2, 1)
        tileGrid.setColumnStretch(3, 1)

        self.btnVideoOD = TileButton(
            "视频检测",
            "载入本地视频流并展示连续推理结果与运行日志。",
            "icon/kaishi.png",
            accent="#1db98a",
            min_height=130,
        )
        self.btnRealTimOD = TileButton(
            "实时检测",
            "加载视频组件并实时缩放原画面与检测输出区域。",
            "icon/xunhuan.png",
            accent="#4d7cff",
            min_height=130,
        )
        self.btn3 = TileButton("裂缝分析", "对路面裂缝图像进行分割并调用 AI 生成结果分析。", "icon/fenzhiqi.png", accent="#8b5cf6", min_height=130)
        self.btn4 = TileButton("文件管理", "浏览工程素材、检测输出和导出结果文件。", "icon/wenbenchuli.png", accent="#4d7cff", min_height=130)
        self.btn5 = TileButton("智能AI", "围绕检测结果进行解释、提问与场景化问答。", "icon/API.png", accent="#ff7aa2", min_height=130)
        self.btn6 = TileButton("系统设置", "切换模型并调整置信度与 NMS 参数。", "icon/shezhi.png", accent="#7c55f1", min_height=130)

        # 路面缺陷介绍卡片，占据 row0 col0-1
        self.infoCard = QtWidgets.QFrame()
        self.infoCard.setObjectName("infoCard")
        self.infoCard.setMinimumWidth(0)
        self.infoCard.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        infoCardGrid = QtWidgets.QGridLayout(self.infoCard)
        infoCardGrid.setContentsMargins(0, 0, 0, 0)
        infoCardGrid.setSpacing(0)

        self.infoImage = QtWidgets.QLabel()
        self.infoImage.setObjectName("infoImage")
        self.infoImage.setScaledContents(False)
        self.infoImage.setAlignment(QtCore.Qt.AlignCenter)
        self.infoImage.setMinimumSize(0, 0)
        self.infoImage.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self._infoPixmap = QtGui.QPixmap("icon/q1.png")
        if not self._infoPixmap.isNull():
            self.infoImage.setPixmap(self._infoPixmap)

        infoTextWrap = QtWidgets.QFrame()
        infoTextWrap.setObjectName("infoTextWrap")
        infoTextWrap.setMinimumWidth(380)
        infoTextLayout = QtWidgets.QVBoxLayout(infoTextWrap)
        infoTextLayout.setContentsMargins(24, 20, 28, 20)
        infoTextLayout.setSpacing(10)
        self.infoTitle = QtWidgets.QLabel("路面缺陷检测")
        self.infoTitle.setObjectName("infoTitle")
        self.infoTitle.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.infoDesc = QtWidgets.QLabel("系统支持裂缝、坑槽、车辙等多类路面缺陷的智能识别与分析，结合深度学习模型与 AI 问答，为道路养护提供高效决策支持。")
        self.infoDesc.setObjectName("infoDesc")
        self.infoDesc.setWordWrap(True)
        self.infoDesc.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.infoDesc.setTextFormat(QtCore.Qt.RichText)
        infoTextLayout.addStretch(1)
        infoTextLayout.addWidget(self.infoTitle)
        infoTextLayout.addWidget(self.infoDesc)
        infoTextLayout.addStretch(1)

        infoCardGrid.addWidget(self.infoImage, 0, 0)
        infoCardGrid.addWidget(infoTextWrap, 0, 0, QtCore.Qt.AlignRight)
        self.infoCard.resizeEvent = self._resizeInfoImage

        # 第0行: col0,col1=路面缺陷介绍卡片; col2=视频检测, col3=实时检测
        tileGrid.addWidget(self.infoCard, 0, 0, 1, 2)
        tileGrid.addWidget(self.btnVideoOD, 0, 2)
        tileGrid.addWidget(self.btnRealTimOD, 0, 3)
        # 第1行: col0=裂缝分析, col1=文件管理, col2=智能问答, col3=系统设置
        tileGrid.addWidget(self.btn3, 1, 0)
        tileGrid.addWidget(self.btn4, 1, 1)
        tileGrid.addWidget(self.btn5, 1, 2)
        tileGrid.addWidget(self.btn6, 1, 3)

        homeLayout.addLayout(tileGrid)
        homeLayout.addStretch(10)

        self.stackedWidget.addWidget(self.page_home)

    def _build_detect_page(self):
        self.page_detect = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_detect)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        contentLayout = QtWidgets.QHBoxLayout()
        contentLayout.setSpacing(14)

        previewSurface = SurfaceFrame("实时画面", "支持视频文件与摄像头两种输入模式，可拖动调整左右画面比例。")
        self.label_ori_video = self._build_preview_label("原始视频 / 摄像头画面")
        self.label_treated = self._build_preview_label("检测结果输出")
        self.detectPreviewSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.detectPreviewSplitter.setObjectName("detectPreviewSplitter")
        self.detectPreviewSplitter.setChildrenCollapsible(False)
        self.detectPreviewSplitter.addWidget(self.label_ori_video)
        self.detectPreviewSplitter.addWidget(self.label_treated)
        self.detectPreviewSplitter.setStretchFactor(0, 1)
        self.detectPreviewSplitter.setStretchFactor(1, 1)
        self.detectPreviewSplitter.setSizes([660, 800])
        previewSurface.rootLayout.addWidget(self.detectPreviewSplitter, 3)

        previewSurface.rootLayout.addStretch(1)
        resultTitle = QtWidgets.QLabel("输出结果")
        resultTitle.setObjectName("blockTitle")
        previewSurface.rootLayout.addWidget(resultTitle)
        self.textLog = QtWidgets.QTextBrowser()
        self.textLog.setObjectName("softTextBrowser")
        self.textLog.setPlaceholderText("当前帧检测到的目标会显示在这里。")
        self.textLog.setMinimumHeight(24)
        self.textLog.setMaximumHeight(88)
        previewSurface.rootLayout.addWidget(self.textLog, 0)

        sideSurface = SurfaceFrame("操作面板", "")
        self.videoBtn = self._build_pill_button("选择视频", primary=False)
        self.camBtn = self._build_pill_button("开始检测", primary=True)
        self.stopBtn = self._build_pill_button("停止", primary=False, danger=True)
        for widget in (self.videoBtn, self.camBtn, self.stopBtn):
            widget.setMinimumHeight(48)

        self.detectModeBadge = QtWidgets.QLabel("模式 · 待机")
        self.detectModeBadge.setObjectName("miniBadge")

        modeHint = QtWidgets.QLabel("进入页面后可继续从首页切换视频检测或实时检测模式。")
        modeHint.setObjectName("infoHint")
        modeHint.setWordWrap(True)

        sideSurface.rootLayout.addWidget(self.detectModeBadge, 0, QtCore.Qt.AlignLeft)
        sideSurface.rootLayout.addWidget(modeHint)
        sideSurface.rootLayout.addWidget(self.videoBtn)
        sideSurface.rootLayout.addWidget(self.camBtn)
        sideSurface.rootLayout.addWidget(self.stopBtn)
        sideSurface.rootLayout.addStretch(1)

        contentLayout.addWidget(previewSurface, 5)
        contentLayout.addWidget(sideSurface, 1)
        layout.addLayout(contentLayout, 1)

        self.stackedWidget.addWidget(self.page_detect)

    def _build_manager_page(self):
        self.page_manager = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_manager)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)

        treeSurface = SurfaceFrame("目录树")
        self.treeView = QtWidgets.QTreeView()
        self.treeView.setObjectName("softTree")
        treeSurface.rootLayout.addWidget(self.treeView, 1)

        listSurface = SurfaceFrame("内容区")
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setObjectName("softList")
        self.listWidget.setViewMode(QtWidgets.QListView.IconMode)
        self.listWidget.setIconSize(QtCore.QSize(92, 92))
        self.listWidget.setResizeMode(QtWidgets.QListView.Adjust)
        self.listWidget.setSpacing(16)
        listSurface.rootLayout.addWidget(self.listWidget, 1)

        body.addWidget(treeSurface, 2)
        body.addWidget(listSurface, 5)
        layout.addLayout(body, 1)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(12)
        self.btnDelete = self._build_pill_button("删除", primary=False, danger=True)
        self.btnExport = self._build_pill_button("导出", primary=False)
        self.btnRefresh = self._build_pill_button("刷新", primary=True)
        actions.addWidget(self.btnDelete)
        actions.addWidget(self.btnExport)
        actions.addWidget(self.btnRefresh)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.stackedWidget.addWidget(self.page_manager)

    def _build_ai_page(self):
        self.page_ai = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_ai)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        chatSurface = SurfaceFrame("对话区")
        self.text_chat = QtWidgets.QTextBrowser()
        self.text_chat.setObjectName("softTextBrowser")
        self.text_chat.setPlaceholderText("输入检测相关问题，AI 回复会展示在这里。")
        chatSurface.rootLayout.addWidget(self.text_chat, 1)

        inputRow = QtWidgets.QHBoxLayout()
        inputRow.setSpacing(12)
        self.edit_ai_input = QtWidgets.QLineEdit()
        self.edit_ai_input.setObjectName("softLineEdit")
        self.edit_ai_input.setPlaceholderText("输入你的问题...")
        self.edit_ai_input.setMinimumHeight(48)
        self.btn_send_ai = self._build_pill_button("发送", primary=True)
        self.btn_send_ai.setFixedWidth(118)
        inputRow.addWidget(self.edit_ai_input, 1)
        inputRow.addWidget(self.btn_send_ai)
        chatSurface.rootLayout.addLayout(inputRow)
        layout.addWidget(chatSurface, 1)

        self.stackedWidget.addWidget(self.page_ai)

    def _build_setting_page(self):
        self.page_setting = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_setting)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        centerRow = QtWidgets.QHBoxLayout()
        centerRow.setSpacing(14)

        inferSurface = SurfaceFrame("推理配置", "参数修改会立即同步到当前会话。")

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(26)
        grid.setVerticalSpacing(22)

        grid.addWidget(self._build_field_label("版本信息"), 0, 0)
        self.labelVersion = QtWidgets.QLabel("v1.0.0")
        self.labelVersion.setObjectName("fieldValue")
        grid.addWidget(self.labelVersion, 0, 1)

        grid.addWidget(self._build_field_label("模型选择"), 1, 0)
        self.comboModel = QtWidgets.QComboBox()
        self.comboModel.setObjectName("softCombo")
        self.comboModel.setMinimumHeight(44)
        self.comboModel.addItems(["yolov8n.pt", "yolo11n.pt"])
        grid.addWidget(self.comboModel, 1, 1)

        grid.addWidget(self._build_field_label("输入尺寸"), 2, 0)
        self.comboImgSize = QtWidgets.QComboBox()
        self.comboImgSize.setObjectName("softCombo")
        self.comboImgSize.setMinimumHeight(44)
        self.comboImgSize.addItems(["320", "416", "640", "1280"])
        self.comboImgSize.setCurrentText("640")
        grid.addWidget(self.comboImgSize, 2, 1)

        grid.addWidget(self._build_field_label("置信度"), 3, 0)
        confRow = QtWidgets.QHBoxLayout()
        confRow.setSpacing(12)
        self.sliderConf = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sliderConf.setRange(1, 100)
        self.sliderConf.setValue(60)
        self.labelConf = QtWidgets.QLabel("0.60")
        self.labelConf.setObjectName("valueBadge")
        confRow.addWidget(self.sliderConf, 1)
        confRow.addWidget(self.labelConf)
        confWrap = QtWidgets.QWidget()
        confWrap.setLayout(confRow)
        grid.addWidget(confWrap, 3, 1)

        grid.addWidget(self._build_field_label("NMS"), 4, 0)
        nmsRow = QtWidgets.QHBoxLayout()
        nmsRow.setSpacing(12)
        self.sliderNMS = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sliderNMS.setRange(1, 100)
        self.sliderNMS.setValue(45)
        self.labelNMS = QtWidgets.QLabel("0.45")
        self.labelNMS.setObjectName("valueBadge")
        nmsRow.addWidget(self.sliderNMS, 1)
        nmsRow.addWidget(self.labelNMS)
        nmsWrap = QtWidgets.QWidget()
        nmsWrap.setLayout(nmsRow)
        grid.addWidget(nmsWrap, 4, 1)

        inferSurface.rootLayout.addLayout(grid)

        aiSurface = SurfaceFrame("AI 与 API 配置", "修改后即时生效，无需重启。")
        aiGrid = QtWidgets.QGridLayout()
        aiGrid.setHorizontalSpacing(26)
        aiGrid.setVerticalSpacing(22)

        aiGrid.addWidget(self._build_field_label("AI 模型"), 0, 0)
        self.comboAiModel = QtWidgets.QComboBox()
        self.comboAiModel.setObjectName("softCombo")
        self.comboAiModel.setMinimumHeight(44)
        self.comboAiModel.addItems(["qwen-vl-plus", "qwen-vl-max", "qwen-plus", "qwen-max"])
        self.comboAiModel.setCurrentText("qwen-vl-plus")
        aiGrid.addWidget(self.comboAiModel, 0, 1)

        aiGrid.addWidget(self._build_field_label("API Key"), 1, 0)
        self.editApiKey = QtWidgets.QLineEdit()
        self.editApiKey.setObjectName("softLineEdit")
        self.editApiKey.setMinimumHeight(44)
        self.editApiKey.setEchoMode(QtWidgets.QLineEdit.Password)
        self.editApiKey.setPlaceholderText("输入 Qwen API Key")
        self.btnToggleKey = QtWidgets.QPushButton("👁")
        self.btnToggleKey.setFixedWidth(44)
        self.btnToggleKey.setMinimumHeight(44)
        self.btnToggleKey.setObjectName("pillButton")
        self.btnToggleKey.setCursor(QtCore.Qt.PointingHandCursor)
        keyRow = QtWidgets.QHBoxLayout()
        keyRow.setSpacing(8)
        keyRow.addWidget(self.editApiKey, 1)
        keyRow.addWidget(self.btnToggleKey)
        keyWrap = QtWidgets.QWidget()
        keyWrap.setLayout(keyRow)
        aiGrid.addWidget(keyWrap, 1, 1)

        aiGrid.addWidget(self._build_field_label("天气城市"), 2, 0)
        self.editWeatherCity = QtWidgets.QLineEdit()
        self.editWeatherCity.setObjectName("softLineEdit")
        self.editWeatherCity.setMinimumHeight(44)
        self.editWeatherCity.setPlaceholderText("例如: Yantai")
        self.editWeatherCity.setText("Yantai")
        aiGrid.addWidget(self.editWeatherCity, 2, 1)

        aiSurface.rootLayout.addLayout(aiGrid)

        centerRow.addWidget(inferSurface, 1)
        centerRow.addWidget(aiSurface, 1)
        layout.addLayout(centerRow, 0)
        layout.addStretch(1)

        self.stackedWidget.addWidget(self.page_setting)

    def _build_crack_page(self):
        self.page_crack = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_crack)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        bodyRow = QtWidgets.QHBoxLayout()
        bodyRow.setSpacing(14)

        leftPanel = QtWidgets.QVBoxLayout()
        leftPanel.setSpacing(14)

        resultImgSurface = SurfaceFrame("结果显示")
        resultImgSurface.setMinimumHeight(560)
        resultContentRow = QtWidgets.QHBoxLayout()
        resultContentRow.setSpacing(16)

        self.label_crack_result = self._build_preview_label("选择图片后自动分割")
        self.label_crack_result.setMinimumSize(360, 520)

        self.text_crack_analysis = QtWidgets.QTextBrowser()
        self.text_crack_analysis.setObjectName("softTextBrowser")
        self.text_crack_analysis.setMinimumSize(320, 520)
        self.text_crack_analysis.setPlaceholderText("AI 分析结果将显示在这里。")

        resultContentRow.addWidget(self.label_crack_result, 3)
        resultContentRow.addWidget(self.text_crack_analysis, 2)
        resultImgSurface.rootLayout.addLayout(resultContentRow, 1)
        leftPanel.addWidget(resultImgSurface, 1)

        bodyRow.addLayout(leftPanel, 1)

        actionSurface = SurfaceFrame("操作")
        actionSurface.setFixedWidth(280)
        actionLayout = QtWidgets.QVBoxLayout()
        actionLayout.setSpacing(12)
        self.btn_select_img = self._build_pill_button("选择图片", primary=True)
        actionLayout.addWidget(self.btn_select_img)

        self.edit_ai_question = QtWidgets.QLineEdit()
        self.edit_ai_question.setObjectName("softLineEdit")
        self.edit_ai_question.setPlaceholderText("输入需要 AI 分析的问题...")
        self.edit_ai_question.setMinimumHeight(46)
        self.btn_ai_analysis = self._build_pill_button("AI 分析", primary=True)
        actionLayout.addWidget(self.edit_ai_question)
        actionLayout.addWidget(self.btn_ai_analysis)
        actionLayout.addStretch(1)
        actionSurface.rootLayout.addLayout(actionLayout)

        bodyRow.addWidget(actionSurface, 0)

        layout.addLayout(bodyRow, 1)

        self.stackedWidget.addWidget(self.page_crack)

    def _build_crack_picker_page(self):
        self.page_crack_picker = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.page_crack_picker)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        pickerSurface = SurfaceFrame("图片选择", "仅显示 icon 文件夹中的图片，点击即可开始分割分析。")
        self.iconImageList = QtWidgets.QListWidget()
        self.iconImageList.setObjectName("softList")
        self.iconImageList.setViewMode(QtWidgets.QListView.IconMode)
        self.iconImageList.setMovement(QtWidgets.QListView.Static)
        self.iconImageList.setResizeMode(QtWidgets.QListView.Adjust)
        self.iconImageList.setSpacing(18)
        self.iconImageList.setIconSize(QtCore.QSize(160, 120))
        self.iconImageList.setWordWrap(True)
        self.iconImageList.setUniformItemSizes(True)
        pickerSurface.rootLayout.addWidget(self.iconImageList, 1)

        layout.addWidget(pickerSurface, 1)
        self.stackedWidget.addWidget(self.page_crack_picker)

    def _build_pill_button(self, text, primary=False, danger=False):
        btn = QtWidgets.QPushButton(text)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.setProperty("primary", primary)
        btn.setProperty("danger", danger)
        btn.setObjectName("pillButton")
        return btn

    def _build_preview_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setMinimumSize(320, 360)
        label.setObjectName("previewLabel")
        label.setWordWrap(True)
        return label

    def _build_sidebar_logo(self):
        pixmap = QtGui.QPixmap("icon/model-Y.png")
        if pixmap.isNull():
            pixmap = QtGui.QPixmap(56, 56)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QColor("#22c55e"))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(pixmap.rect(), 18, 18)
            painter.end()
            return pixmap
        return pixmap.scaled(56, 56, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

    def _resizeInfoImage(self, event):
        if hasattr(self, '_infoPixmap') and not self._infoPixmap.isNull():
            sz = self.infoImage.size()
            scaled = self._infoPixmap.scaled(sz, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            rounded = QtGui.QPixmap(sz)
            rounded.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(rounded)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            path = QtGui.QPainterPath()
            path.addRoundedRect(QtCore.QRectF(rounded.rect()), 24, 24)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            self.infoImage.setPixmap(rounded)
        return QtWidgets.QFrame.resizeEvent(self.infoCard, event)

    def update_info_card(self, image_path=None, title="", desc=""):
        if image_path:
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                self._infoPixmap = pixmap
                if hasattr(self, "infoCard"):
                    self._resizeInfoImage(None)
        if hasattr(self, "infoTitle"):
            self.infoTitle.setText(title)
        if hasattr(self, "infoDesc"):
            self.infoDesc.setText(desc)

    def _build_field_label(self, text):
        label = QtWidgets.QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _apply_style(self, MainWindow):
        MainWindow.setStyleSheet(
            """
            QWidget#centralWidget {
                background-image: url(icon/111_blur.jpg);
                background-position: center;
                background-repeat: no-repeat;
                color: #243447;
                font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
            }
            QFrame#appShell {
                background: rgba(255, 255, 255, 0.58);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-radius: 32px;
            }
            QFrame#navRail {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.96),
                    stop: 1 rgba(243, 247, 255, 0.90)
                );
                border-top-left-radius: 32px;
                border-bottom-left-radius: 32px;
                border-right: 1px solid rgba(209, 220, 239, 0.78);
            }
            QPushButton#appBadge {
                background: rgba(243, 248, 255, 0.96);
                border: 1px solid rgba(212, 224, 243, 0.95);
                border-radius: 18px;
            }
            QPushButton#appBadge:hover {
                background: rgba(236, 245, 255, 1);
            }
            QPushButton#navTitle {
                color: #1f3b63;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1.2px;
                background: transparent;
                border: none;
                padding: 0px;
                text-align: center;
            }
            QPushButton#navSubTitle {
                color: #7b8faa;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
                padding: 0px;
                text-align: center;
            }
            QFrame#navDivider {
                background: rgba(209, 220, 239, 0.92);
                border: none;
            }
            QLabel#navDotActive {
                background: #4d7cff;
                border-radius: 5px;
            }
            QLabel#navDot {
                background: rgba(181, 198, 223, 0.92);
                border-radius: 5px;
            }
            QLabel#navHint {
                padding: 6px 10px;
                border-radius: 12px;
                background: rgba(238, 244, 255, 1);
                color: #4d7cff;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            QFrame#sideStatusCard {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(214, 224, 241, 0.88);
                border-radius: 16px;
            }
            QLabel#sideStatusIcon {
                background: rgba(243, 248, 255, 0.96);
                border: 1px solid rgba(212, 224, 243, 0.95);
                border-radius: 17px;
            }
            QLabel#sideStatusTitle {
                color: #6d84a3;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }
            QLabel#sideStatusValue {
                color: #203553;
                font-size: 11px;
                font-weight: 600;
                line-height: 1.45;
            }
            QFrame#contentFrame, QFrame#pageHost, QStackedWidget#stackedWidget {
                background: transparent;
            }
            QFrame#topHero {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.74),
                    stop: 0.55 rgba(247, 250, 255, 0.70),
                    stop: 1 rgba(239, 245, 255, 0.66)
                );
                border: 1px solid rgba(217, 228, 244, 0.78);
                border-radius: 24px;
            }
            QLabel#heroTag {
                min-width: 0px;
                max-width: 0px;
                padding: 0px;
                border-radius: 12px;
                background: transparent;
                color: transparent;
                font-size: 1px;
                font-weight: 400;
                letter-spacing: 0px;
            }
            QLabel#heroTitle {
                color: #203553;
                font-size: 30px;
                font-weight: 700;
            }
            QLabel#heroDesc {
                color: #70839d;
                font-size: 13px;
            }
            QLabel#heroMode, QLabel#heroModel, QLabel#miniBadge {
                padding: 6px 12px;
                border-radius: 12px;
                background: rgba(242, 246, 255, 0.80);
                color: #45607f;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#backHomeIcon {
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(219, 228, 242, 0.78);
                border-radius: 14px;
            }
            QFrame#homePoster {
                border-radius: 28px;
                border-image: url(icon/111_blur.jpg) 0 0 0 0 stretch stretch;
            }
            QFrame#infoCard {
                border-radius: 24px;
                border: 1px solid rgba(215, 226, 242, 0.60);
                background: #2a3a4a;
            }
            QLabel#infoImage {
                border-radius: 24px;
                background: transparent;
            }
            QFrame#infoTextWrap {
                background: transparent;
                border: none;
                min-width: 330px;
                max-width: 360px;
            }
            QLabel#infoTitle {
                color: #ffffff;
                font-size: 24px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#infoDesc {
                color: rgba(255, 255, 255, 0.92);
                font-size: 13px;
                line-height: 1.7;
                background: transparent;
                min-width: 300px;
            }
            QLabel#posterEyebrow {
                color: #4d7cff;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1.2px;
            }
            QLabel#posterTitle {
                color: #ffffff;
                font-size: 34px;
                font-weight: 700;
                line-height: 1.05;
            }
            QLabel#posterNote {
                max-width: 420px;
                color: #f7fbff;
                font-size: 14px;
                line-height: 1.6;
            }
            QLabel#posterWeatherIcon {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.22);
                border-radius: 20px;
            }
            QFrame#posterForecastCard {
                background: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 16px;
            }
            QLabel#posterForecastDay {
                color: rgba(236, 245, 255, 0.82);
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            QLabel#posterForecastValue {
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                line-height: 1.45;
            }
            QFrame#homeInfoCard {
                border-image: url(icon/222.jpg) 0 0 0 0 stretch stretch;;
                background: rgba(255, 255, 255, 0.72);
                border: 1px solid rgba(219, 228, 242, 0.76);
                border-radius: 24px;
            }
            QLabel#homeClock {
                color: #ffffff;
                font-size: 30px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#homeDate {
                color: #eff6ff;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.9px;
            }
            QLabel#homeHint {
                color: #f7fbff;
                font-size: 12px;
                line-height: 1.5;
            }
            QFrame#statCard {
                background: rgba(255, 255, 255, 0.70);
                border: 1px solid rgba(219, 228, 242, 0.74);
                border-radius: 20px;
            }
            QFrame#statCard[tone="warm"] {
                background: rgba(255, 250, 244, 0.74);
            }
            QFrame#statCard[tone="violet"] {
                background: rgba(247, 243, 255, 0.74);
            }
            QLabel#statLabel {
                color: #7a8ea8;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.7px;
            }
            QLabel#statValue {
                color: #203553;
                font-size: 18px;
                font-weight: 700;
            }
            QFrame#surfaceFrame {
                background: rgba(255, 255, 255, 0.66);
                border: 1px solid rgba(219, 228, 242, 0.74);
                border-radius: 24px;
            }
            QLabel#surfaceTitle, QLabel#sectionTitle {
                color: #203553;
                font-size: 19px;
                font-weight: 700;
            }
            QLabel#surfaceSubtitle, QLabel#sectionSubtitle {
                color: #768aa5;
                font-size: 12px;
                line-height: 1.5;
            }
            QLabel#blockTitle {
                color: #45607f;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#previewLabel {
                background: rgba(248, 251, 255, 0.98);
                border: 1px dashed rgba(194, 209, 231, 0.92);
                border-radius: 18px;
                color: #8aa0bf;
                font-size: 14px;
                padding: 10px;
            }
            QSplitter#detectPreviewSplitter::handle {
                background: rgba(220, 229, 243, 0.95);
                width: 10px;
                margin: 10px 0;
                border-radius: 5px;
            }
            QSplitter#detectPreviewSplitter::handle:hover {
                background: rgba(160, 184, 226, 0.95);
            }
            QTextBrowser#softTextBrowser, QLineEdit#softLineEdit, QComboBox#softCombo,
            QTreeView#softTree, QListWidget#softList {
                background: rgba(252, 253, 255, 0.98);
                border: 1px solid rgba(219, 228, 242, 0.98);
                border-radius: 16px;
                color: #243447;
                selection-background-color: rgba(77, 124, 255, 0.14);
                selection-color: #203553;
            }
            QTextBrowser#softTextBrowser, QTreeView#softTree, QListWidget#softList {
                padding: 10px;
            }
            QTreeView#softTree::item, QListWidget#softList::item {
                padding: 6px;
            }
            QLineEdit#softLineEdit {
                padding: 0 14px;
                font-size: 14px;
            }
            QComboBox#softCombo {
                padding: 0 12px;
            }
            QComboBox#softCombo::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                background: rgba(255, 255, 255, 1);
                color: #243447;
                border: 1px solid rgba(219, 228, 242, 1);
            }
            QPushButton#pillButton {
                background: rgba(255, 255, 255, 0.98);
                color: #203553;
                border: 1px solid rgba(213, 224, 240, 0.96);
                border-radius: 14px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#pillButton:hover {
                background: rgba(246, 249, 255, 1);
                border-color: rgba(162, 187, 229, 0.92);
            }
            QPushButton#pillButton[primary="true"] {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #4d7cff,
                    stop: 1 #22c55e
                );
                color: white;
                border: none;
            }
            QPushButton#pillButton[primary="true"]:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #3d69f2,
                    stop: 1 #18b26b
                );
            }
            QPushButton#pillButton[danger="true"] {
                color: #b45309;
                background: rgba(255, 247, 237, 1);
                border: 1px solid rgba(252, 211, 167, 0.94);
            }
            QPushButton#pillButton[danger="true"]:hover {
                background: rgba(255, 237, 213, 1);
            }
            QLabel#infoHint, QLabel#pathLabel {
                color: #70839d;
                font-size: 13px;
            }
            QLabel#fieldLabel {
                color: #415a77;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#fieldValue {
                color: #203553;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel#valueBadge {
                min-width: 56px;
                padding: 6px 10px;
                border-radius: 12px;
                background: rgba(77, 124, 255, 0.10);
                color: #4d7cff;
                font-weight: 700;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(193, 205, 226, 0.8);
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4d7cff,
                    stop: 1 #22c55e
                );
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                margin: -7px 0;
                border-radius: 9px;
                background: #ffffff;
                border: 1px solid rgba(193, 205, 226, 0.9);
            }
            QHeaderView::section {
                background: rgba(245, 249, 255, 1);
                color: #415a77;
                border: none;
                padding: 6px;
            }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(171, 188, 216, 0.78);
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
                border: none;
            }
            """
        )
