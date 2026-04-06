from PySide6 import QtWidgets, QtCore, QtGui
import cv2, os, time
import sys
import numpy as np
from threading import Thread
from UI import Ui_MainWindow
from rknnlite.api import RKNNLite
from rknnmain import RKNNImageInfer
from queue import Queue

# RKNN_MODEL = "rknn/yolowwr.rknn"

QUANTIZE_ON = True
OBJ_THRESH = 0.60
NMS_THRESH = 0.45
IMG_SIZE = 640

CLASSES = (
    "Alligator crack",
    "Longitudinal crack",
    "Oblique crack",
    "Pothole",
    "Repair",
    "Transverse crack",
)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def xywh2xyxy(x):
    # Convert [x, y, w, h] to [x1, y1, x2, y2]
    y = np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y


# 把 YOLO feature map 解码成真实框
def process(input, mask, anchors):
    anchors = [anchors[i] for i in mask]
    grid_h, grid_w = map(int, input.shape[0:2])
    box_confidence = sigmoid(input[..., 4])
    # box_confidence = input[..., 4]
    box_confidence = np.expand_dims(box_confidence, axis=-1)
    box_class_probs = sigmoid(input[..., 5:])
    # box_class_probs = input[..., 5:]
    box_xy = sigmoid(input[..., :2]) * 2 - 0.5
    # box_xy = input[..., :2] * 2 - 0.5
    col = np.tile(np.arange(0, grid_w), grid_w).reshape(-1, grid_w)
    row = np.tile(np.arange(0, grid_h).reshape(-1, 1), grid_h)
    col = col.reshape(grid_h, grid_w, 1, 1).repeat(3, axis=-2)
    row = row.reshape(grid_h, grid_w, 1, 1).repeat(3, axis=-2)
    grid = np.concatenate((col, row), axis=-1)
    box_xy += grid
    box_xy *= int(IMG_SIZE / grid_h)
    box_wh = pow(sigmoid(input[..., 2:4]) * 2, 2)
    # box_wh = pow(input[..., 2:4] * 2, 2)
    box_wh = box_wh * anchors
    box = np.concatenate((box_xy, box_wh), axis=-1)
    return box, box_confidence, box_class_probs


def filter_boxes(boxes, box_confidences, box_class_probs):
    boxes = boxes.reshape(-1, 4)
    box_confidences = box_confidences.reshape(-1)
    box_class_probs = box_class_probs.reshape(-1, box_class_probs.shape[-1])
    _box_pos = np.where(box_confidences >= OBJ_THRESH)
    boxes = boxes[_box_pos]
    box_confidences = box_confidences[_box_pos]
    box_class_probs = box_class_probs[_box_pos]
    class_max_score = np.max(box_class_probs, axis=-1)
    classes = np.argmax(box_class_probs, axis=-1)
    _class_pos = np.where(class_max_score >= OBJ_THRESH)
    boxes = boxes[_class_pos]
    classes = classes[_class_pos]
    scores = (class_max_score * box_confidences)[_class_pos]
    return boxes, classes, scores


# 去掉重复框（IoU > 阈值）
def nms_boxes(boxes, scores):
    x = boxes[:, 0]
    y = boxes[:, 1]
    w = boxes[:, 2] - boxes[:, 0]
    h = boxes[:, 3] - boxes[:, 1]
    areas = w * h
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x[i], x[order[1:]])
        yy1 = np.maximum(y[i], y[order[1:]])
        xx2 = np.minimum(x[i] + w[i], x[order[1:]] + w[order[1:]])
        yy2 = np.minimum(y[i] + h[i], y[order[1:]] + h[order[1:]])
        w1 = np.maximum(0.0, xx2 - xx1 + 0.00001)
        h1 = np.maximum(0.0, yy2 - yy1 + 0.00001)
        inter = w1 * h1
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= NMS_THRESH)[0]
        order = order[inds + 1]
    keep = np.array(keep)
    return keep


def dfl(x):
    n, c, h, w = x.shape
    p_num = 4
    mc = c // p_num  # 16

    x = x.reshape(n, p_num, mc, h, w)

    # softmax
    x = np.exp(x) / np.sum(np.exp(x), axis=2, keepdims=True)

    acc = np.arange(mc).reshape(1, 1, mc, 1, 1)
    x = (x * acc).sum(2)

    return x


# def dfl(position):
#     # Distribution Focal Loss (DFL)
#     import torch
#     x = torch.tensor(position)
#     n,c,h,w = x.shape
#     p_num = 4
#     mc = c//p_num
#     y = x.reshape(n,p_num,mc,h,w)
#     y = y.softmax(2)
#     acc_metrix = torch.tensor(range(mc)).float().reshape(1,1,mc,1,1)
#     y = (y*acc_metrix).sum(2)
#     return y.numpy()


def box_process(position):
    grid_h, grid_w = position.shape[2:4]

    col, row = np.meshgrid(np.arange(grid_w), np.arange(grid_h))
    col = col.reshape(1, 1, grid_h, grid_w)
    row = row.reshape(1, 1, grid_h, grid_w)

    grid = np.concatenate((col, row), axis=1)

    stride = np.array([640 // grid_h, 640 // grid_w]).reshape(1, 2, 1, 1)

    position = dfl(position)

    box_xy1 = grid + 0.5 - position[:, 0:2, :, :]
    box_xy2 = grid + 0.5 + position[:, 2:4, :, :]

    boxes = np.concatenate((box_xy1 * stride, box_xy2 * stride), axis=1)

    return boxes


def yolo11_post_process(input_data):
    boxes, scores, classes_conf = [], [], []
    defualt_branch = 3
    pair_per_branch = len(input_data) // defualt_branch
    # Python 忽略 score_sum 输出
    for i in range(defualt_branch):
        boxes.append(box_process(input_data[pair_per_branch * i]))
        classes_conf.append(input_data[pair_per_branch * i + 1])
        scores.append(
            np.ones_like(
                input_data[pair_per_branch * i + 1][:, :1, :, :], dtype=np.float32
            )
        )

    def sp_flatten(_in):
        ch = _in.shape[1]
        _in = _in.transpose(0, 2, 3, 1)
        return _in.reshape(-1, ch)

    boxes = [sp_flatten(_v) for _v in boxes]
    classes_conf = [sp_flatten(_v) for _v in classes_conf]
    scores = [sp_flatten(_v) for _v in scores]

    boxes = np.concatenate(boxes)
    classes_conf = np.concatenate(classes_conf)
    scores = np.concatenate(scores)

    # filter according to threshold
    boxes, classes, scores = filter_boxes(boxes, scores, classes_conf)

    # nms
    nboxes, nclasses, nscores = [], [], []
    for c in set(classes):
        inds = np.where(classes == c)
        b = boxes[inds]
        c = classes[inds]
        s = scores[inds]
        keep = nms_boxes(b, s)

        if len(keep) != 0:
            nboxes.append(b[keep])
            nclasses.append(c[keep])
            nscores.append(s[keep])

    if not nclasses and not nscores:
        return None, None, None

    boxes = np.concatenate(nboxes)
    classes = np.concatenate(nclasses)
    scores = np.concatenate(nscores)

    return boxes, classes, scores


def draw1(image, boxes, scores, classes):
    for box, score, cl in zip(boxes, scores, classes):
        top, left, right, bottom = box
        # print('class: {}, score: {}'.format(CLASSES[cl], score))
        print(
            "box coordinate left,top,right,down: [{}, {}, {}, {}]".format(
                top, left, right, bottom
            )
        )
        top = int(top)
        left = int(left)
        right = int(right)
        bottom = int(bottom)
        # 在图上画框
        cv2.rectangle(image, (top, left), (right, bottom), (0, 255, 0), 3)
        # 写类别 + 分数
        cv2.putText(
            image,
            "{0} {1:.2f}".format(CLASSES[cl], score),
            (top, left - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )


def letterbox(im, new_shape=(640, 640), color=(0, 0, 0)):
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    dw /= 2  # divide padding into 2 sides
    dh /= 2
    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(
        im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )  # add border
    return im, ratio, (dw, dh)


class MWindow(QtWidgets.QMainWindow):
    updateLog = QtCore.Signal(str)  # 新增

    def __init__(self):

        super().__init__()

        # 设置界面
        self.ui = Ui_MainWindow()
        self.ui.setupUI(self)
        # 初始化rknn
        self.rknn = RKNNLite()
        self.load_model_list()

        self.fps = 0.0
        self.is_video_mode = False
        self.is_camera_mode = False

        self.last_log_time = time.time()

        self.save_dir = "capsave"
        self.last_save_time = 0
        self.save_interval = 2.0  # 秒
        self.save_thresh = 0.7  # 置信度阈值
        self.video_path = "video/od.mp4"
        os.makedirs(self.save_dir, exist_ok=True)

        # self.conf_thresh = 0.0
        # self.nms_thresh = 0.0
        # ===== 分析控制 =====
        self.ui.btn3.clicked.connect(self.goto_crack)
        self.ui.btn_select_img.clicked.connect(self.selectImage)
        self.ui.btn_run_seg.clicked.connect(self.runSegmentation)
        self.ui.btn_back_crack.clicked.connect(self.goto_home)
        # ===== 文件控制 =====
        self.magmodel = QtWidgets.QFileSystemModel()
        self.magmodel.setRootPath(QtCore.QDir.currentPath())

        self.ui.treeView.setModel(self.magmodel)
        self.ui.treeView.setRootIndex(self.magmodel.index(QtCore.QDir.currentPath()))
        self.ui.treeView.clicked.connect(self.on_folder_clicked)
        self.ui.btnDelete.clicked.connect(self.delete_file)
        self.ui.btnRefresh.clicked.connect(self.refresh)
        # ===== 时间控制 =====
        self.ui.btn5.clicked.connect(self.goto_time)
        self.ui.btnBackTime.clicked.connect(self.goto_home)
        self.timer_clock = QtCore.QTimer()
        self.timer_clock.timeout.connect(self.update_time)
        self.timer_clock.start(1000)  # 每秒一次
        # ===== 设置控制 =====
        self.ui.btn6.clicked.connect(self.goto_setting)
        self.ui.btnBackSetting.clicked.connect(self.goto_home)
        self.ui.sliderConf.valueChanged.connect(self.update_conf)
        self.ui.sliderNMS.valueChanged.connect(self.update_nms)
        self.ui.comboModel.currentIndexChanged.connect(self.change_model)
        self.ui.comboModel.setCurrentIndex(4)
        # if self.ui.comboModel.count() > 2:
        #     self.ui.comboModel.setCurrentIndex(0)
        # self.ui.comboModel.currentIndexChanged.emit(self.ui.comboModel.currentIndex(2))

        # ===== 页面跳转 =====
        self.ui.btnVideoOD.clicked.connect(self.goto_detect)
        self.ui.btnRealTimOD.clicked.connect(self.goto_detect)

        self.ui.backBtn.clicked.connect(self.goto_home)
        self.ui.btn4.clicked.connect(self.goto_manage)
        self.ui.btnBackManager.clicked.connect(self.goto_home)

        # ===== UIBtn 访问控件 =====
        self.ui.camBtn.clicked.connect(self.startCamera)
        self.ui.stopBtn.clicked.connect(self.stop)
        self.ui.videoBtn.clicked.connect(self.openVideoFile)

        self.updateLog.connect(self.appendLog)

        # 定义定时器，用于控制显示视频的帧率
        self.timer_camera = QtCore.QTimer()
        # 定时到了，回调 self.show_camera
        self.timer_camera.timeout.connect(self.show_camera)

        # 要处理的视频帧图片队列，目前就放1帧图片
        # self.frameToAnalyze = []
        self.frameToAnalyze = Queue(maxsize=1)

        # # 启动处理视频帧独立线程
        Thread(target=self.frameAnalyzeThreadFunc, daemon=True).start()

    def load_model_list(self):
        folder = "rknn"

        if not os.path.exists(folder):
            print("目录不存在:", folder)
            return

        files = os.listdir(folder)

        # 👉 只保留模型文件（可选过滤）
        model_files = [f for f in files if f.endswith(".pt") or f.endswith(".rknn")]

        self.ui.comboModel.clear()
        self.ui.comboModel.addItems(model_files)

    def appendLog(self, text):
        print("\n UIok \n:", text)
        self.ui.textLog.append(str(text))

    def startCamera(self):
        if self.is_video_mode:
            self.cap = cv2.VideoCapture(self.video_path)  # 你的视频路径
        elif self.is_camera_mode:
            self.cap = cv2.VideoCapture(11)

        ref, frame = self.cap.read()
        if not ref:
            raise ValueError("error reading")

        if self.timer_camera.isActive() == False:  # 若定时器未启动
            self.timer_camera.start(50)

    def openVideoFile(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )

        if not file_path:
            return

        print("选择视频:", file_path)

        self.video_path = file_path

        # 跳转到检测页面
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_detect)

        # 打开视频
        # self.cap = cv2.VideoCapture(file_path)

        # if not self.cap.isOpened():
        #     QtWidgets.QMessageBox.warning(self, "错误", "无法打开视频")
        #     return

        # 启动读取线程
        # self.startVideo()

    def show_camera(self):

        ret, frame = self.cap.read()  # 从视频流中读取
        if not ret:
            return

        # 把读到的16:10帧的大小重新设置
        frame = cv2.resize(frame, (300, 300))
        # 视频色彩转换回RGB，OpenCV images as BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qImage = QtGui.QImage(
            frame.data, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888
        )  # 变成QImage形式
        # 往显示视频的Label里 显示QImage
        self.ui.label_ori_video.setPixmap(QtGui.QPixmap.fromImage(qImage))

        # 如果当前没有处理任务
        # if not self.frameToAnalyze:
        #     self.frameToAnalyze.append(frame)
        if self.frameToAnalyze.full():
            try:
                self.frameToAnalyze.get_nowait()
            except:
                pass

        self.frameToAnalyze.put(frame)

    def frameAnalyzeThreadFunc(self):

        while True:
            # if not self.frameToAnalyze:
            #     time.sleep(0.01)
            #     continue
            if self.frameToAnalyze.empty():
                time.sleep(0.01)
                continue
            # ===== FPS 起点 =====
            t1 = time.time()
            # frame = self.frameToAnalyze.pop(0)
            frame = self.frameToAnalyze.get()
            # ⚠️ 注意：frame 当前是 RGB (因为 show_camera 已经转过)
            img = frame.copy()

            # ===== 1. letterbox =====
            img_lb, ratio, (dw, dh) = letterbox(img, new_shape=(IMG_SIZE, IMG_SIZE))

            # ===== 2. expand dim =====
            img_input = np.expand_dims(img_lb, 0)

            # ===== 3. RKNN 推理 =====
            outputs = self.rknn.inference(inputs=[img_input])

            # # ===== 5. 后处理 =====
            boxes, classes, scores = yolo11_post_process(outputs)
            print("boxes:", boxes)
            print("classes", classes)
            print("scores", scores)

            # ===== FPS 计算 =====
            t2 = time.time()
            curr_fps = 1.0 / (t2 - t1)
            self.fps = self.fps * 0.9 + curr_fps * 0.1
            print("fps= %.2f" % (self.fps))

            # ===== 6. 画框（在 letterbox 图上）=====
            img_show = img_lb.copy()

            det_info = []
            if boxes is not None:
                draw1(img_show, boxes, scores, classes)
                for cl, sc in zip(classes, scores):
                    det_info.append(f"{CLASSES[cl]}({sc:.2f})")

            # ===== 自动保存高置信度帧 =====
            if scores is not None and len(scores) > 0:
                max_score = float(np.max(scores))

                if max_score >= self.save_thresh:
                    now = time.time()

                    if now - self.last_save_time > self.save_interval:
                        # 生成文件名（时间戳）
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"{timestamp}_{max_score:.2f}.jpg"
                        save_path = os.path.join(self.save_dir, filename)

                        # ⚠️ 保存画框图
                        cv2.imwrite(
                            save_path, cv2.cvtColor(img_show, cv2.COLOR_RGB2BGR)
                        )

                        print(f"[保存] {save_path}")

                        self.last_save_time = now

            # ===== 7. 转 Qt 显示 =====
            img_show = cv2.resize(img_show, (300, 300))

            qImage = QtGui.QImage(
                img_show.data,
                img_show.shape[1],
                img_show.shape[0],
                QtGui.QImage.Format_RGB888,
            )

            self.ui.label_treated.setPixmap(QtGui.QPixmap.fromImage(qImage))

            # ===== 日志输出（限频）=====
            if time.time() - self.last_log_time > 0.3:
                log = f"FPS: {self.fps:.2f}\n"
                log += "Detected: " + (", ".join(det_info) if det_info else "None")
                log += "\n" + "-" * 30
                self.updateLog.emit(log)
                self.last_log_time = time.time()
            print("log %s" % (log))

            time.sleep(0.02)

    def stop(self):
        self.timer_camera.stop()  # 关闭定时器
        self.cap.release()  # 释放视频流
        # ===== 清空队列（Queue写法）=====
        # from queue import Empty

        # while not self.frameToAnalyze.empty():
        #     try:
        #         self.frameToAnalyze.get_nowait()
        #     except Empty:
        #         break
        # self.ui.label_ori_video.clear()  # 清空视频显示区域
        # self.ui.label_treated.clear()  # 清空视频显示区域

    def on_folder_clicked(self, index):
        path = self.magmodel.filePath(index)
        self.ui.labelPath.setText(f"当前路径: {path}")

        self.ui.listWidget.clear()

        for file in os.listdir(path):
            full_path = os.path.join(path, file)

            item = QtWidgets.QListWidgetItem(file)

            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                icon = QtGui.QIcon(full_path)

            elif file.lower().endswith((".mp4", ".avi")):
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
            self,
            "确认删除",
            f"删除 {path} ?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
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

    def refresh(self):
        index = self.ui.treeView.currentIndex()
        self.on_folder_clicked(index)

    def goto_crack(self):
        # self.seg_model = YOLO("yolov8n-seg.pt")
        self.seg_model = RKNNImageInfer("rknn/yolov11_seg.rknn")
        # 初始化模型
        self.seg_model.load_model()
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_crack)

    def goto_time(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_time)

    def selectImage(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择图片", "", "Images (*.png *.jpg *.bmp)"
        )

        if not file_path:
            return

        self.current_img_path = file_path

        # 显示原图
        img = cv2.imread(file_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        self.showImage(img, self.ui.label_crack_ori)

    def runSegmentation(self):
        if not hasattr(self, "current_img_path"):
            return
        print("原始路径 self.current_img_path:", self.current_img_path)
        # 推理
        result = self.seg_model.infer_path(self.current_img_path)

        base_name = os.path.basename(self.current_img_path)  # xxx.jpg
        print("base_name:", base_name)

        name, ext = os.path.splitext(base_name)  # xxx, .jpg
        save_name = f"{name}_result{ext}"  # xxx_result.jpg
        save_path = os.path.join("out", save_name)

        # 保存
        os.makedirs("out", exist_ok=True)
        self.seg_model.save(result, save_path)

        print(f"Result saved to: {save_path}")

        # 4️⃣ 读取并显示（带安全检查）
        res_img = cv2.imread(save_path)
        if res_img is None:
            raise RuntimeError(f"读取结果失败: {save_path}")

        res_img = cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB)

        self.showImage(res_img, self.ui.label_crack_res)

    def showImage(self, img, label):
        h, w, ch = img.shape
        bytes_per_line = ch * w

        qimg = QtGui.QImage(img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)

        pixmap = QtGui.QPixmap.fromImage(qimg)

        # ⭐ 核心：按label大小等比例缩放
        pixmap = pixmap.scaled(
            label.width(),
            label.height(),
            QtCore.Qt.KeepAspectRatio,  # 保持比例
            QtCore.Qt.SmoothTransformation,
        )

        label.setPixmap(pixmap)

    def update_time(self):
        current = QtCore.QDateTime.currentDateTime()

        # 时间（到秒）
        time_str = current.toString("HH:mm:ss")

        # 日期
        date_str = current.toString("yyyy-MM-dd dddd")

        self.ui.labelTime.setText(time_str)
        self.ui.labelDate.setText(date_str)

    def goto_setting(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_setting)

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
        self.ui.textLog.clear()
        self.ui.label_ori_video.clear()  # 清空视频显示区域
        self.ui.label_treated.clear()  # 清空视频显示区域
        # 切换页面
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_detect)

    def goto_manage(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_manager)

    def update_conf(self, val):
        global OBJ_THRESH
        conf = val / 100.0
        self.ui.labelConf.setText(f"{conf:.2f}")
        # self.conf_thresh = conf
        OBJ_THRESH = conf
        print("\n conf \n", conf)

    def update_nms(self, val):
        global NMS_THRESH
        nms = val / 100.0
        self.ui.labelNMS.setText(f"{nms:.2f}")
        # self.nms_thresh = nms
        NMS_THRESH = nms
        print("\n nms \n", nms)

    def change_model(self):
        model_name = self.ui.comboModel.currentText()
        model_path = "rknn/" + model_name
        print("切换模型:", model_path)

        # 重新加载
        # self.model = YOLO(model_path)
        # self.model = "rknn/yolowwr.rknn"
        if hasattr(self, "rknn") and self.rknn is not None:
            print("--> Release old RKNN model")
            self.rknn.release()

        print("--> Load RKNN model")
        ret = self.rknn.load_rknn(model_path)
        if ret != 0:
            print("Load RKNN model failed")
            exit(ret)
        print("done")
        ret = self.rknn.init_runtime()
        if ret != 0:
            print("Init runtime environment failed!")
            exit(ret)
        print("done")

    def goto_home(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.page_home)
        self.is_video_mode = False
        self.is_camera_mode = False
        # 释放资源
        if hasattr(self, "seg_model") and self.seg_model is not None:
            print("--> Release seg_model model")
            self.seg_model.release()


if __name__ == "__main__":

    app = QtWidgets.QApplication()
    window = MWindow()
    window.show()
    app.exec()
