import torch
import requests
import io
import os
import time
from PIL import Image
from rembg import remove, new_session
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline

# 全局会话与模型缓存
sessions = {}
t2i_pipe = None
i2i_pipe = None

def get_rembg_session(model_name):
    if model_name not in sessions:
        sessions[model_name] = new_session(model_name)
    return sessions[model_name]

def remove_background(img, model_name):
    """核心抠图逻辑"""
    if img is None: return None, None
    img = img.convert("RGBA")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    output_data = remove(img_byte_arr.getvalue(), session=get_rembg_session(model_name))
    res_img = Image.open(io.BytesIO(output_data))
    
    os.makedirs("output", exist_ok=True)
    filename = f"asset_{int(time.time())}.png"
    save_path = os.path.abspath(os.path.join("output", filename))
    res_img.save(save_path, "PNG")
    return res_img, save_path

def run_t2i(prompt, provider, api_key, model_id):
    """文生图逻辑引擎"""
    if provider == "SiliconFlow (云端)":
        url = "https://api.siliconflow.cn/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_id,
            "prompt": prompt,
            "image_size": "1024x1024"
        }
        try:
            res = requests.post(url, json=payload, headers=headers).json()
            img_url = res['images'][0]['url']
            return Image.open(io.BytesIO(requests.get(img_url).content)), "Cloud Success"
        except Exception as e:
            return None, f"API 错误: {str(e)}"
    else:
        global t2i_pipe
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            if t2i_pipe is None or t2i_pipe.config._name_or_path != model_id:
                t2i_pipe = StableDiffusionPipeline.from_pretrained(
                    model_id, 
                    torch_dtype=torch.float16 if device=="cuda" else torch.float32
                ).to(device)
            return t2i_pipe(prompt, num_inference_steps=20).images[0], "本地生成成功"
        except Exception as e:
            return None, f"本地引擎错误: {str(e)}"

def run_i2i(image, prompt, provider, api_key, model_id):
    """图生图逻辑引擎"""
    if provider == "SiliconFlow (云端)":
        return None, "提示：云端 API 目前不开放图生图接口"
    else:
        global i2i_pipe
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            if i2i_pipe is None or i2i_pipe.config._name_or_path != model_id:
                i2i_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
                    model_id, 
                    torch_dtype=torch.float16 if device=="cuda" else torch.float32
                ).to(device)
            return i2i_pipe(prompt=prompt, image=image.convert("RGB"), strength=0.75).images[0], "本地图生图成功"
        except Exception as e:
            return None, f"图生图错误: {str(e)}"
