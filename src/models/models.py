from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime
import datetime

class Base(DeclarativeBase):
    pass

class Server(Base):
    __tablename__ = "server"
    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(unique=True)
    channel_id: Mapped[int]
    created_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc))
    accounts: Mapped[list["Account"]] = relationship(back_populates="server", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    riot_username: Mapped[str]
    user_tag: Mapped[str]
    encrypted_id: Mapped[str]
    discord_user: Mapped[str]
    server_id: Mapped[int] = mapped_column(ForeignKey("server.id"))
    server: Mapped["Server"] = relationship(back_populates="accounts")
    in_game: Mapped[bool] = mapped_column(default=False, nullable=False)
    solo_tier: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked', nullable=False)
    solo_rank: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked' ,nullable=False)
    solo_league_points: Mapped[int] = mapped_column(default=-1, server_default='-1', nullable=False)
    flex_tier: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked' ,nullable=False)
    flex_rank: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked', nullable=False)
    flex_league_points: Mapped[int] = mapped_column(default=-1, server_default='-1', nullable=False)
    created_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc)) # Used to track inactive accounts
