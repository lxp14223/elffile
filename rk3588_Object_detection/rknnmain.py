import cv2
from rknnlite.api import RKNNLite
from func import myFunc


class RKNNImageInfer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.rknn = None

    def load_model(self):
        """加载 RKNN 模型"""
        self.rknn = RKNNLite()

        ret = self.rknn.load_rknn(self.model_path)
        if ret != 0:
            raise RuntimeError("Load RKNN model failed")

        ret = self.rknn.init_runtime()
        if ret != 0:
            raise RuntimeError("Init runtime failed")

        print("RKNN init done")

    def infer(self, img):
        """对单张图片进行推理"""
        if self.rknn is None:
            raise RuntimeError("Model not loaded")

        return myFunc(self.rknn, img)

    def infer_path(self, img_path):
        """输入图片路径进行推理"""
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError(f"Image load failed: {img_path}")

        result = self.infer(img)
        return result

    def save(self, img, save_path):
        """保存结果"""
        cv2.imwrite(save_path, img)
        print(f"Result saved to: {save_path}")

    def show(self, img, win_name="result"):
        """显示结果"""
        cv2.imshow(win_name, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def release(self):
        """释放资源"""
        if self.rknn:
            self.rknn.release()
            print("RKNN released")


if __name__ == "__main__":
    model_path = "./rknnModel/yolov8s_seg.rknn"
    img_path = "./bus.jpg"
    save_path = "./result.jpg"

    infer = RKNNImageInfer(model_path)

    # 初始化模型
    infer.load_model()

    # 推理
    result = infer.infer_path(img_path)

    # 保存 + 显示
    infer.save(result, save_path)
    infer.show(result)

    # 释放资源
    infer.release()
