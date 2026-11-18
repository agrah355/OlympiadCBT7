from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Paper(Base):
    __tablename__ = 'papers'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(40), nullable=False)
    year = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, default=120)
    positive_marks = Column(Float, default=3)
    negative_marks = Column(Float, default=1)
    published = Column(Boolean, default=False)
    questions = relationship('Question', back_populates='paper', cascade='all, delete-orphan')

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    number = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    options = Column(Text, nullable=False, default='[]')
    answer = Column(String(20), nullable=True)
    solution = Column(Text, nullable=True)
    reviewed = Column(Boolean, default=False)
    paper = relationship('Paper', back_populates='questions')

class Attempt(Base):
    __tablename__ = 'attempts'
    id = Column(Integer, primary_key=True, index=True)
    student = Column(String(100), default='Student')
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    answers = Column(Text, nullable=False, default='{}')
    score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    accuracy = Column(Float, default=0)
    time_taken_seconds = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
