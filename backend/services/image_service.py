import base64
import io
import os
from pathlib import Path
from PIL import Image
from openai import OpenAI


class ImageService:
    """图片识别服务层"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
        )
    
    def recognize_food(self, image_path: str) -> str:
        """
        调用API获取图片中的食物名称
        
        Args:
            image_path: 图片路径
            
        Returns:
            食物名称（逗号分隔）
        """
        b64_img = self._image_to_webp_b64(image_path)
        if not b64_img:
            raise RuntimeError("图片读取失败，请检查路径或格式")
        
        response = self.client.chat.completions.create(
            model=os.getenv("LLM_MODEL_VL"),
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
                            "text": "看一下这张图片里面有什么食材,只需要返回食材名称即可,用逗号隔开,其他的一律不要返回,如果里面没有食材则返回没有食材这四个字"
                        }
                    ]
                }
            ],
            stream=False,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def _image_to_webp_b64(self, path: str) -> str:
        """
        把任意本地图片转换为 WebP 格式并 base64 编码
        
        Args:
            path: 图片路径
            
        Returns:
            base64 编码的 WebP 图片
        """
        with Image.open(path) as img:
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=85)
            return base64.b64encode(buf.getvalue()).decode()
