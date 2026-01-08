import base64, io, os
from PIL import Image
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("SILICONFLOW_API_KEY"),   # 硅基流动后台复制
    base_url=os.getenv("LLM_BASE_URL"),
)

def get_food_name(image_path: str) -> str:
    """调用API获取图片中的食物名称"""
    # 1. 把任意本地图片 → WebP → base64
    b64_img = image_to_webp_b64(image_path)
    if not b64_img:
        raise RuntimeError("图片读取失败，请检查路径或格式")
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL_VL"),      # 模型名严格按官网填写
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/webp;base64,{b64_img}",
                            "detail": "high"
                        }
                    },
                    {
                        "type": "text",
                        "text": "看一下这张图片里面有什么食材,只需要返回食材名称即可,\
                        用逗号隔开,其他的一律不要返回,如果里面没有食材则返回没有食材这四个字"
                    }
                ]
            }
        ],
        stream=False,      # 改为 False，一次性返回结果
        max_tokens=1000
    )
    return response.choices[0].message.content

# 2. 把任意本地图片 → WebP → base64
def image_to_webp_b64(path: str) -> str:
    with Image.open(path) as img:
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=85)   # 体积/清晰度折中
        return base64.b64encode(buf.getvalue()).decode()




  