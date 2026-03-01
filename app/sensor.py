from sqlalchemy import Column, String, Boolean
from app.models import Base

class Sensor(Base):
    __tablename__ = "sensors"
    sensorAddress = Column(String, primary_key=True, index=True)
    active = Column(Boolean, default=True)
    color = Column(String)
    name = Column(String)
    groupName = Column(String)
