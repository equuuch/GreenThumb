from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Date, Numeric, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    plants = relationship("Plant", back_populates="owner", cascade="all, delete")
    token_usages = relationship("TokenUsage", back_populates="user", cascade="all, delete")
    consultations = relationship("AIConsultation", back_populates="user", cascade="all, delete")

class TokenUsage(Base):
    __tablename__ = "token_usage"
    token_usage_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    tokens_count = Column(Integer)
    request_type = Column(String) # normalize, passport, diagnosis и т.д.
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="token_usages")

class PlantCatalog(Base):
    __tablename__ = "plant_catalog"
    catalog_id = Column(Integer, primary_key=True, autoincrement=True)
    species_name = Column(String, unique=True, nullable=False)
    latin_name = Column(String)
    description = Column(Text)
    default_watering_interval = Column(Integer)
    default_light_level = Column(Float)

    aliases = relationship("PlantAlias", back_populates="catalog")
    plants_instances = relationship("Plant", back_populates="catalog_info")

class PlantAlias(Base):
    __tablename__ = "plant_aliases"
    alias_id = Column(Integer, primary_key=True, autoincrement=True)
    user_input = Column(String, unique=True, nullable=False)
    catalog_id = Column(Integer, ForeignKey("plant_catalog.catalog_id"), nullable=False)

    catalog = relationship("PlantCatalog", back_populates="aliases")

class Plant(Base):
    __tablename__ = "plants"
    plant_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    catalog_id = Column(Integer, ForeignKey("plant_catalog.catalog_id"), nullable=False)
    custom_name = Column(String)
    image_url = Column(String) # путь к локальному файлу
    status_text = Column(String, default='healthy')
    last_watered_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates="plants")
    catalog_info = relationship("PlantCatalog", back_populates="plants_instances")
    growth_logs = relationship("GrowthLog", back_populates="plant", cascade="all, delete")
    calendar_tasks = relationship("CareCalendar", back_populates="plant", cascade="all, delete")

class CareCalendar(Base):
    __tablename__ = "care_calendar"
    calendar_id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.plant_id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String)
    scheduled_date = Column(Date, nullable=False) 
    completion_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)

    plant = relationship("Plant", back_populates="calendar_tasks")

class GrowthLog(Base):
    __tablename__ = "growth_logs"
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey("plants.plant_id", ondelete="CASCADE"), nullable=False)
    height = Column(Numeric, nullable=False)
    note = Column(Text) # заметка
    image_path = Column(String) 
    measured_at = Column(Date, server_default=func.current_date())

    plant = relationship("Plant", back_populates="growth_logs")

class AIConsultation(Base):
    __tablename__ = "ai_consultations"
    consultation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.plant_id", ondelete="CASCADE"), nullable=True)
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    consultation_type = Column(String) # тип запроса для аналитики
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="consultations")