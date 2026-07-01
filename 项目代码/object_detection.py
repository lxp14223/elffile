from PySide6 import QtWidgets, QtCore, QtGui
import cv2, os, time
import sys
import numpy as np
import requests
import base64
from collections import deque
from datetime import datetime
from threading import Thread, Lock
from UI import Ui_MainWindow
# 不然每次YOLO处理都会输出调试信息
os.environ['YOLO_VERBOSE'] = 'False'
from ultralytics import YOLO
try:
    from rknnlite.api import RKNNLite
except ImportError:
    RKNNLite = None

RKNN_MODEL = 'yolov5s.rknn'
QUANTIZE_ON = True
OBJ_THRESH = 0.60
NMS_THRESH = 0.45
IMG_SIZE = 640

CLASSES = ('Alligator crack', 'Longitudinal crack', 'Oblique crack', 'Pothole', 'Repair', 'Transverse crack')

CLASS_NAME_MAP = {
    "Alligator crack": "鳄鱼裂缝",
    "Longitudinal crack": "纵向裂缝",
    "Oblique crack": "斜向裂缝",
    "Pothole": "坑洞",
    "Repair": "维修",
    "Transverse crack": "横向裂缝",
}

QWEN_API_KEY = "sk-edc9f9df1e3a4643b935c060ebf9f4af"
QWEN_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
QWEN_MODEL = "qwen-vl-plus"

WEATHER_DESC_MAP = {
    "sunny": "晴",
    "clear": "晴",
    "partly cloudy": "多云",
    "cloudy": "阴",
    "overcast": "阴",
    "mist": "薄雾",
    "fog": "雾",
    "patchy rain nearby": "附近有零星降雨",
    "light rain": "小雨",
    "moderate rain": "中雨",
    "heavy rain": "大雨",
    "light drizzle": "毛毛雨",
    "thundery outbreaks nearby": "附近有雷暴",
    "patchy snow nearby": "附近有零星降雪",
}


class MWindow(QtWidgets.QMainWindow):
    updateLog = QtCore.Signal(str)
    aiAnalysisResult = QtCore.Signal(str)
    locationFetched = QtCore.Signal(str, str)
    weatherFetched = QtCore.Signal(str, str, str, str, str, str)
    detectPreviewReady = QtCore.Signal(QtGui.QImage)

    def _normalize_weather_desc(self, value):
        text = (value or "").strip()
        if not text:
            return ""
        return WEATHER_DESC_MAP.get(text.lower(), text)

    def _debug_network_log(self, title, message):
        print(f"[{title}] {message}", flush=True)

    aiChatResult = QtCore.Signal(str)   # 新增
    
    def __init__(self):

        super().__init__()

        # 设置界面
        self.ui = Ui_MainWindow()
        self.ui.setupUI(self)
        self.is_video_mode = False
        self.is_camera_mode = False
        self.model = None
        self.rknn = None
        self.model_backend = None
        self.rknn_lock = Lock()
        self.video_writer = None
        self.saved_video_path = ""
        self.video_save_queue = deque(maxlen=120)
        self.fps = 0.0
        self.last_log_time = time.time()
        self.current_video_path = "video/od.mp4"
        self.load_model_list()
        self.locationFetched.connect(self._apply_location_update)
        self.weatherFetched.connect(self._apply_weather_update)
        self.detectPreviewReady.connect(self._apply_detect_preview)
        self._setup_dashboard_state()
        self._setup_home_gallery()

        # self.conf_thresh = 0.0
        # self.nms_thresh = 0.0
        self.ui.appBadge.clicked.connect(self.goto_home)
        self.ui.navTitle.clicked.connect(self.goto_home)
        self.ui.navSubTitle.clicked.connect(self.goto_home)
        # ===== 分析控制 =====
        self.ui.btn3.clicked.connect(self.goto_crack)
        self.ui.btn_select_img.clicked.connect(self.selectImage)
        self.ui.iconImageList.itemClicked.connect(self.select_icon_image)
        self.aiAnalysisResult.connect(self.displayAiResult)
        self.ui.btn_ai_analysis.clicked.connect(self.runQwenAnalysis)
        # ===== 文件控制 =====
        self.magmodel = QtWidgets.QFileSystemModel()
        self.magmodel.setRootPath(QtCore.QDir.currentPath())

        self.ui.treeView.setModel(self.magmodel)
        self.ui.treeView.setRootIndex(self.magmodel.index(QtCore.QDir.currentPath()))
        self.ui.treeView.clicked.connect(self.on_folder_clicked)
        self.ui.btnDelete.clicked.connect(self.delete_file)
        self.ui.btnExport.clicked.connect(self.export_file)
        self.ui.btnRefresh.clicked.connect(self.refresh)
        # ===== AI问答控制 =====
        self.ui.btn5.clicked.connect(self.goto_ai)
        self.aiChatResult.connect(self.displayAiChat)
        self.ui.btn_send_ai.clicked.connect(self.sendAiQuestion)
        self.ui.edit_ai_input.returnPressed.connect(self.sendAiQuestion)
        # ===== 设置控制 =====
        self.ui.btn6.clicked.connect(self.goto_setting)
        self.ui.sliderConf.valueChanged.connect(self.update_conf)
        self.ui.sliderNMS.valueChanged.connect(self.update_nms)
        self.ui.comboModel.currentIndexChanged.connect(self.change_model)
        self.ui.comboModel.currentIndexChanged.emit(
            self.ui.comboModel.currentIndex()
        )
        self.ui.comboImgSize.currentIndexChanged.connect(self.change_img_size)
        self.ui.comboAiModel.currentIndexChanged.connect(self.change_ai_model)
        self.ui.editApiKey.textChanged.connect(self.change_api_key)
        self.ui.btnToggleKey.clicked.connect(self.toggle_api_key_visible)
        self.ui.editWeatherCity.textChanged.connect(self.change_weather_city)

        # ===== 检测跳转 =====
        self.ui.btnVideoOD.clicked.connect(self.goto_detect)
        self.ui.btnRealTimOD.clicked.connect(self.goto_detect)

        # ===== 管理控制 =====
        self.ui.btn4.clicked.connect(self.goto_manage)
        self.ui.videoBtn.clicked.connect(self.select_video_file)
        self.ui.camBtn.clicked.connect(self.startCamera)
        self.ui.stopBtn.clicked.connect(self.stop)
        # ===== 检测页种类 =====
        self.updateLog.connect(self.appendLog)

        # 定义定时器，用于控制显示视频的帧率
        self.timer_camera = QtCore.QTimer()
        # 定时到了，回调 self.show_camera
        self.timer_camera.timeout.connect(self.show_camera)
        self.dashboard_timer = QtCore.QTimer(self)
        self.dashboard_timer.timeout.connect(self.update_home_clock)
        self.dashboard_timer.start(1000)
        self.update_home_clock()
        self.home_gallery_timer = QtCore.QTimer(self)
        self.home_gallery_timer.timeout.connect(self._advance_home_gallery)
        if len(self.home_gallery_items) > 1:
            self.home_gallery_timer.start(3500)


        # # 加载 YOLO nano 模型，第一次比较耗时，要20秒左右
        # self.model = YOLO('rknn/yolov8n.pt')

        # 要处理的视频帧图片队列，目前就放1帧图片
        self.frameToAnalyze = deque(maxlen=1)

        # # 启动处理视频帧独立线程
        Thread(target=self.frameAnalyzeThreadFunc,daemon=True).start()
        Thread(target=self.videoSaveThreadFunc, daemon=True).start()



    def _setup_dashboard_state(self):
        self.page_meta = {
            "home": ("路面缺陷检测系统", "", ""),
            "detect": ("检测工作区", "查看实时画面、模型结果与运行日志。", "检测"),
            "manager": ("文件管理", "统一管理素材、输出文件与导出结果。", "管理"),
            "ai": ("智能AI", "结合检测场景进行解释、问答与辅助分析。", "问答"),
            "setting": ("系统设置", "调整模型、置信度与 NMS 参数。", "设置"),
            "crack": ("裂缝分析", "执行裂缝分割并生成 AI 结果分析。", "分割"),
        }
        self.update_page_header("home")
        self._sync_threshold_cards()
        self._sync_model_label()
        self._update_detect_mode_badge()
        self._fetch_location_async()
        self._fetch_weather_async()

    def _setup_home_gallery(self):
        gallery_dir = os.path.join("qD")
        image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        text_map = {
            "AlligatorCrack": (
                "Alligator crack",
                "<div style='text-align:right;'>"
                "<div style='font-size:22px;font-weight:700;color:#ffffff;'>龟裂</div>"
                "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>龟裂是由许多相互连接的裂缝组成。通常意味着路面结构已经出现疲劳损伤，需要铣刨重铺。</div>"
                "</div>",
            ),
            "LongitudinalCrack": (
                "Longitudinal Crack",
                "<div style='text-align:right;'>"
                "<div style='font-size:22px;font-weight:700;color:#ffffff;'>纵向裂缝</div>"
                "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>裂缝与道路行驶方向平行。主要因为温度收缩、路基不均匀沉降、施工接缝质量差以及沥青老化所致。</div>"
                "</div>",
            ),
            "Oblique crack": (
                "Oblique Crack",
                "<div style='text-align:right;'>"
                "<div style='font-size:22px;font-weight:700;color:#ffffff;'>斜向裂缝</div>"
                "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>主要因为地基局部变形、剪切应力集中、车辆转弯制动、不均匀沉降所致。通常是结构应力异常的表现。</div>"
                "</div>",
            ),
            "Pothole": (
                "Pothole",
                "<div style='text-align:right;'>"
                "<div style='font-size:22px;font-weight:700;color:#ffffff;'>坑槽</div>"
                "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>路面局部材料脱落形成坑洞。可能导致爆胎、车辆悬挂损坏、交通事故。属于需要优先维修的病害。</div>"
                "</div>",
            ),
            "Repair": (
                "Repair",
                "<div style='text-align:right;'>"
                "<div style='font-size:22px;font-weight:700;color:#ffffff;'>修补区域</div>"
                "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>是道路曾经维修过的区域，可能出现二次开裂，修补层脱落以及新旧材料结合不良。</div>"
                "</div>",
            ),
        }
        self.home_gallery_items = []
        self.home_gallery_index = 0

        if os.path.isdir(gallery_dir):
            for name in sorted(os.listdir(gallery_dir)):
                path = os.path.join(gallery_dir, name)
                base, ext = os.path.splitext(name)
                if not os.path.isfile(path) or ext.lower() not in image_exts:
                    continue
                title, desc = text_map.get(
                    base,
                    (
                        base,
                        (
                            "<div style='text-align:right;'>"
                            f"<div style='font-size:22px;font-weight:700;color:#ffffff;'>{base}</div>"
                            f"<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>当前展示图片 {name}，可继续向 qD 文件夹添加图片，主页会自动纳入轮播。</div>"
                            "</div>"
                        ),
                    ),
                )
                self.home_gallery_items.append(
                    {"image": path, "title": title, "desc": desc}
                )

        if not self.home_gallery_items:
            self.home_gallery_items.append(
                {
                    "image": os.path.join("icon", "q1.png"),
                    "title": "Road Distress Detection",
                    "desc": (
                        "<div style='text-align:right;'>"
                        "<div style='font-size:22px;font-weight:700;color:#ffffff;'>路面缺陷检测</div>"
                        "<div style='margin-top:10px;font-size:13px;line-height:1.75;color:rgba(255,255,255,0.92);'>系统支持裂缝、坑槽、车辙等多类路面缺陷的智能识别与分析，结合深度学习模型与 AI 问答，为道路养护提供高效决策支持。</div>"
                        "</div>"
                    ),
                }
            )

        self._apply_home_gallery_item(0)

    def _apply_home_gallery_item(self, index):
        if not self.home_gallery_items:
            return
        self.home_gallery_index = index % len(self.home_gallery_items)
        item = self.home_gallery_items[self.home_gallery_index]
        self.ui.update_info_card(
            image_path=item["image"],
            title=item["title"],
            desc=item["desc"],
        )

    def _advance_home_gallery(self):
        if len(self.home_gallery_items) <= 1:
            return
        self._apply_home_gallery_item(self.home_gallery_index + 1)

    def update_home_clock(self):
        current = QtCore.QDateTime.currentDateTime()
        self.ui.homeClock.setText(current.toString("hh : mm : ss"))
        if not self.ui.homeDate.text().strip() or self.ui.homeDate.text() == "当前位置":
            self.ui.homeDate.setText(current.toString("正在定位 · yyyy-MM-dd"))
        if hasattr(self.ui, "posterEyebrow"):
            self.ui.posterEyebrow.setText(current.toString("天气概览 · yyyy-MM-dd"))

    def update_page_header(self, key):
        title, desc, tag = self.page_meta.get(key, self.page_meta["home"])
        self.ui.heroTitle.setText(title)
        self.ui.heroDesc.setText(desc)
        self.ui.heroTag.setText(tag)

    def _sync_model_label(self):
        model_name = self.ui.comboModel.currentText().strip() or "waiting"
        # self.ui.heroModel.setText(f"模型：{model_name}")
        # self.ui.statModel.value.setText(model_name)

    def _sync_threshold_cards(self):
        self.ui.statConf.value.setText(self.ui.labelConf.text())
        self.ui.statNms.value.setText(self.ui.labelNMS.text())

    def _update_detect_mode_badge(self):
        if self.is_video_mode:
            self.ui.detectModeBadge.setText("模式 · 视频")
        elif self.is_camera_mode:
            self.ui.detectModeBadge.setText("模式 · 摄像头")
        else:
            self.ui.detectModeBadge.setText("模式 · 待机")

    def _fetch_location_async(self):
        label = "山东烟台"
        status_note = ""
        self.locationFetched.emit(label, status_note)

    def _fetch_weather_async(self):
        def worker():
            text = "天气获取中"
            forecast = [("明天", "天气获取中"), ("后天", "天气获取中")]
            weather_note = ""
            req_kwargs = {"timeout": 6, "proxies": {"http": None, "https": None}}
            city = self.ui.editWeatherCity.text().strip() or "Yantai"
            self._debug_network_log("天气", f"开始请求 https://wttr.in/{city}?format=j1")
            try:
                resp = requests.get(f"https://wttr.in/{city}?format=j1", **req_kwargs)
                self._debug_network_log("天气", f"wttr.in 状态码: {resp.status_code}")
                data = resp.json()
                self._debug_network_log("天气", f"wttr.in 返回摘要: {str(data)[:320]}")
                current = data.get("current_condition", [{}])[0]
                temp_c = current.get("temp_C", "")
                feels_like = current.get("FeelsLikeC", "")
                humidity = current.get("humidity", "")
                desc_list = current.get("lang_zh", []) or current.get("weatherDesc", [])
                desc = ""
                if desc_list:
                    desc = self._normalize_weather_desc(desc_list[0].get("value", ""))
                if temp_c or desc:
                    text = f"{desc} {temp_c}°C".strip()
                else:
                    weather_note = "天气数据为空，请稍后重试。"
                self._debug_network_log(
                    "天气",
                    f"当前天气解析: desc={desc}, temp={temp_c}, feels_like={feels_like}, humidity={humidity}, text={text}"
                )

                weather_days = data.get("weather", []) or []
                next_days = weather_days[1:3]
                forecast = []
                day_names = ["明天", "后天"]
                for idx, item in enumerate(next_days):
                    max_temp = item.get("maxtempC", "")
                    min_temp = item.get("mintempC", "")
                    hourly = item.get("hourly", []) or []
                    hourly_desc_list = []
                    if hourly:
                        midday = hourly[min(len(hourly) - 1, 4)]
                        hourly_desc_list = midday.get("lang_zh", []) or midday.get("weatherDesc", [])
                    day_desc = ""
                    if hourly_desc_list:
                        day_desc = self._normalize_weather_desc(hourly_desc_list[0].get("value", ""))
                    temp_range = ""
                    if min_temp or max_temp:
                        temp_range = f"{min_temp}~{max_temp}°C".strip("~")
                    summary = " ".join(part for part in (day_desc, temp_range) if part).strip()
                    forecast.append((day_names[idx], summary or "暂无预报"))
                    self._debug_network_log(
                        "天气",
                        f"{day_names[idx]} 解析: desc={day_desc}, min={min_temp}, max={max_temp}, summary={forecast[-1][1]}"
                    )

                while len(forecast) < 2:
                    forecast.append((day_names[len(forecast)], "暂无预报"))
            except Exception as e:
                self._debug_network_log("天气", f"wttr.in 请求失败: {repr(e)}")
                text = "天气暂不可用"
                feels_like = ""
                humidity = ""
                weather_note = "天气请求失败，请检查网络连接。"
                forecast = [("明天", "天气暂不可用"), ("后天", "天气暂不可用")]

            self._debug_network_log(
                "天气",
                f"发送界面更新信号: title={text}, forecast1={forecast[0][1]}, forecast2={forecast[1][1]}, note={weather_note or 'OK'}"
            )
            self.weatherFetched.emit(
                text,
                feels_like,
                humidity,
                weather_note,
                forecast[0][1],
                forecast[1][1],
            )

        Thread(target=worker, daemon=True).start()

    def _apply_location_update(self, label, status_note):
        self._debug_network_log("定位", f"主线程更新界面: homeDate={label}, note={status_note}")
        self.ui.homeDate.setText(label)
        self.ui.gpsCard.valueLabel.setText(label)
        if hasattr(self.ui, "posterNote"):
            self.ui.posterNote.setText(f"{label}\n{status_note}")

    def _apply_weather_update(self, text, feels_like, humidity, weather_note, forecast1, forecast2):
        self._debug_network_log(
            "天气",
            f"主线程更新界面: title={text}, forecast1={forecast1}, forecast2={forecast2}, note={weather_note or 'OK'}"
        )
        self.ui.weatherCard.valueLabel.setText(text)
        if hasattr(self.ui, "posterTitle"):
            self.ui.posterTitle.setText(text)
        if hasattr(self.ui, "posterNote"):
            detail_parts = []
            if feels_like:
                detail_parts.append(f"体感温度 {feels_like}°C")
            if humidity:
                detail_parts.append(f"湿度 {humidity}%")
            detail = " · ".join(detail_parts)
            location_text = self.ui.homeDate.text().strip() or "当前位置"
            note = location_text
            if detail:
                note = f"{location_text}\n{detail}"
            elif weather_note:
                note = f"{location_text}\n{weather_note}"
            self.ui.posterNote.setText(note)
        if hasattr(self.ui, "posterForecastValue1"):
            self.ui.posterForecastValue1.setText(forecast1)
        if hasattr(self.ui, "posterForecastValue2"):
            self.ui.posterForecastValue2.setText(forecast2)

    def load_model_list(self):
        folder = "rknn"

        if not os.path.exists(folder):
            print("目录不存在:", folder)
            return

        files = os.listdir(folder)

        # 👉 只保留模型文件（可选过滤）
        model_files = [f for f in files if f.endswith(".pt") or f.endswith(".rknn")]

        if "yolowwrl.pt" in model_files:
            model_files.remove("yolowwrl.pt")
            model_files.insert(0, "yolowwrl.pt")
        self.ui.comboModel.clear()
        self.ui.comboModel.addItems(model_files)
        self._sync_model_label()

    def appendLog(self, text):
        print("\n UIok \n:", text)
        self.ui.textLog.setPlainText(str(text))

    def _ensure_ptresult_dir(self):
        out_dir = "ptresult"
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _build_timestamp_name(self, prefix, ext):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{stamp}{ext}"

    def _start_video_writer(self, frame):
        if not self.is_video_mode:
            self._release_video_writer()
            return

        out_dir = self._ensure_ptresult_dir()
        source_name = os.path.splitext(os.path.basename(self.current_video_path))[0] or "video"
        output_name = self._build_timestamp_name(f"{source_name}_detect", ".mp4")
        self.saved_video_path = os.path.join(out_dir, output_name)

        fps = 25.0
        if hasattr(self, "cap") and self.cap is not None:
            cap_fps = self.cap.get(cv2.CAP_PROP_FPS)
            if cap_fps and cap_fps > 1:
                fps = cap_fps

        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(self.saved_video_path, fourcc, fps, (w, h))
        self.updateLog.emit(f"检测视频保存至: {self.saved_video_path}")

    def _release_video_writer(self):
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

    def videoSaveThreadFunc(self):
        while True:
            if not self.video_save_queue:
                time.sleep(0.005)
                continue

            frame = self.video_save_queue.popleft()
            if self.video_writer is not None:
                self.video_writer.write(frame)

    def _apply_detect_preview(self, qimage):
        pixmap = QtGui.QPixmap.fromImage(qimage).scaled(
            self.ui.label_treated.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.ui.label_treated.setPixmap(pixmap)
        
    def startCamera(self):
        if self.model is None:
            self.appendLog("当前模型未成功加载，无法开始检测。请切换到可用模型，或先安装缺失依赖。")
            return
        self._release_video_writer()
        if self.is_video_mode:
            self.cap = cv2.VideoCapture(self.current_video_path)
        elif self.is_camera_mode:
            self.cap = cv2.VideoCapture(0)
        self._update_detect_mode_badge()

        ref, frame = self.cap.read()
        if not ref:
            raise ValueError("error reading")
        self.frameToAnalyze.clear()
        self.video_save_queue.clear()
            
        if self.timer_camera.isActive() == False:  # 若定时器未启动
            self.timer_camera.start(15)

    def show_camera(self):

        ret, frame = self.cap.read()  # 从视频流中读取
        if not ret:
            return

        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qImage = QtGui.QImage(
            display_frame.data,
            display_frame.shape[1],
            display_frame.shape[0],
            display_frame.strides[0],
            QtGui.QImage.Format_RGB888
        )
        pixmap = QtGui.QPixmap.fromImage(qImage).scaled(
            self.ui.label_ori_video.size(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.ui.label_ori_video.setPixmap(pixmap)

        self.frameToAnalyze.append(frame)

    def _format_detection_summary(self, results):
        boxes = getattr(results, "boxes", None)
        if boxes is None or boxes.cls is None or len(boxes.cls) == 0:
            return "当前帧检测结果：未检测到目标"

        class_ids = boxes.cls.detach().cpu().numpy().astype(int).tolist()
        counts = {}
        for class_id in class_ids:
            name = CLASSES[class_id] if 0 <= class_id < len(CLASSES) else str(class_id)
            name = CLASS_NAME_MAP.get(name, name)
            counts[name] = counts.get(name, 0) + 1

        lines = [f"当前帧检测结果：{len(class_ids)} 个目标"]
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"{name}: {count}")
        return "\n".join(lines)

    class _SimpleBoxes:
        def __init__(self, xyxy, cls, conf):
            self.xyxy = np.asarray(xyxy, dtype=np.float32)
            self.cls = np.asarray(cls, dtype=np.float32)
            self.conf = np.asarray(conf, dtype=np.float32)

    class _SimpleResult:
        def __init__(self, image_bgr, boxes):
            self.orig_img = image_bgr
            self.boxes = boxes

        def plot(self, line_width=3):
            canvas = self.orig_img.copy()
            if self.boxes is None or len(self.boxes.cls) == 0:
                return canvas

            for box, score, class_id in zip(self.boxes.xyxy, self.boxes.conf, self.boxes.cls.astype(int)):
                x1, y1, x2, y2 = [int(v) for v in box]
                name = CLASSES[class_id] if 0 <= class_id < len(CLASSES) else str(class_id)
                label = f"{name} {float(score):.2f}"
                cv2.rectangle(canvas, (x1, y1), (x2, y2), (56, 189, 248), line_width)
                text_origin = (x1, max(18, y1 - 8))
                cv2.putText(canvas, label, text_origin, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2, cv2.LINE_AA)
                cv2.putText(canvas, label, text_origin, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            return canvas

    def _sigmoid(self, x):
        x = np.clip(x, -50, 50)
        return 1.0 / (1.0 + np.exp(-x))

    def _letterbox(self, image, new_shape=(640, 640), color=(114, 114, 114)):
        shape = image.shape[:2]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        ratio = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = (int(round(shape[1] * ratio)), int(round(shape[0] * ratio)))
        dw = new_shape[1] - new_unpad[0]
        dh = new_shape[0] - new_unpad[1]
        dw /= 2.0
        dh /= 2.0

        if shape[::-1] != new_unpad:
            image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)

        top = int(round(dh - 0.1))
        bottom = int(round(dh + 0.1))
        left = int(round(dw - 0.1))
        right = int(round(dw + 0.1))
        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return image, ratio, (dw, dh)

    def _xywh2xyxy(self, boxes):
        y = np.empty_like(boxes)
        y[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.0
        y[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.0
        y[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.0
        y[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.0
        return y

    def _nms_boxes(self, boxes, scores, iou_threshold):
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)
            if order.size == 1:
                break

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            union = areas[i] + areas[order[1:]] - inter + 1e-6
            iou = inter / union
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return keep

    def _postprocess_rknn_outputs(self, outputs, ratio, pad, original_shape):
        if not outputs:
            return self._SimpleBoxes(np.empty((0, 4)), np.empty((0,)), np.empty((0,)))

        head = np.asarray(outputs[0])
        head = np.squeeze(head)

        if head.ndim == 3:
            if head.shape[0] < head.shape[1]:
                head = np.transpose(head, (1, 0, 2))
            head = head.reshape(-1, head.shape[-1])
        elif head.ndim == 2:
            if head.shape[0] < head.shape[1]:
                head = head.T
        else:
            raise ValueError(f"Unsupported RKNN output shape: {head.shape}")

        if head.shape[-1] < 5 + len(CLASSES):
            raise ValueError(f"RKNN output channels not enough: {head.shape}")

        box_data = head[:, :4].astype(np.float32)
        objectness = self._sigmoid(head[:, 4].astype(np.float32))
        class_scores = self._sigmoid(head[:, 5:5 + len(CLASSES)].astype(np.float32))
        class_ids = np.argmax(class_scores, axis=1)
        class_conf = class_scores[np.arange(class_scores.shape[0]), class_ids]
        scores = objectness * class_conf

        valid = scores >= OBJ_THRESH
        if not np.any(valid):
            return self._SimpleBoxes(np.empty((0, 4)), np.empty((0,)), np.empty((0,)))

        box_data = box_data[valid]
        scores = scores[valid]
        class_ids = class_ids[valid]

        boxes = self._xywh2xyxy(box_data)
        dw, dh = pad
        boxes[:, [0, 2]] -= dw
        boxes[:, [1, 3]] -= dh
        boxes /= max(ratio, 1e-6)

        h0, w0 = original_shape[:2]
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, w0 - 1)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, h0 - 1)

        final_boxes = []
        final_scores = []
        final_classes = []
        for class_id in np.unique(class_ids):
            inds = np.where(class_ids == class_id)[0]
            keep = self._nms_boxes(boxes[inds], scores[inds], NMS_THRESH)
            for keep_idx in keep:
                final_boxes.append(boxes[inds][keep_idx])
                final_scores.append(scores[inds][keep_idx])
                final_classes.append(class_id)

        if not final_boxes:
            return self._SimpleBoxes(np.empty((0, 4)), np.empty((0,)), np.empty((0,)))

        return self._SimpleBoxes(
            np.asarray(final_boxes, dtype=np.float32),
            np.asarray(final_classes, dtype=np.float32),
            np.asarray(final_scores, dtype=np.float32),
        )

    def _load_detection_model(self, model_path):
        model_ext = os.path.splitext(model_path)[1].lower()
        if model_ext == ".rknn":
            if RKNNLite is None:
                raise ImportError("rknnlite not installed, cannot load .rknn model")

            new_rknn = RKNNLite()
            print("--> Load RKNN model")
            ret = new_rknn.load_rknn(model_path)
            if ret != 0:
                new_rknn.release()
                raise RuntimeError(f"Load RKNN model failed: {ret}")
            print("done")

            print("--> Init runtime environment")
            ret = new_rknn.init_runtime()
            if ret != 0:
                new_rknn.release()
                raise RuntimeError(f"Init runtime environment failed: {ret}")
            print("done")

            if getattr(self, "rknn", None) is not None:
                print("--> Release old RKNN model")
                try:
                    self.rknn.release()
                except Exception:
                    pass

            self.rknn = new_rknn
            self.model_backend = "rknn"
            self.model = model_path
            return self.model

        self.model_backend = "yolo"
        self.model = YOLO(model_path)
        return self.model

    def _run_detection_inference(self, frame):
        if self.model is None:
            return None
        if self.model_backend == "rknn":
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized, ratio, pad = self._letterbox(image_rgb, (IMG_SIZE, IMG_SIZE))
            img_input = np.expand_dims(resized, axis=0)
            with self.rknn_lock:
                outputs = self.rknn.inference(inputs=[img_input])
            boxes = self._postprocess_rknn_outputs(outputs, ratio, pad, frame.shape)
            return self._SimpleResult(frame, boxes)

        return self.model(frame)[0]

    def frameAnalyzeThreadFunc(self):

        while True:
            if not self.frameToAnalyze:
                time.sleep(0.005)
                continue
            # ===== FPS 起点 =====
            t1 = time.time()

            frame = self.frameToAnalyze.popleft()
            results = self._run_detection_inference(frame)
            if results is None:
                time.sleep(0.05)
                continue

            img_show = results.plot(line_width=3)
            if self.video_writer is None and self.is_video_mode:
                self._start_video_writer(img_show)
            if self.video_writer is not None and self.is_video_mode:
                self.video_save_queue.append(img_show.copy())
            if img_show.ndim == 3:
                img_show = cv2.cvtColor(img_show, cv2.COLOR_BGR2RGB)
            detection_summary = self._format_detection_summary(results)



            # ===== FPS 计算 =====
            t2 = time.time()
            curr_fps = 1.0 / (t2 - t1)
            self.fps = self.fps * 0.9 + curr_fps * 0.1
            print("fps= %.2f" % (self.fps))

            qImage = QtGui.QImage(
                img_show.data,
                img_show.shape[1],
                img_show.shape[0],
                img_show.strides[0],
                QtGui.QImage.Format_RGB888
            )
            self.detectPreviewReady.emit(qImage.copy())
            self.updateLog.emit(detection_summary)

            # ===== 日志输出（限频）=====
            # if time.time() - self.last_log_time > 0.3:
            #     log = f"FPS: {self.fps:.2f}\n"
            #     log += "Detected: " + (", ".join(det_info) if det_info else "None")
            #     log += "\n" + "-"*30
            #     self.updateLog.emit(log)
            #     self.last_log_time = time.time()
            # print("log %s" % (log))
            
            time.sleep(0.001)
            
            
    def stop(self):
        self.timer_camera.stop()  # 关闭定时器
        if hasattr(self, "cap") and self.cap is not None:
            self.cap.release()  # 释放视频流
        self._release_video_writer()
        self.frameToAnalyze.clear()
        self.video_save_queue.clear()
        self.ui.label_ori_video.clear()  # 清空视频显示区域
        self.ui.label_treated.clear()  # 清空视频显示区域
        self.ui.label_ori_video.setText("原始视频 / 摄像头画面")
        self.ui.label_treated.setText("检测结果输出")
        self.ui.textLog.clear()
        self._update_detect_mode_badge()

    def _release_rknn_model(self):
        if getattr(self, "rknn", None) is not None:
            try:
                self.rknn.release()
            finally:
                self.rknn = None
        if self.model_backend == "rknn":
            self.model = None
            self.model_backend = None


    def on_folder_clicked(self, index):
        path = self.magmodel.filePath(index)

        self.ui.listWidget.clear()

        for file in os.listdir(path):
            full_path = os.path.join(path, file)

            item = QtWidgets.QListWidgetItem(file)

            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                icon = QtGui.QIcon(full_path)

            elif file.lower().endswith(('.mp4', '.avi')):
                icon = QtGui.QIcon("icon/video.png")  # 自己准备一个图标

            else:
                icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)

            item.setIcon(icon)
            item.setData(QtCore.Qt.UserRole, full_path)

            self.ui.listWidget.addItem(item)

    def delete_file(self):
        item = self.ui.listWidget.currentItem()
        if not item:
            return

        path = item.data(QtCore.Qt.UserRole)

        reply = QtWidgets.QMessageBox.question(
            self, "确认删除", f"删除 {path} ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                import shutil
                shutil.rmtree(path)

            self.ui.listWidget.takeItem(self.ui.listWidget.row(item))

    def export_file(self):
        item = self.ui.listWidget.currentItem()
        if not item:
            return

        src = item.data(QtCore.Qt.UserRole)

        dst, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出文件")

        if dst:
            import shutil
            shutil.copy(src, dst)

    def select_video_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            self.current_video_path,
            "Videos (*.mp4 *.avi *.mov *.mkv)"
        )

        if not file_path:
            return

        
        
        self.current_video_path = file_path
        self.is_video_mode = True
        self.is_camera_mode = False
        self._update_detect_mode_badge()
        self.ui.textLog.append(f"已选择视频: {file_path}")

        cap = cv2.VideoCapture(file_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qImage = QtGui.QImage(
                frame.data, frame.shape[1], frame.shape[0],
                frame.strides[0], QtGui.QImage.Format_RGB888
            )
            pixmap = QtGui.QPixmap.fromImage(qImage).scaled(
                self.ui.label_ori_video.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            self.ui.label_ori_video.setPixmap(pixmap)
            self.ui.label_treated.setText("检测结果输出")

    def refresh(self):
        index = self.ui.treeView.currentIndex()
        self.on_folder_clicked(index)

    def goto_crack(self):
        self.seg_model = YOLO("yolov8n-seg.pt")
        self._load_icon_images()
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_crack_picker)
        self.update_page_header("crack")

    def goto_ai(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_ai)
        self.update_page_header("ai")

    def _load_icon_images(self):
        self.ui.iconImageList.clear()
        image_dir = os.path.join(os.getcwd(), "segaimage")
        if not os.path.isdir(image_dir):
            return

        image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        for name in sorted(os.listdir(image_dir)):
            full_path = os.path.join(image_dir, name)
            if not os.path.isfile(full_path):
                continue
            if os.path.splitext(name)[1].lower() not in image_exts:
                continue

            item = QtWidgets.QListWidgetItem(QtGui.QIcon(full_path), os.path.splitext(name)[0])
            item.setData(QtCore.Qt.UserRole, full_path)
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setSizeHint(QtCore.QSize(180, 160))
            self.ui.iconImageList.addItem(item)

    def selectImage(self):
        self._load_icon_images()
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_crack_picker)
        self.update_page_header("crack")

    def select_icon_image(self, item):
        file_path = item.data(QtCore.Qt.UserRole)
        if not file_path:
            return

        self.current_img_path = file_path
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_crack)
        self.runSegmentation()

    def runSegmentation(self):
        if not hasattr(self, "current_img_path"):
            return

        img = cv2.imread(self.current_img_path)

        # 推理
        results = self.seg_model(img)[0]

        # 可视化（带mask）
        res_img = results.plot(line_width=3)

        out_dir = self._ensure_ptresult_dir()
        source_name = os.path.splitext(os.path.basename(self.current_img_path))[0] or "segment"
        save_path = os.path.join(out_dir, self._build_timestamp_name(f"{source_name}_seg", ".png"))
        cv2.imwrite(save_path, res_img)

        res_img = cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB)

        self.showImage(res_img, self.ui.label_crack_result)
        self.ui.text_crack_analysis.clear()
        self.ui.text_crack_analysis.append(f"分割结果已保存: {save_path}")
        self.runQwenAnalysis()

    def displayAiResult(self, text):
        self.ui.text_crack_analysis.append(text)

    def runQwenAnalysis(self):
        if not hasattr(self, "current_img_path"):
            self.ui.text_crack_analysis.append("请先选择图片并运行分割分析")
            return

        if not QWEN_API_KEY:
            self.ui.text_crack_analysis.append("错误: 请先设置 QWEN_API_KEY")
            return

        img = cv2.imread(self.current_img_path)
        _, buffer = cv2.imencode(".jpg", img)
        img_base64 = base64.b64encode(buffer).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }

        question = self.ui.edit_ai_question.text().strip()
        if not question:
            question = "请详细分析这张图片中的裂缝情况，包括裂缝的位置、长度、宽度、严重程度以及可能的安全隐患，并给出处理建议。"

        payload = {
            "model": QWEN_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ]
        }

        self.ui.text_crack_analysis.append("正在调用智能AI进行分析...")

        def api_call():
            try:
                resp = requests.post(QWEN_API_URL, headers=headers, json=payload, timeout=60,
                                     proxies={"http": None, "https": None})
                result = resp.json()
                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                    self.aiAnalysisResult.emit(f"\n===== 智能AI分析结果 =====\n{content}\n")
                else:
                    self.aiAnalysisResult.emit(f"API返回异常: {result}")
            except Exception as e:
                self.aiAnalysisResult.emit(f"API调用失败: {str(e)}")

        Thread(target=api_call, daemon=True).start()

    def showImage(self, img, label):
        h, w, ch = img.shape
        bytes_per_line = ch * w

        qimg = QtGui.QImage(img.data, w, h, bytes_per_line,
                            QtGui.QImage.Format_RGB888)

        pixmap = QtGui.QPixmap.fromImage(qimg)

        # ⭐ 核心：按label大小等比例缩放
        pixmap = pixmap.scaled(
            label.width(),
            label.height(),
            QtCore.Qt.KeepAspectRatio,  # 保持比例
            QtCore.Qt.SmoothTransformation
        )

        label.setPixmap(pixmap)


    def displayAiChat(self, text):
        self.ui.text_chat.append(f"【AI】{text}\n")

    def sendAiQuestion(self):
        question = self.ui.edit_ai_input.text().strip()
        if not question:
            return

        if not QWEN_API_KEY:
            self.ui.text_chat.append("【系统】错误: 请先设置 QWEN_API_KEY")
            return

        self.ui.text_chat.append(f"【你】{question}")
        self.ui.edit_ai_input.clear()
        self.ui.text_chat.append("【AI】思考中...")

        headers = {
            "Authorization": f"Bearer {QWEN_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "qwen-plus",
            "messages": [
                {"role": "user", "content": question}
            ]
        }

        def api_call():
            try:
                resp = requests.post(QWEN_API_URL, headers=headers, json=payload, timeout=60,
                                     proxies={"http": None, "https": None})
                result = resp.json()
                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                    self.aiChatResult.emit(content)
                else:
                    self.aiChatResult.emit(f"API返回异常: {result}")
            except Exception as e:
                self.aiChatResult.emit(f"API调用失败: {str(e)}")

        Thread(target=api_call, daemon=True).start()

    def goto_setting(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_setting)
        self.update_page_header("setting")
    def goto_detect(self):
        sender = self.sender()
        if sender == self.ui.btnVideoOD:
            self.is_video_mode = True
            self.is_camera_mode = False
            self.ui.videoBtn.setVisible(True)
            print("进入 视频检测 模式")

        elif sender == self.ui.btnRealTimOD:
            self.is_video_mode = False
            self.is_camera_mode = True
            self.ui.videoBtn.setVisible(False)
            print("进入 摄像头检测 模式")
        # 切换页面
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_detect)
        self.update_page_header("detect")
        self._update_detect_mode_badge()

    def goto_manage(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_manager)
        self.update_page_header("manager")

    def change_img_size(self):
        global IMG_SIZE
        IMG_SIZE = int(self.ui.comboImgSize.currentText())
        print(f"输入尺寸切换为: {IMG_SIZE}")

    def change_ai_model(self):
        global QWEN_MODEL
        QWEN_MODEL = self.ui.comboAiModel.currentText()
        print(f"AI 模型切换为: {QWEN_MODEL}")

    def change_api_key(self):
        global QWEN_API_KEY
        QWEN_API_KEY = self.ui.editApiKey.text().strip()

    def toggle_api_key_visible(self):
        if self.ui.editApiKey.echoMode() == QtWidgets.QLineEdit.Password:
            self.ui.editApiKey.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.ui.editApiKey.setEchoMode(QtWidgets.QLineEdit.Password)

    def change_weather_city(self):
        city = self.ui.editWeatherCity.text().strip()
        if city:
            self._fetch_weather_async()

    def update_conf(self, val):
        global OBJ_THRESH
        conf = val / 100.0
        self.ui.labelConf.setText(f"{conf:.2f}")
        # self.conf_thresh = conf
        OBJ_THRESH = conf
        self._sync_threshold_cards()
        print("\n conf \n", conf)
    def update_nms(self, val):
        global NMS_THRESH
        nms = val / 100.0
        self.ui.labelNMS.setText(f"{nms:.2f}")
        # self.nms_thresh = nms
        NMS_THRESH = nms
        self._sync_threshold_cards()
        print("\n nms \n", nms)


    def change_model(self):
        model_name = self.ui.comboModel.currentText()
        if not model_name:
            return
        model_path = "rknn/" + model_name
        print("切换模型:", model_path)

        old_model = self.model
        old_backend = self.model_backend
        old_rknn = self.rknn
        try:
            self.model = self._load_detection_model(model_path)
            self.appendLog(f"模型切换成功: {model_name}")
            self._sync_model_label()
        except Exception as e:
            self.model = old_model
            self.model_backend = old_backend
            self.rknn = old_rknn
            error_text = str(e)
            self.appendLog(f"模型加载失败: {model_name}\n{error_text}")
            print(f"[模型] 加载失败: {repr(e)}")

    def closeEvent(self, event):
        self.stop()
        self._release_rknn_model()
        super().closeEvent(event)

    def goto_home(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
        self.is_video_mode = False
        self.is_camera_mode = False
        self.update_page_header("home")
        self._update_detect_mode_badge()


if __name__ == '__main__':

    app = QtWidgets.QApplication()
    window = MWindow()
    window.show()
    app.exec()
