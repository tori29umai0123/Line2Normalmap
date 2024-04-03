# -*- coding: utf-8 -*-
# https://github.com/kohya-ss/sd-scripts/blob/main/finetune/tag_images_by_wd14_tagger.py

import csv
import os
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'

from PIL import Image
import cv2
import numpy as np
from pathlib import Path
import onnx
import onnxruntime as ort

# from wd14 tagger
IMAGE_SIZE = 448

model = None  # Initialize model variable


def convert_array_to_bgr(array):
    """
    Convert a NumPy array image to BGR format regardless of its original format.
    
    Parameters:
    - array: NumPy array of the image.
    
    Returns:
    - A NumPy array representing the image in BGR format.
    """
    # グレースケール画像（2次元配列）
    if array.ndim == 2:
        # グレースケールをBGRに変換（3チャンネルに拡張）
        bgr_array = np.stack((array,) * 3, axis=-1)
    # RGBAまたはRGB画像（3次元配列）
    elif array.ndim == 3:
        # RGBA画像の場合、アルファチャンネルを削除
        if array.shape[2] == 4:
            array = array[:, :, :3]
        # RGBをBGRに変換
        bgr_array = array[:, :, ::-1]
    else:
        raise ValueError("Unsupported array shape.")

    return bgr_array


def preprocess_image(image):
    image = np.array(image)
    image = convert_array_to_bgr(image)

    size = max(image.shape[0:2])
    pad_x = size - image.shape[1]
    pad_y = size - image.shape[0]
    pad_l = pad_x // 2
    pad_t = pad_y // 2
    image = np.pad(image, ((pad_t, pad_y - pad_t), (pad_l, pad_x - pad_l), (0, 0)), mode="constant", constant_values=255)

    interp = cv2.INTER_AREA if size > IMAGE_SIZE else cv2.INTER_LANCZOS4
    image = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE), interpolation=interp)

    image = image.astype(np.float32)
    return image

def modelLoad(model_dir):
    onnx_path = os.path.join(model_dir, "model.onnx")
    # 実行プロバイダーをCPUのみに指定
    providers = ['CPUExecutionProvider']
    # InferenceSessionの作成時にプロバイダーのリストを指定
    ort_session = ort.InferenceSession(onnx_path, providers=providers)
    input_name = ort_session.get_inputs()[0].name
    
    # 実際に使用されているプロバイダーを取得して表示
    actual_provider = ort_session.get_providers()[0]  # 使用されているプロバイダー
    print(f"Using provider: {actual_provider}")
    
    return [ort_session, input_name]

def analysis(image_path, model_dir, model):
    ort_session = model[0]
    input_name = model[1]

    with open(os.path.join(model_dir, "selected_tags.csv"), "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        l = [row for row in reader]
        header = l[0]  # tag_id,name,category,count
        rows = l[1:]
    assert header[0] == "tag_id" and header[1] == "name" and header[2] == "category", f"unexpected csv format: {header}"

    general_tags = [row[1] for row in rows[1:] if row[2] == "0"]
    character_tags = [row[1] for row in rows[1:] if row[2] == "4"]

    tag_freq = {}
    undesired_tags = []

    # 画像をロードして前処理する
    image_pil = Image.open(image_path).convert("RGB")

    image_preprocessed = preprocess_image(image_pil)
    image_preprocessed = np.expand_dims(image_preprocessed, axis=0)

    # 推論を実行
    prob = ort_session.run(None, {input_name: image_preprocessed})[0][0]
    # タグを生成
    combined_tags = []
    general_tag_text = ""
    character_tag_text = ""
    remove_underscore = True
    caption_separator = ", "
    general_threshold = 0.35
    character_threshold = 0.35

    for i, p in enumerate(prob[4:]):
        if i < len(general_tags) and p >= general_threshold:
            tag_name = general_tags[i]
            if remove_underscore and len(tag_name) > 3:  # ignore emoji tags like >_< and ^_^
                tag_name = tag_name.replace("_", " ")

            if tag_name not in undesired_tags:
                tag_freq[tag_name] = tag_freq.get(tag_name, 0) + 1
                general_tag_text += caption_separator + tag_name
                combined_tags.append(tag_name)
        elif i >= len(general_tags) and p >= character_threshold:
            tag_name = character_tags[i - len(general_tags)]
            if remove_underscore and len(tag_name) > 3:
                tag_name = tag_name.replace("_", " ")

            if tag_name not in undesired_tags:
                tag_freq[tag_name] = tag_freq.get(tag_name, 0) + 1
                character_tag_text += caption_separator + tag_name
                combined_tags.append(tag_name)

    # 先頭のカンマを取る
    if len(general_tag_text) > 0:
        general_tag_text = general_tag_text[len(caption_separator) :]
    if len(character_tag_text) > 0:
        character_tag_text = character_tag_text[len(caption_separator) :]
    tag_text = caption_separator.join(combined_tags)
    return tag_text