from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import io
from PIL import Image
import base64

# 导入咱们的核心逻辑 (相对引用)
from core import run_t2i, run_i2i, remove_background, load_config

app = FastAPI(title="AI 变异鱼工厂后端 API", version="6.0")

# 解决跨域问题，方便你的 TS 前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 定义数据结构 ---
class T2IRequest(BaseModel):
    prompt: str
    provider: str = "SiliconFlow (云端)"
    model_id: str = "Kwai-Kolors/Kolors"
    api_key: Optional[str] = None

class ResponseModel(BaseModel):
    image_base64: str
    message: str

# --- 辅助函数：将 PIL 转为 Base64 ---
def img_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# --- 路由定义 ---

@app.get("/")
async def root():
    return {"status": "Online", "message": "AI 资产流水线后端已就绪"}

@app.post("/api/t2i", response_model=ResponseModel)
async def api_t2i(req: T2IRequest):
    cfg = load_config()
    key = req.api_key or cfg.get("api_key", "")
    
    img, msg = run_t2i(req.prompt, req.provider, key, req.model_id)
    if img:
        return {"image_base64": img_to_base64(img), "message": msg}
    raise HTTPException(status_code=500, detail=msg)

@app.post("/api/remove_bg")
async def api_remove_bg(file: UploadFile = File(...), engine: str = Form("isnet-general-use")):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        res_img, _ = remove_background(img, engine)
        return {"image_base64": img_to_base64(res_img), "message": "Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 启动服务器，默认端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
