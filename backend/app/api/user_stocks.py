from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user_stocks import Watchlist, Favourite, AnalysisHistory
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["user_stocks"])


# Pydantic schemas
class StockBase(BaseModel):
    ticker: str
    name: str
    exchange: str | None = None


class StockResponse(StockBase):
    id: int
    added_at: str
    
    class Config:
        from_attributes = True


class AnalysisHistoryResponse(BaseModel):
    id: int
    ticker: str
    name: str
    analysis_data: dict | None
    created_at: str
    
    class Config:
        from_attributes = True


# Watchlist endpoints
@router.post("/watchlist", response_model=StockResponse)
async def add_to_watchlist(
    stock: StockBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add stock to user's watchlist"""
    # Check if already in watchlist
    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.ticker == stock.ticker
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{stock.ticker} is already in your watchlist"
        )
    
    watchlist_item = Watchlist(
        user_id=current_user.id,
        ticker=stock.ticker,
        name=stock.name,
        exchange=stock.exchange
    )
    db.add(watchlist_item)
    db.commit()
    db.refresh(watchlist_item)
    
    return watchlist_item.to_dict()


@router.get("/watchlist", response_model=List[StockResponse])
async def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's watchlist"""
    watchlist = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id
    ).order_by(Watchlist.added_at.desc()).all()
    
    return [item.to_dict() for item in watchlist]


@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove stock from watchlist"""
    item = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.ticker == ticker
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{ticker} not found in watchlist"
        )
    
    db.delete(item)
    db.commit()
    
    return {"message": f"{ticker} removed from watchlist"}


# Favourites endpoints
@router.post("/favourites", response_model=StockResponse)
async def add_to_favourites(
    stock: StockBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add stock to user's favourites"""
    # Check if already in favourites
    existing = db.query(Favourite).filter(
        Favourite.user_id == current_user.id,
        Favourite.ticker == stock.ticker
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{stock.ticker} is already in your favourites"
        )
    
    favourite_item = Favourite(
        user_id=current_user.id,
        ticker=stock.ticker,
        name=stock.name,
        exchange=stock.exchange
    )
    db.add(favourite_item)
    db.commit()
    db.refresh(favourite_item)
    
    return favourite_item.to_dict()


@router.get("/favourites", response_model=List[StockResponse])
async def get_favourites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's favourites"""
    favourites = db.query(Favourite).filter(
        Favourite.user_id == current_user.id
    ).order_by(Favourite.added_at.desc()).all()
    
    return [item.to_dict() for item in favourites]


@router.delete("/favourites/{ticker}")
async def remove_from_favourites(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove stock from favourites"""
    item = db.query(Favourite).filter(
        Favourite.user_id == current_user.id,
        Favourite.ticker == ticker
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{ticker} not found in favourites"
        )
    
    db.delete(item)
    db.commit()
    
    return {"message": f"{ticker} removed from favourites"}


# Analysis History endpoint
@router.get("/history", response_model=List[AnalysisHistoryResponse])
async def get_analysis_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's analysis history"""
    history = db.query(AnalysisHistory).filter(
        AnalysisHistory.user_id == current_user.id
    ).order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
    
    return [item.to_dict() for item in history]


@router.post("/history")
async def add_to_history(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add analysis to history"""
    history_item = AnalysisHistory(
        user_id=current_user.id,
        ticker=request.get('ticker'),
        name=request.get('name'),
        analysis_data=request.get('analysis_data')
    )
    db.add(history_item)
    db.commit()
    db.refresh(history_item)
    
    return history_item.to_dict()


@router.delete("/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an analysis history item"""
    history_item = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == history_id,
        AnalysisHistory.user_id == current_user.id
    ).first()
    
    if not history_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History item not found"
        )
    
    db.delete(history_item)
    db.commit()


# Saved Analysis endpoints
class SaveAnalysisRequest(BaseModel):
    ticker: str
    title: str | None = None
    analysis_data: dict


class SavedAnalysisResponse(BaseModel):
    id: str
    ticker: str
    name: str | None = None  # Stock company name
    title: str | None
    sentiment: str
    price: float
    currency: str
    confidence: float | None = None  # Confidence score (0-1 decimal)
    saved_at: str


class SavedAnalysisFullResponse(SavedAnalysisResponse):
    analysis_data: dict


@router.post("/saved-analyses", response_model=SavedAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def save_analysis(
    request: SaveAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save an analysis result (max 10 per user)"""
    from app.models.saved_analysis import SavedAnalysis
    from sqlalchemy.exc import IntegrityError
    
    # Check if user already has 10 saved analyses
    saved_count = db.query(SavedAnalysis).filter(
        SavedAnalysis.user_email == current_user.email
    ).count()
    
    if saved_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have reached the maximum limit of 10 saved analyses. Please delete one to save a new one."
        )
    
    # Create new saved analysis
    saved_analysis = SavedAnalysis(
        user_email=current_user.email,
        ticker=request.ticker.upper(),
        title=request.title,
        analysis_data=request.analysis_data
    )
    
    db.add(saved_analysis)
    db.commit()
    db.refresh(saved_analysis)
    return saved_analysis.to_dict()


@router.get("/saved-analyses", response_model=List[SavedAnalysisResponse])
async def get_saved_analyses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's saved analyses"""
    from app.models.saved_analysis import SavedAnalysis
    
    saved_analyses = db.query(SavedAnalysis).filter(
        SavedAnalysis.user_email == current_user.email
    ).order_by(SavedAnalysis.saved_at.desc()).all()
    
    return [sa.to_dict() for sa in saved_analyses]


@router.get("/saved-analyses/{analysis_id}", response_model=SavedAnalysisFullResponse)
async def get_saved_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full saved analysis including data"""
    from app.models.saved_analysis import SavedAnalysis
    import uuid
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis ID")
    
    saved_analysis = db.query(SavedAnalysis).filter(
        SavedAnalysis.id == analysis_uuid,
        SavedAnalysis.user_email == current_user.email
    ).first()
    
    if not saved_analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved analysis not found")
    
    return saved_analysis.to_full_dict()


@router.delete("/saved-analyses/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a saved analysis"""
    from app.models.saved_analysis import SavedAnalysis
    import uuid
    
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid analysis ID")
    
    saved_analysis = db.query(SavedAnalysis).filter(
        SavedAnalysis.id == analysis_uuid,
        SavedAnalysis.user_email == current_user.email
    ).first()
    
    if not saved_analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved analysis not found")
    
    db.delete(saved_analysis)
    db.commit()
