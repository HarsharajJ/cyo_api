from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Pincode(Base):
    __tablename__ = "pincodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    zipcode: Mapped[str] = mapped_column(String, index=True)
    district: Mapped[str] = mapped_column(String)
    state_name: Mapped[str] = mapped_column(String)