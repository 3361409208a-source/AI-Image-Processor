import gradio as gr
from PIL import Image
import os
import sys

# 关键：确保能找到 core 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import load_config, save_config, search_market, get_installed_gen_models, get_installed_tools, MODEL_ALIASES
from core import run_t2i, run_i2i, remove_background

custom_css = """
.image-container img { background-image: conic-gradient(#eee 25%, white 0 50%, #eee 0 75%, white 0) !important; background-size: 20px 20px !important; }
.main-header { text-align: center; color: #2c3e50; padding: 10px; }
"""

def main():
    cfg = load_config()
    
    with gr.Blocks(title="AI 变异鱼工厂 V6.0 调试版", css=custom_css) as demo:
        with gr.Tabs():

            with gr.Tab("✍️ 文生图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        t2i_prompt = gr.Textbox(label="描述词", lines=4)
                        t2i_engine = gr.Radio(["SiliconFlow (云端)", "StableDiffusion (本地)"], value=cfg["preferred_provider"], label="引擎")
                        t2i_model = gr.Dropdown(choices=get_installed_gen_models() or ["runwayml/stable-diffusion-v1-5"], label="模型")
                        t2i_btn = gr.Button("🚀 测试生成", variant="primary")
                    with gr.Column(scale=1):
                        t2i_out = gr.Image(label="输出结果")
                t2i_btn.click(fn=run_t2i, inputs=[t2i_prompt, t2i_engine, gr.State(cfg["api_key"]), t2i_model], outputs=[t2i_out, gr.Markdown()])

            with gr.Tab("✂️ 智能抠图"):
                with gr.Row():
                    with gr.Column(scale=1):
                        cut_in = gr.Image(label="待处理图", type="pil")
                        cut_engine = gr.Dropdown(["u2net", "isnet-general-use", "sam", "silueta"], value="isnet-general-use", label="引擎")
                        cut_btn = gr.Button("✂️ 分离背景")
                    with gr.Column(scale=1):
                        cut_out = gr.Image(label="预览", elem_classes="image-container")
                        cut_file = gr.File(label="导出原档")
                cut_btn.click(fn=remove_background, inputs=[cut_in, cut_engine], outputs=[cut_out, cut_file])

            with gr.Tab("📦 资产管理"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🎨 本地模型仓")
                        gr.Dataframe(headers=["模型 ID", "状态"], value=[[m, "Ready"] for m in get_installed_gen_models()])
                    with gr.Column():
                        gr.Markdown("#### ✂️ 抠图工具箱")
                        gr.Dataframe(headers=["工具", "大小"], value=get_installed_tools())
                gr.Markdown("---")
                s_api = gr.Textbox(label="API Key", value=cfg["api_key"], type="password")
                s_save = gr.Button("💾 保存设置")
                s_save.click(fn=save_config, inputs=[s_api, t2i_engine], outputs=gr.Label())

    demo.launch(inbrowser=True)

if __name__ == "__main__":
    main()

