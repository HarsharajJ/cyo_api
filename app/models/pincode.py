from sqlalchemy import String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Pincode(Base):
    __tablename__ = "pincodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    district: Mapped[str] = mapped_column(String, index=True)
    state_name: Mapped[str] = mapped_column(String, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    pincode: Mapped[str] = mapped_column(String, index=True)