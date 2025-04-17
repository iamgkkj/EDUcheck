from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Corrected line
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Corrected line

    # Relationships
    messages = relationship('ChatMessage', backref='chat', lazy='dynamic')
    student = relationship('User', foreign_keys=[student_id], backref='student_chats')
    teacher = relationship('User', foreign_keys=[teacher_id], backref='teacher_chats')

    def __repr__(self):
        return f"<Chat id:{self.id} student_id:{self.student_id} teacher_id:{self.teacher_id}>"

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow) # Corrected line
    is_read = Column(Boolean, default=False)
    attachment_path = Column(String(255))
    # Relationships
    sender = relationship('User', foreign_keys=[sender_id])
    receiver = relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f"<ChatMessage id:{self.id} chat_id:{self.chat_id} sender_id:{self.sender_id}>"