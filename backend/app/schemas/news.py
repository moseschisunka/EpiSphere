from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NewsArticleBase(BaseModel):
    title: str
    summary: str
    content: str
    source: Optional[str] = None
    image_url: Optional[str] = None
    is_public: bool = True

class NewsArticleCreate(NewsArticleBase):
    pass

class NewsArticle(NewsArticleBase):
    id: int
    published_at: datetime

    model_config = ConfigDict(from_attributes=True)

