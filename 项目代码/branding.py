from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


APP_TITLE = "路面缺陷检测分析平台"
ICON_CANDIDATES = (
    Path("icon/model-Y.png"),
    Path("icon/damoxing.png"),
    Path("icon/API.png"),
    Path("icon/app_logo.png"),
    Path("icon/app_logo.jpg"),
    Path("icon/app_logo.jpeg"),
    Path("icon/app_logo.ico"),
    Path("pyqt/icon/model-Y.png"),
    Path("pyqt/icon/damoxing.png"),
    Path("pyqt/icon/API.png"),
    Path("pyqt/icon/app_logo.png"),
    Path("pyqt/icon/app_logo.jpg"),
    Path("pyqt/icon/app_logo.jpeg"),
    Path("pyqt/icon/app_logo.ico"),
)


def _build_logo_pixmap(size):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

    margin = size * 0.18
    center = QtCore.QPointF(size / 2, size / 2)
    segments = [
        ("#34A853", QtCore.QPointF(margin, margin), center),
        ("#4285F4", center, QtCore.QPointF(size - margin, size - margin)),
        ("#EA4335", QtCore.QPointF(margin, size - margin), center),
        ("#FBBC05", center, QtCore.QPointF(size - margin, margin)),
    ]

    pen = QtGui.QPen()
    pen.setWidthF(size * 0.18)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)

    for color, start, end in segments:
        pen.setColor(QtGui.QColor(color))
        painter.setPen(pen)
        painter.drawLine(start, end)

    painter.end()
    return pixmap


def create_brand_icon():
    for icon_path in ICON_CANDIDATES:
        if icon_path.exists():
            return QtGui.QIcon(str(icon_path))

    icon = QtGui.QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_build_logo_pixmap(size))
    return icon


def apply_branding(window, title=APP_TITLE):
    icon = create_brand_icon()
    window.setWindowTitle(title)
    window.setWindowIcon(icon)

    app = QtWidgets.QApplication.instance()
    if app is not None:
        app.setWindowIcon(icon)
