import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import asyncio
import cv2
from PIL import Image, ImageTk
import numpy as np
import os
import sys
import datetime
from utils.tagger import modelLoad, analysis
from utils.request_api import create_and_save_images, get_model, set_model, get_controlnet_model


if getattr(sys, 'frozen', False):
    # PyInstaller でビルドされた場合
    dpath = os.path.dirname(sys.executable)
else:
    # 通常の Python スクリプトとして実行された場合
    dpath = os.path.dirname(sys.argv[0])

model = None
fastapi_url = None


def canny_process(image_path, threshold1, threshold2):
    img_pil = Image.open(image_path).convert('RGBA')
    img = np.array(img_pil)  # PIL画像をNumPy配列に変換
    
    alpha_channel = img[:, :, 3]
    # RGBチャンネルを取得
    rgb_channels = img[:, :, :3]
        
    # アルファチャンネルで透明部分を白にする
    # アルファチャンネルが0の部分は白に、それ以外は元の色を使う
    white_background = np.ones_like(rgb_channels, dtype=np.uint8) * 255
    # アルファチャンネルを基に背景を合成
    white_background = cv2.bitwise_not(white_background, mask=alpha_channel)
    background = cv2.bitwise_or(white_background, white_background, mask=alpha_channel)
    foreground = cv2.bitwise_and(rgb_channels, rgb_channels, mask=alpha_channel)
    combined = cv2.add(foreground, background)
    
    # RGBA形式からRGB形式に変換
    combined = cv2.cvtColor(combined, cv2.COLOR_RGBA2RGB)
    
    # グレースケール変換
    gray = cv2.cvtColor(combined, cv2.COLOR_RGB2GRAY)
    # Cannyエッジ検出
    edges = cv2.Canny(gray, threshold1, threshold2)
    
    return edges

def resize_image_aspect_ratio(image, max_length=1200):
    # 元の画像サイズを取得
    original_width, original_height = image.size

    # アスペクト比を計算
    aspect_ratio = original_width / original_height

    # 長辺がmax_lengthになるように新しいサイズを計算
    if original_width > original_height:
        new_width = max_length
        new_height = round(max_length / aspect_ratio)
    else:
        new_height = max_length
        new_width = round(max_length * aspect_ratio)

    # 新しいサイズで画像をリサイズ
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized_image


class Application(TkinterDnD.Tk):
    def __init__(self, fastapi_url=None):
        super().__init__()
        self.fastapi_url = fastapi_url
        self.title("Line2Normalmap")
        self.geometry("600x600")
        self.image_path = None
        self.canny_pil = None
        self.tab_control = ttk.Notebook(self)
        self.line_input_tab = tk.Frame(self.tab_control)
        self.canny_input_tab = tk.Frame(self.tab_control)
        self.image_output_tab = tk.Frame(self.tab_control)
        self.tab_control.add(self.line_input_tab, text='①線画入力')
        self.tab_control.add(self.canny_input_tab, text='②canny入力')
        self.tab_control.add(self.image_output_tab, text='③画像出力')
        self.tab_control.pack(expand=1, fill="both")
        self.setup_line_input_tab()
        self.setup_canny_input_tab()
        self.setup_image_output_tab()
        self.setup_drag_and_drop()
        self.sd_model_names = None
        self.sd_current_model_name = None

    def setup_line_input_tab(self):
        self.prompt_label = tk.Label(self.line_input_tab, text="Prompt:")
        self.prompt_label.pack()
        self.prompt_text = tk.Text(self.line_input_tab, width=60, height=3, wrap=tk.WORD)
        self.prompt_text.pack()
        self.analyze_prompt_button = tk.Button(self.line_input_tab, text="Prompt解析", command=self.analyze_prompt)
        self.analyze_prompt_button.pack()

    def setup_canny_input_tab(self):
        self.threshold1_slider = tk.Scale(self.canny_input_tab, from_=0, to=255, label="Threshold1", orient="horizontal")
        self.threshold1_slider.set(20)
        self.threshold1_slider.pack()
        self.threshold2_slider = tk.Scale(self.canny_input_tab, from_=0, to=255, label="Threshold2", orient="horizontal")
        self.threshold2_slider.set(120)
        self.threshold2_slider.pack()
        tk.Button(self.canny_input_tab, text="Canny加工", command=self.apply_canny).pack()
        self.clear_canny_button = tk.Button(self.canny_input_tab, text="Canny画像消去", command=self.clear_canny)
        self.clear_canny_button.pack()

    def setup_image_output_tab(self):
        self.sd_model_names, self.sd_current_model_name = get_model(self.fastapi_url)
        self.model_label = tk.Label(self.image_output_tab, text="モデル選択:")
        self.model_label.pack()
        # モデル選択プルダウンメニューを作成
        self.model_variable = tk.StringVar(self.image_output_tab)
        self.model_dropdown = tk.OptionMenu(self.image_output_tab, self.model_variable, *self.sd_model_names)
        self.model_dropdown.pack()
        # プルダウンメニューの選択が変更された時に呼び出される関数を登録
        self.model_variable.trace("w", self.on_model_selected)

        self.prompt_label = tk.Label(self.image_output_tab, text="Prompt:")
        self.prompt_label.pack()
        self.prompt_entry = tk.Text(self.image_output_tab, width=60, height=3, wrap=tk.WORD)
        self.prompt_entry.pack()
        self.negative_prompt_label = tk.Label(self.image_output_tab, text="Negative Prompt:")
        self.negative_prompt_label.pack()
        self.negative_prompt_entry = tk.Text(self.image_output_tab, width=60, height=3, wrap=tk.WORD)
        self.negative_prompt_entry.pack()
        negative = "lowres, error, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts,  blurry"
        self.negative_prompt_entry.insert(tk.END, negative)
        self.lineart_fidelity_label = tk.Label(self.image_output_tab, text="線画忠実度（1.0-1.5）:")
        self.lineart_fidelity_label.pack()
        self.lineart_fidelity = tk.DoubleVar(value=1.0)
        self.lineart_fidelity_slider = tk.Scale(self.image_output_tab, from_=1.0, to=1.5, resolution=0.05, orient=tk.HORIZONTAL, variable=self.lineart_fidelity)
        self.lineart_fidelity_slider.pack() 
        self.generate_image_button = tk.Button(self.image_output_tab, text="画像生成", command=self.generate_image)
        self.generate_image_button.pack()


    def on_model_selected(self, *args):
        self.sd_current_model_name = get_model(self.fastapi_url)
        self.selected_model = self.model_variable.get()

    def show_processed_image(self, img):
        # PILライブラリを使用してNumPy配列から画像を作成
        image = Image.fromarray(img)

        # アスペクト比を保ちつつ、長辺が400ピクセルになるようにリサイズする処理
        original_width, original_height = image.size
        max_length = 400

        # アスペクト比を計算
        aspect_ratio = original_width / original_height

        # 長辺が400ピクセルになるように新しいサイズを計算
        if original_width > original_height:
            new_width = max_length
            new_height = round(max_length / aspect_ratio)
        else:
            new_height = max_length
            new_width = round(max_length * aspect_ratio)

        # 新しいサイズで画像をリサイズ
        image_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # リサイズした画像をTkinter用のPhotoImageに変換
        photo = ImageTk.PhotoImage(image_resized)

        # 現在選択されているタブを取得
        current_tab = self.tab_control.nametowidget(self.tab_control.select())

        # 以前に表示した画像があれば削除
        if hasattr(current_tab, 'image_label'):
            current_tab.image_label.pack_forget()
            current_tab.image_label.destroy()

        # 新しい画像を表示するLabelを作成して配置
        current_tab.image_label = tk.Label(current_tab, image=photo)
        current_tab.image_label.image = photo  # 参照を保持しておかないと画像が表示されなくなる
        current_tab.image_label.pack()


    def clear_processed_image(self):
        current_tab = self.tab_control.nametowidget(self.tab_control.select())
        if hasattr(current_tab, 'image_label'):
            current_tab.image_label.pack_forget()
            current_tab.image_label.destroy()
            delattr(current_tab, 'image_label')  # この行を追加

    def setup_drag_and_drop(self):
        for tab in [self.line_input_tab, self.canny_input_tab]:
            tab.drop_target_register(DND_FILES)
            tab.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        files = self.parse_dropped_files(event.data)
        if files:
            try:
                self.image_path = files[0].encode('utf-8').decode(sys.getfilesystemencoding())
            except UnicodeEncodeError as e:
                print(f"Error processing file name: {e}")
                return
            self.load_image(self.image_path)
        
    def parse_dropped_files(self, data):
        files = data.split()
        return [file.replace('{', '').replace('}', '') for file in files]

    def load_image(self, image_path):
        self.image_path = image_path  # 画像パスを更新する

        img = Image.open(self.image_path).convert("RGBA")
        canvas = Image.new('RGBA', img.size, (255, 255, 255, 255))  # 白背景のキャンバスを作成
        img = Image.alpha_composite(canvas, img)
        img = img.convert("RGB")  # 最終的な画像をRGB形式に変換

        # アスペクト比を保ちつつ、長辺が400ピクセルになるようにリサイズ
        max_size = (400, 400)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 長辺を400にするためのリサイズ処理
        original_size = img.size
        ratio = float(max_size[0]) / max(original_size)
        new_size = tuple([int(x * ratio) for x in original_size])
        photo_img = img.resize(new_size, Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(photo_img)

        current_tab = self.tab_control.nametowidget(self.tab_control.select())

        # 既存のimage_labelがある場合、新しい画像で更新する
        if hasattr(current_tab, 'image_label'):
            current_tab.image_label.configure(image=photo)
            current_tab.image_label.image = photo
        else:
            current_tab.image_label = tk.Label(current_tab, image=photo)
            current_tab.image_label.image = photo
            current_tab.image_label.pack()

        # 画像の種類に応じて適切な変数を更新
        if current_tab == self.canny_input_tab:
            self.canny_pil = img  # Canny用PIL画像を更新

    def analyze_prompt(self):
        global model
        model_dir = os.path.join(dpath, 'models/tagger')
        if model is None:
            model = modelLoad(model_dir)
        image_path = self.image_path 
        tag = analysis(image_path, model_dir, model)
        execute_tags = ["monochrome", "greyscale", "lineart", "white background"]
        tag_list = tag.split(", ")
        filtered_tags = [t for t in tag_list if t not in execute_tags]
        new_tag = ", ".join(filtered_tags)
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_entry.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", new_tag)
        self.prompt_entry.insert("1.0", new_tag)

    def apply_canny(self):
        if self.image_path is None:
            return
        threshold1 = self.threshold1_slider.get()
        threshold2 = self.threshold2_slider.get()
        canny = canny_process(self.image_path, threshold1, threshold2)
        self.canny_pil = Image.fromarray(cv2.cvtColor(canny, cv2.COLOR_GRAY2RGB))  # Canny結果をPIL画像として保存
        self.show_processed_image(canny)

    def clear_canny(self):
        self.clear_processed_image()
        self.canny_pil = None

    def generate_image(self):
        output_dir = os.path.join(dpath, "output/")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # self.image_path.splitから拡張子なしの画像の名前部分を抽出
        img_name = os.path.splitext(os.path.basename(self.image_path))[0]
        # 日時の文字列からファイル名として無効な文字を置換
        dt_now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = os.path.join(output_dir, img_name + "_" + dt_now + ".png")
        prompt = "normal map, " + self.prompt_entry.get("1.0", tk.END).strip()
        nega = self.negative_prompt_entry.get("1.0", tk.END).strip()
        lineart_fidelity = float(self.lineart_fidelity_slider.get())

        if self.canny_pil is None:
            self.canny_pil = Image.fromarray(cv2.cvtColor(canny_process(self.image_path, 20, 120), cv2.COLOR_GRAY2RGB))
        self.canny_pil = resize_image_aspect_ratio(self.canny_pil, 1200)
        output_pil = create_and_save_images(self.fastapi_url, prompt, nega, self.canny_pil, lineart_fidelity, output_path)
        output_np = np.array(output_pil)
        self.show_processed_image(output_np)

def start(fastapi_url):
    app = Application(fastapi_url)
    app.mainloop()