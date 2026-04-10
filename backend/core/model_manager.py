import os
from huggingface_hub import HfApi, scan_cache_dir

MODEL_ALIASES = {
    "runwayml/stable-diffusion-v1-5": "🎨 SD 1.5 标准型 (万能王)",
    "Kwai-Kolors/Kolors": "🇨🇳 硅基 Kolors (最佳中文理解)",
    "stabilityai/stable-diffusion-xl-base-1.0": "📸 SDXL 高清版 (细节极佳)",
    "black-forest-labs/FLUX.1-schnell": "⚡ FLUX 极速版 (当前最强画质)",
    "dreamlike-art/dreamlike-diffusion-1.0": "🔮 梦幻插画风 (最适合奇幻生物)",
    "prompthero/openjourney": "🖼️ Midjourney 平替 (艺术感强)"
}

def search_market(query):
    if not query or not isinstance(query, str): query = "stable-diffusion"
    try:
        api = HfApi()
        models = api.list_models(filter="text-to-image", search=query, limit=12, sort="downloads", direction=-1)
        results = []
        for m in models:
            alias = MODEL_ALIASES.get(m.modelId, "🆕 社区新秀")
            results.append([m.modelId, alias, f"{m.downloads}", f"{m.likes}"])
        return results if results else [["无结果", "-", "-", "-"]]
    except Exception as e:
        return [[f"搜索错误: {str(e)}", "-", "-", "-"]]

def get_installed_gen_models():
    try:
        cache_info = scan_cache_dir()
        models = []
        for repo in cache_info.repos:
            if repo.repo_id not in ["u2net", "isnet-general-use", "sam", "silueta"]:
                models.append(repo.repo_id)
        return models
    except:
        return []

def get_installed_tools():
    s = []
    p = os.path.expanduser("~/.u2net")
    if os.path.exists(p):
        for f in os.listdir(p):
            if os.path.isfile(os.path.join(p, f)):
                size = os.path.getsize(os.path.join(p, f))/(1024*1024)
                s.append([f, f"{size:.1f} MB"])
    return s if s else [["-", "0 MB"]]
