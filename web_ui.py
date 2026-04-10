import gradio as gr
from rembg import remove, new_session
from PIL import Image
import io
import os
import torch
import json
import requests
import time
from huggingface_hub import HfApi

# 配置管理
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"api_key": "", "preferred_provider": "SiliconFlow (云端)"}

def save_config(api_key, provider):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"api_key": api_key, "preferred_provider": provider}, f)
    return "✅ 配置已保存"

# 全局缓存
sessions = {}
t2i_pipe = None

def get_session(model_name):
    if model_name not in sessions:
        sessions[model_name] = new_session(model_name)
    return sessions[model_name]

def load_local_sd(custom_model_id=None):
    global t2i_pipe
    model_id = custom_model_id if custom_model_id else "runwayml/stable-diffusion-v1-5"
    try:
        from diffusers import StableDiffusionPipeline
        print(f"[*] Loading Local Model: {model_id}...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        t2i_pipe = StableDiffusionPipeline.from_pretrained(
            model_id, 
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        t2i_pipe.to(device)
        return t2i_pipe
    except Exception as e:
        print(f"Error loading model {model_id}: {e}")
        return None

def generate_via_siliconflow(prompt, api_key, custom_model=None):
    if not api_key: return None, "Error: 请先填入 API Key"
    url = "https://api.siliconflow.cn/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    actual_model = custom_model if custom_model and "/" in custom_model else "Kwai-Kolors/Kolors"
    payload = {
        "model": actual_model,
        "prompt": f"{prompt}, white background, centered, game asset",
        "image_size": "1024x1024",
        "batch_size": 1
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        img_url = data['images'][0]['url']
        img_res = requests.get(img_url)
        return Image.open(io.BytesIO(img_res.content)), f"Cloud ({actual_model}) Success"
    except Exception as e:
        return None, f"API Error: {str(e)}"

def process_image_logic(img, model_name):
    if img is None: return None
    img = img.convert("RGBA")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    input_data = img_byte_arr.getvalue()
    output_data = remove(input_data, session=get_session(model_name))
    res_img = Image.open(io.BytesIO(output_data))
    os.makedirs("output", exist_ok=True)
    save_path = f"output/processed_{int(time.time())}.png"
    res_img.save(save_path, "PNG")
    return res_img

def hf_search(query):
    try:
        api = HfApi()
        models = api.list_models(filter="text-to-image", search=query, limit=10, sort="downloads", direction=-1)
        results = []
        for m in models:
            results.append([m.modelId, f"{m.downloads}", f"{m.likes}", "Text-to-Image"])
        return results if results else [["无结果", "-", "-", "-"]]
    except Exception as e:
        return [[f"搜索错误: {str(e)}", "-", "-", "-"]]

def get_local_models():
    s = []
    p = os.path.expanduser("~/.u2net")
    if os.path.exists(p):
        for f in os.listdir(p):
            if os.path.isfile(os.path.join(p, f)):
                size = os.path.getsize(os.path.join(p, f))/(1024*1024)
                s.append([f, f"{size:.1f} MB"])
    return s if s else [["-", "0 MB"]]

# CSS 棋盘格
custom_css = """
.image-container img { background-image: conic-gradient(#eee 25%, white 0 50%, #eee 0 75%, white 0) !important; background-size: 20px 20px !important; }
.gradio-container { background-color: #f7f7f7; }
"""

def main():
    config = load_config()
    with gr.Blocks(title="AI 素材创作工坊 V3.9") as demo:
        gr.Markdown("# 🧪 AI 变异鱼工厂 V3.9 (全自动商店版)")
        
        with gr.Row():
            model_selector = gr.Dropdown(choices=["u2net", "isnet-general-use", "sam", "silueta"], value="u2net", label="抠图精度引擎")
            provider_selector = gr.Radio(choices=["SiliconFlow (云端)", "StableDiffusion (本地)"], value=config["preferred_provider"], label="生图供应方")

        with gr.Tab("✨ 自动生产线"):
            with gr.Row():
                with gr.Column(scale=1):
                    prompt_input = gr.Textbox(label="1. 描述核心生物", placeholder="机械鱼, 巨齿鲨, 蒸汽朋克...", lines=3)
                    with gr.Row():
                        cloud_model_dropdown = gr.Dropdown(
                            choices=["Kwai-Kolors/Kolors", "stabilityai/stable-diffusion-xl-base-1.0", "black-forest-labs/FLUX.1-schnell"],
                            value="Kwai-Kolors/Kolors",
                            label="☁️ 云端/自定义 ID",
                            allow_custom_value=True
                        )
                    with gr.Row():
                        gen_only_btn = gr.Button("🖼️ 仅生成原图")
                        gen_and_bg_btn = gr.Button("🔥 生成并抠图", variant="primary")
                    status_out = gr.Textbox(label="执行状态", interactive=False)
                    api_key_hidden = gr.Textbox(value=config["api_key"], visible=False)

                with gr.Column(scale=1):
                    raw_output = gr.Image(label="生成结果", type="pil")
                    process_btn = gr.Button("✂️ 对该图执行抠图", variant="secondary")
                    final_output = gr.Image(label="最终透明素材", type="pil", elem_classes="image-container")

            def generate_only_fn(prompt, provider, api_key, custom_val):
                if provider == "SiliconFlow (云端)":
                    img, msg = generate_via_siliconflow(prompt, api_key, custom_val)
                else:
                    pipe = load_local_sd(custom_val)
                    if not pipe: return None, "模型加载失败"
                    img = pipe(f"{prompt}, white background", num_inference_steps=20).images[0]
                    msg = "本地生成成功"
                return img, msg

            def full_pipeline_fn(prompt, provider, model_name, api_key, custom_val):
                img, msg = generate_only_fn(prompt, provider, api_key, custom_val)
                if img:
                    res = process_image_logic(img, model_name)
                    return img, res, f"流水线完成: {msg}"
                return None, None, msg

            gen_only_btn.click(fn=generate_only_fn, inputs=[prompt_input, provider_selector, api_key_hidden, cloud_model_dropdown], outputs=[raw_output, status_out])
            gen_and_bg_btn.click(fn=full_pipeline_fn, inputs=[prompt_input, provider_selector, model_selector, api_key_hidden, cloud_model_dropdown], outputs=[raw_output, final_output, status_out])
            process_btn.click(fn=process_image_logic, inputs=[raw_output, model_selector], outputs=final_output)

        with gr.Tab("🛒 全球模型市场"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 快速分类")
                    with gr.Row():
                        btn_c = gr.Button("🦁 生物", size="sm")
                        btn_m = gr.Button("🤖 机械", size="sm")
                    search_q = gr.Textbox(label="自由搜索", placeholder="输入关键词...")
                    s_btn = gr.Button("搜索广场")
                with gr.Column(scale=2):
                    market_results = gr.Dataframe(headers=["模型 ID", "下载量", "点赞数", "类型"], interactive=True)
                    sel_id = gr.Textbox(label="选中的模型 ID", interactive=False)
                    dl_market_btn = gr.Button("📥 一键下载到本地", variant="primary")
                    market_status = gr.Markdown("状态：就绪")

        with gr.Tab("📦 本地仓库"):
            with gr.Row():
                gr.Button("📂 打开抠图模型目录").click(fn=lambda: os.startfile(os.path.expanduser("~/.u2net")))
                gr.Button("📂 打开 AI 权重目录").click(fn=lambda: os.startfile(os.path.expanduser("~/.cache/huggingface/hub")))
            local_table = gr.Dataframe(headers=["文件名", "体积MB"], value=get_local_models())
            refresh_btn = gr.Button("🔄 刷新列表")

        # 核心交互逻辑 (修复 UnboundLocalError)
        s_btn.click(fn=hf_search, inputs=search_q, outputs=market_results)
        btn_c.click(fn=lambda: hf_search("monster creature"), outputs=market_results)
        btn_m.click(fn=lambda: hf_search("mech robot"), outputs=market_results)
        market_results.select(fn=lambda e: e.value if e.index[1]==0 else gr.skip(), outputs=sel_id)

        def start_market_dl(m_id):
            if not m_id: return "请先点选 ID", gr.skip()
            yield f"⏳ 正在后台下载 {m_id}...", gr.skip()
            load_local_sd(m_id)
            yield f"✅ 下载完成: {m_id}", get_local_models()

        dl_market_btn.click(fn=start_market_dl, inputs=sel_id, outputs=[market_status, local_table])
        refresh_btn.click(fn=get_local_models, outputs=local_table)
        demo.load(fn=get_local_models, outputs=local_table)
        demo.load(fn=lambda: hf_search("stable-diffusion"), outputs=market_results)

        with gr.Tab("⚙ 设置"):
            api_input = gr.Textbox(label="SiliconFlow API Key", value=config["api_key"], type="password")
            prov_input = gr.Radio(choices=["SiliconFlow (云端)", "StableDiffusion (本地)"], value=config["preferred_provider"], label="生图供应方")
            gr.Button("保存配置").click(fn=save_config, inputs=[api_input, prov_input], outputs=gr.Label())

    demo.launch(inbrowser=True, css=custom_css)

if __name__ == "__main__":
    main()
