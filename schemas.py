from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# 資料模型
class Request(BaseModel):
    question: str
    location: str
    radius: int = 1000
    max_results: int = 5
    user_preferences: Optional[Dict[str, Any]] = None