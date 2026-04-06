import os
import cv2
import numpy as np
from copy import copy

# from rknn.api import RKNN
from rknnlite.api import RKNNLite

OBJ_THRESH = 0.25
NMS_THRESH = 0.45
MAX_DETECT = 300
IMG_SIZE = (640, 640)

target = "rk3588"
device_id = "192.168.103.152:5555"

rknn_model_path = "rknn/yolov8n-seg.onnx"
img_path = "icon/bus.jpg"

CLASSES = (
    "person",
    "bicycle",
    "car",
    "motorbike ",
    "aeroplane ",
    "bus ",
    "train",
    "truck ",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign ",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog ",
    "horse ",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra ",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife ",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza ",
    "donut",
    "cake",
    "chair",
    "sofa",
    "pottedplant",
    "bed",
    "diningtable",
    "toilet ",
    "tvmonitor",
    "laptop	",
    "mouse	",
    "remote ",
    "keyboard ",
    "cell phone",
    "microwave ",
    "oven ",
    "toaster",
    "sink",
    "refrigerator ",
    "book",
    "clock",
    "vase",
    "scissors ",
    "teddy bear ",
    "hair drier",
    "toothbrush ",
)


# ------------------------------------------------
# 工具函数
# ------------------------------------------------


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def softmax(x, axis):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def nms_numpy(boxes, scores, iou_thresh):

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []

    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)

        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(iou <= iou_thresh)[0]
        order = order[inds + 1]

    return keep


# ------------------------------------------------
# YOLOv8 DFL 解码
# ------------------------------------------------


def dfl(position):

    n, c, h, w = position.shape

    p_num = 4
    mc = c // p_num

    y = position.reshape(n, p_num, mc, h, w)

    y = softmax(y, axis=2)

    acc = np.arange(mc).reshape(1, 1, mc, 1, 1)

    y = (y * acc).sum(2)

    return y


def box_process(position):

    grid_h, grid_w = position.shape[2:4]

    col, row = np.meshgrid(np.arange(grid_w), np.arange(grid_h))

    col = col.reshape(1, 1, grid_h, grid_w)
    row = row.reshape(1, 1, grid_h, grid_w)

    grid = np.concatenate((col, row), axis=1)

    stride = np.array([IMG_SIZE[1] // grid_h, IMG_SIZE[0] // grid_w]).reshape(
        1, 2, 1, 1
    )

    position = dfl(position)

    box_xy = grid + 0.5 - position[:, 0:2, :, :]
    box_xy2 = grid + 0.5 + position[:, 2:4, :, :]

    xyxy = np.concatenate((box_xy * stride, box_xy2 * stride), axis=1)

    return xyxy


# ------------------------------------------------
# NMS前筛选
# ------------------------------------------------


def filter_boxes(boxes, scores, class_probs, seg_part):

    class_max = np.max(class_probs, axis=-1)
    classes = np.argmax(class_probs, axis=-1)

    pos = np.where(class_max * scores >= OBJ_THRESH)

    boxes = boxes[pos]
    classes = classes[pos]
    scores = (class_max * scores)[pos]
    seg_part = seg_part[pos]

    return boxes, classes, scores, seg_part


# ------------------------------------------------
# 后处理
# ------------------------------------------------


def post_process(input_data):

    proto = input_data[-1]

    boxes = []
    scores = []
    classes_conf = []
    seg_part = []

    branch = 3
    pair = len(input_data) // branch

    for i in range(branch):

        boxes.append(box_process(input_data[pair * i]))
        classes_conf.append(input_data[pair * i + 1])
        scores.append(np.ones_like(input_data[pair * i + 1][:, :1, :, :]))
        seg_part.append(input_data[pair * i + 3])

    def flatten(x):

        c = x.shape[1]
        x = x.transpose(0, 2, 3, 1)
        return x.reshape(-1, c)

    boxes = np.concatenate([flatten(x) for x in boxes])
    classes_conf = np.concatenate([flatten(x) for x in classes_conf])
    scores = np.concatenate([flatten(x) for x in scores])
    seg_part = np.concatenate([flatten(x) for x in seg_part])

    boxes, classes, scores, seg_part = filter_boxes(
        boxes, scores, classes_conf, seg_part
    )

    if len(boxes) == 0:
        return None, None, None, None

    ids = nms_numpy(boxes, scores, NMS_THRESH)

    ids = ids[:MAX_DETECT]

    boxes = boxes[ids]
    classes = classes[ids]
    scores = scores[ids]
    seg_part = seg_part[ids]

    ph, pw = proto.shape[-2:]

    proto = proto.reshape(seg_part.shape[-1], -1)

    seg_img = np.matmul(seg_part, proto)

    seg_img = sigmoid(seg_img)

    seg_img = seg_img.reshape(-1, ph, pw)

    seg_img = np.array([cv2.resize(m, (640, 640)) for m in seg_img])

    seg_img = seg_img > 0.5

    return boxes, classes, scores, seg_img


# ------------------------------------------------
# 绘制
# ------------------------------------------------


def draw(image, boxes, scores, classes):

    for box, score, cl in zip(boxes, scores, classes):

        x1, y1, x2, y2 = map(int, box)

        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)

        label = f"{CLASSES[cl]} {score:.2f}"

        cv2.putText(
            image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2
        )


# ------------------------------------------------
# resize
# ------------------------------------------------


def letter_box(im, new_shape):

    h, w = im.shape[:2]

    r = min(new_shape[0] / h, new_shape[1] / w)

    new_unpad = (int(w * r), int(h * r))

    im = cv2.resize(im, new_unpad)

    dw = new_shape[1] - new_unpad[0]
    dh = new_shape[0] - new_unpad[1]

    dw //= 2
    dh //= 2

    im = cv2.copyMakeBorder(
        im, dh, dh, dw, dw, cv2.BORDER_CONSTANT, value=(114, 114, 114)
    )

    return im, r, (dw, dh)


# ------------------------------------------------
# 主程序
# ------------------------------------------------

if __name__ == "__main__":

    rknn = RKNNLite()

    print("load model")

    rknn.load_rknn(rknn_model_path)

    print("init runtime")

    rknn.init_runtime(target=target, device_id=device_id)

    img_src = cv2.imread(img_path)

    img, ratio, (dw, dh) = letter_box(img_src, IMG_SIZE)

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    print("inference")

    outputs = rknn.inference(inputs=[img])

    boxes, classes, scores, seg_img = post_process(outputs)

    if boxes is not None:

        draw(img_src, boxes, scores, classes)

        cv2.imwrite("result.jpg", img_src)

        print("result saved")
