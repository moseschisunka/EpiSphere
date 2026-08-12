from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.db.models import AuditAction, AuditLog, NewsArticle, User
from app.schemas import news as news_schema
from app.api.v1.deps import allow_admin
from app.core.limiter import limiter

router = APIRouter()


@router.get("", response_model=List[news_schema.NewsArticle])
def list_news_articles(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List public health news articles."""
    query = db.query(NewsArticle).filter(NewsArticle.is_public.is_(True))
    if search:
        query = query.filter(
            (NewsArticle.title.ilike(f"%{search}%")) | 
            (NewsArticle.summary.ilike(f"%{search}%"))
        )
    return query.order_by(NewsArticle.published_at.desc()).offset(skip).limit(limit).all()


@router.get("/admin", response_model=List[news_schema.NewsArticle])
def list_admin_news_articles(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin),
):
    """List all news articles, including drafts, for administrators."""
    query = db.query(NewsArticle)
    if search:
        query = query.filter(
            (NewsArticle.title.ilike(f"%{search}%")) |
            (NewsArticle.summary.ilike(f"%{search}%"))
        )
    return query.order_by(NewsArticle.published_at.desc()).offset(skip).limit(limit).all()


@router.get("/{article_id}", response_model=news_schema.NewsArticle)
def get_news_article(article_id: int, db: Session = Depends(get_db)):
    """Get article details by ID."""
    article = db.query(NewsArticle).filter(
        NewsArticle.id == article_id,
        NewsArticle.is_public.is_(True),
    ).first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")
    return article


from app.core.dependencies import get_news_agent_or_admin

@router.post("", response_model=news_schema.NewsArticle)
@limiter.limit("30/minute")
def create_news_article(
    request: Request,
    article_in: news_schema.NewsArticleCreate,
    db: Session = Depends(get_db),
    agent_or_admin = Depends(get_news_agent_or_admin)
):
    """Create a new health news article (Admin or Agent only)."""
    article = NewsArticle(
        title=article_in.title,
        summary=article_in.summary,
        content=article_in.content,
        source=article_in.source or "EpiSphere Health Network",
        image_url=article_in.image_url,
        is_public=article_in.is_public,
        published_at=datetime.utcnow()
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    actor = agent_or_admin if hasattr(agent_or_admin, "name") else None
    db.add(AuditLog(
        user_id=agent_or_admin.id if isinstance(agent_or_admin, User) else None,
        action=AuditAction.CREATE,
        resource_type="news_article",
        resource_id=article.id,
        details={
            "actor": actor.name if actor else "admin",
            "auth_method": actor.auth_method if actor else "bearer",
            "request_id": getattr(request.state, "request_id", None),
        },
    ))
    db.commit()
    return article


@router.put("/{article_id}", response_model=news_schema.NewsArticle)
def update_news_article(
    article_id: int,
    article_in: news_schema.NewsArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Update an existing news article (Admin only)."""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")

    previous_values = {
        "title": article.title,
        "summary": article.summary,
        "content": article.content,
        "source": article.source,
        "image_url": article.image_url,
        "is_public": article.is_public,
    }
    article.title = article_in.title
    article.summary = article_in.summary
    article.content = article_in.content
    article.source = article_in.source
    article.image_url = article_in.image_url
    article.is_public = article_in.is_public
    
    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPDATE,
        resource_type="news_article",
        resource_id=article.id,
        details={"before": previous_values, "after": article_in.model_dump()},
    ))
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{article_id}")
def delete_news_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
):
    """Delete a news article (Admin only)."""
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found")

    db.add(AuditLog(
        user_id=current_user.id,
        action=AuditAction.DELETE,
        resource_type="news_article",
        resource_id=article.id,
        details={"title": article.title, "is_public": article.is_public},
    ))
    db.delete(article)
    db.commit()
    return {"message": "Article deleted successfully", "id": article_id}
