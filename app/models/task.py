from sqlalchemy import String, DateTime, func, ForeignKey, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import datetime



class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    is_done: Mapped[bool] = mapped_column(default=False)
    due_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=None
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now())
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))