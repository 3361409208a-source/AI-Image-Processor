import gradio as gr
from PIL import Image
import os
import sys

# 关键：确保能找到 core 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import (
    load_config,
    save_config,
    search_market,
    get_installed_gen_models,
    get_installed_tools,
    MODEL_ALIASES,
)
from core import run_t2i, run_i2i, remove_background

CLOUD_MODELS = list(MODEL_ALIASES.keys())


def update_model_choices(engine):
    if engine == "SiliconFlow (云端)":
        return gr.Dropdown(choices=CLOUD_MODELS, value=CLOUD_MODELS[0])
    else:
        local_models = get_installed_gen_models()
        return gr.Dropdown(
            choices=local_models or ["无本地模型"],
            value=local_models[0] if local_models else None,
        )


custom_css = """
.image-container img { background-image: conic-gradient(#eee 25%, white 0 50%, #eee 0 75%, white 0) !important; background-size: 20px 20px !important; }
.main-header { text-align: center; color: #2c3e50; padding: 10px; }
"""


def select_local_file():
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")]
    )
    root.destroy()
    if file_path:
        file_path = os.path.abspath(file_path)
        try:
            img = Image.open(file_path)
            return file_path, img
        except Exception as e:
            return file_path, gr.update()
    return gr.update(), gr.update()


def save_and_replace_source(processed_img, source_path, upload_path):
    if processed_img is None:
        return "⚠️ 没有可保存的抠图结果，请先进行抠图处理。"
    
    # 1. 如果指定了源文件绝对路径（通过 选择本地文件 按钮获取）
    if source_path:
        source_path = source_path.strip('"\'')
        try:
            os.makedirs(os.path.dirname(os.path.abspath(source_path)), exist_ok=True)
            processed_img.save(source_path, "PNG")
            return f"✅ 已成功覆盖替换本地原文件：`{source_path}`"
        except Exception as e:
            return f"❌ 替换文件失败：{str(e)}"
            
    # 2. 如果没有指定源文件路径，但有上传时的临时文件路径，则保存到项目的 input 文件夹下，并替换同名文件
    if upload_path:
        try:
            filename = os.path.basename(upload_path)
            input_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "input"))
            os.makedirs(input_dir, exist_ok=True)
            target_path = os.path.join(input_dir, filename)
            processed_img.save(target_path, "PNG")
            return f"✅ 已保存并替换输入文件夹同名文件：`{target_path}`"
        except Exception as e:
            return f"❌ 保存到输入文件夹失败：{str(e)}"
            
    return "⚠️ 无法获取源文件路径，请先选择本地文件或上传图片。"


def on_remove_background(img_path, model_name):
    res_img, save_path = remove_background(img_path, model_name)
    if res_img is not None:
        return gr.update(value=res_img), gr.update(value=save_path, visible=True)
    return None, gr.update(visible=False)


def main():
    cfg = load_config()

    with gr.Blocks(title="AI 变异鱼工厂 V6.0 调试版", css=custom_css) as demo:
        source_path_state = gr.State("")
        with gr.Tabs():
            with gr.Tab("✍️ 文生图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        t2i_prompt = gr.Textbox(label="描述词", lines=4)
                        t2i_engine = gr.Radio(
                            ["SiliconFlow (云端)", "StableDiffusion (本地)"],
                            value=cfg["preferred_provider"],
                            label="引擎",
                        )
                        t2i_model = gr.Dropdown(
                            choices=CLOUD_MODELS,
                            value=CLOUD_MODELS[0],
                            label="模型",
                        )
                        t2i_engine.change(
                            fn=update_model_choices,
                            inputs=t2i_engine,
                            outputs=t2i_model,
                        )
                        t2i_btn = gr.Button("🚀 测试生成", variant="primary")
                    with gr.Column(scale=1):
                        t2i_out = gr.Image(label="输出结果")
                t2i_btn.click(
                    fn=run_t2i,
                    inputs=[
                        t2i_prompt,
                        t2i_engine,
                        gr.State(cfg["api_key"]),
                        t2i_model,
                    ],
                    outputs=[t2i_out, gr.Markdown()],
                )

            with gr.Tab("✂️ 智能抠图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        cut_in = gr.Image(label="待处理图 (支持拖拽上传或本地选择)", type="filepath", height=320)
                        select_local_btn = gr.Button("📂 选择本地文件 (直接支持替换)")
                        cut_engine = gr.Dropdown(
                            ["u2net", "isnet-general-use", "sam", "silueta"],
                            value="isnet-general-use",
                            label="抠图引擎",
                        )
                        cut_btn = gr.Button("✂️ 开始分离背景", variant="primary")
                        
                    with gr.Column(scale=1):
                        cut_out = gr.Image(label="抠图预览 (透明背景)", elem_classes="image-container", type="pil", height=320, interactive=False)
                        cut_file = gr.File(label="导出透明原档", visible=False)
                        save_replace_btn = gr.Button("💾 保存并替换源文件", variant="secondary")
                        save_status = gr.Markdown()
                
                select_local_btn.click(
                    fn=select_local_file,
                    outputs=[source_path_state, cut_in]
                )
                
                cut_btn.click(
                    fn=on_remove_background,
                    inputs=[cut_in, cut_engine],
                    outputs=[cut_out, cut_file],
                )
                
                save_replace_btn.click(
                    fn=save_and_replace_source,
                    inputs=[cut_out, source_path_state, cut_in],
                    outputs=[save_status],
                )

            with gr.Tab("📦 资产管理"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🎨 本地模型仓")
                        gr.Dataframe(
                            headers=["模型 ID", "状态"],
                            value=[[m, "Ready"] for m in get_installed_gen_models()],
                        )
                    with gr.Column():
                        gr.Markdown("#### ✂️ 抠图工具箱")
                        gr.Dataframe(
                            headers=["工具", "大小"], value=get_installed_tools()
                        )
                gr.Markdown("---")
                s_api = gr.Textbox(
                    label="API Key", value=cfg["api_key"], type="password"
                )
                s_save = gr.Button("💾 保存设置")
                s_save.click(
                    fn=save_config, inputs=[s_api, t2i_engine], outputs=gr.Label()
                )

    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
