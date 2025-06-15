from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime, Table, Column
import datetime

class Base(DeclarativeBase):
    pass

account_server_association = Table(
    "account_server_association",
    Base.metadata,
    Column("account_id", ForeignKey("user_account.id"), primary_key=True),
    Column("server_id", ForeignKey("server.id"), primary_key=True)
)

class Server(Base):
    __tablename__ = "server"
    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[int] = mapped_column(unique=True)
    channel_id: Mapped[int]

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        secondary=account_server_association,
        back_populates="servers"
    )

    created_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc))

class Account(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    riot_username: Mapped[str]
    user_tag: Mapped[str]
    encrypted_id: Mapped[str]
    discord_user: Mapped[str]

    servers: Mapped[list["Server"]] = relationship(
        "Server",
        secondary=account_server_association,
        back_populates="accounts"
    )

    in_game: Mapped[bool] = mapped_column(default=False, nullable=False)

    solo_tier: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked', nullable=False)
    solo_rank: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked' ,nullable=False)
    solo_league_points: Mapped[int] = mapped_column(default=-1, server_default='-1', nullable=False)

    flex_tier: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked' ,nullable=False)
    flex_rank: Mapped[str] = mapped_column(default='Unranked', server_default='Unranked', nullable=False)
    flex_league_points: Mapped[int] = mapped_column(default=-1, server_default='-1', nullable=False)

    created_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = mapped_column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), onupdate=datetime.datetime.now(datetime.timezone.utc)) # Used to track inactive accounts
