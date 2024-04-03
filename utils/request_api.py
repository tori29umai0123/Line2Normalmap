import requests
import json
import base64
from datetime import datetime
import os
import itertools
import random
import re
from PIL import Image, PngImagePlugin, ImageEnhance, ImageFilter, ImageOps
import io
import glob
import cv2


def build_payload(prompt, nega, w, h, unit1):
    return {
        "prompt": prompt,
        "negative_prompt": nega,
        "seed": -1,
        "sampler_name": "Euler a",
        "steps": 20,
        "cfg_scale": 7,
        "width": w,
        "height": h,
        "alwayson_scripts": {"ControlNet": {"args": [unit1]}},
    }        

def send_post_request(url, payload):
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response


def save_image(data, url, file_name):
    image_string = data["images"][0]
    image_bytes = base64.b64decode(image_string)

    png_payload = {
        "image": "data:image/png;base64," + image_string
    }
    response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
    image_info = response2.json().get("info")

    image = Image.open(io.BytesIO(image_bytes))
    pnginfo = PngImagePlugin.PngInfo()
    if image_info:  # Ensure image_info is not None
        pnginfo.add_text("parameters", image_info)

    image.save(file_name, pnginfo=pnginfo)
    return image


def create_and_save_images(input_url, prompt, nega, canny_pil, lineart_fidelity, output_path):
    url = f"{input_url}/sdapi/v1/txt2img"
    w, h = canny_pil.size
    canny_bytes = io.BytesIO()
    canny_pil.save(canny_bytes, format='PNG')
    encoded_canny = base64.b64encode(canny_bytes.getvalue()).decode('utf-8')
    
    prompt = "masterpiece, best quality, SimplepositiveXLv1 <lora:sdxl-testlora-normalmap_04b_dim32:1.2>, " + prompt
    unit1 = {
        "image": encoded_canny,
        "mask_image": None,
        "control_mode": "Balanced",
        "enabled": True,
        "guidance_end": 1,
        "guidance_start": 0,
        "pixel_perfect": True,
        "processor_res": 1200,
        "resize_mode": "Just Resize",  # "Just Resize", "Crop and Resize", "Resize and Fill"
        "threshold_a": 64,
        "threshold_b": 64,
        "weight": lineart_fidelity,
        "module": "canny",
        "model": "control-lora-canny-rank256 [ec2dbbe4]",
        "save_detected_map": None,
        "hr_option": "Both"
    }    


    payload = build_payload(prompt, nega, w, h, unit1)
    response = send_post_request(url, payload)
    image_data = response.json()

    if "images" in image_data and image_data["images"]:
        output_pil = save_image(image_data, input_url, output_path)
        print(f"Downloaded {output_path} to local")
        return output_pil
    else:
        print("Failed to generate image. 'images' key not found in the response.")

def get_model(url):
    sd_models = requests.get(f"{url}/sdapi/v1/sd-models").json()
    sd_model_names = [i["title"] for i in sd_models]
    current_model_name = requests.get(f"{url}/sdapi/v1/options").json()["sd_model_checkpoint"]
    return sd_model_names, current_model_name

def get_controlnet_model(url):
    cn_models = requests.get(f"{url}/controlnet/model_list").json()
    return cn_models

def set_model(url, sd_model_name):
    option_payload = {
        "sd_model_checkpoint":sd_model_name,
    }
    response = requests.post(url=f'{url}/sdapi/v1/options', json=option_payload)