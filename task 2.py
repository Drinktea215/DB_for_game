from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, Session
from sqlalchemy import Integer, String, ForeignKey, Boolean, Date, create_engine, select
from typing import Optional
from datetime import date
import csv


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = 'players'

    player_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    player_levels: Mapped[Optional[list[PlayerLevel]]] = relationship('PlayerLevel', back_populates='player')


class Level(Base):
    __tablename__ = 'levels'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[int] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    player_levels: Mapped[Optional[list[PlayerLevel]]] = relationship('PlayerLevel', back_populates='level')
    level_prizes: Mapped[Optional[list[LevelPrize]]] = relationship('LevelPrize', back_populates='level')


class Prize(Base):
    __tablename__ = 'prizes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[int] = mapped_column(String)
    level_prizes: Mapped[Optional[list[LevelPrize]]] = relationship('LevelPrize', back_populates='prize')


class PlayerLevel(Base):
    __tablename__ = 'player_levels'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    player_id: Mapped[str] = mapped_column(String(100), ForeignKey('players.player_id'))
    player: Mapped[Optional[list[Player]]] = relationship('Player', back_populates='player_levels', cascade="all")
    level_id: Mapped[int] = mapped_column(Integer, ForeignKey('levels.id'))
    level: Mapped[Optional[list[Level]]] = relationship('Level', back_populates='player_levels', cascade="all")

    completed: Mapped[date] = mapped_column(Date, nullable=True)
    is_completed: Mapped[int] = mapped_column(Boolean, default=False)
    score: Mapped[int] = mapped_column(Integer, default=0)


class LevelPrize(Base):
    __tablename__ = 'level_prizes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    level_id: Mapped[int] = mapped_column(Integer, ForeignKey('levels.id'))
    level: Mapped[Optional[list[Level]]] = relationship('Level', back_populates='level_prizes', cascade="all")

    prize_id: Mapped[int] = mapped_column(Integer, ForeignKey('prizes.id'))
    prize: Mapped[Optional[list[Prize]]] = relationship('Prize', back_populates='level_prizes', cascade="all")

    received: Mapped[date] = mapped_column(Date)


def reward_for_level(session: Session, player_id: str, level_id: int, prize_id: int):
    with session as s:
        player_level = s.execute(
            select(PlayerLevel).where(PlayerLevel.player_id == player_id,
                                      PlayerLevel.level_id == level_id)).scalar_one_or_none()

        if player_level and player_level.is_completed:
            level_prize = LevelPrize(level_id=level_id, prize_id=prize_id, received=date.today())
            s.add(level_prize)
            s.commit()


def to_csv(s: Session):
    with s:
        query = (select(Player.player_id,
                        Level.title.label("level_title"),
                        PlayerLevel.is_completed,
                        Prize.title.label("prize_title"))
                 .outerjoin(PlayerLevel, PlayerLevel.player_id == Player.player_id)
                 .outerjoin(Level, PlayerLevel.level_id == Level.id)
                 .outerjoin(LevelPrize, LevelPrize.level_id == Level.id)
                 .outerjoin(Prize, LevelPrize.prize_id == Prize.id))

        result = s.execute(query)

        with open("players.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Player ID", "Level Title", "Completed", "Prize"])

            for row in result:
                writer.writerow(row)
