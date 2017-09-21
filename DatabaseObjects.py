import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, PickleType, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class Site(Base):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(10), nullable=False, unique=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    ele = Column(Float, nullable=False)


class InversionConfiguration(Base):
    __tablename__ = 'inversion_configurations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    sub_inputs = Column(PickleType)
    smooth_mat = Column(PickleType)
    mask = Column(PickleType)
    faults = Column(PickleType)
    site_map = Column(PickleType)
    site_list = Column(PickleType)

    smoothing = Column(Boolean, nullable=False)
    corner_fix = Column(Boolean, nullable=False)
    short_smoothing = Column(Boolean, nullable=False)
    convergence = Column(Boolean, nullable=False)

class SiteInversionAssociation(Base):
    __tablename__ = 'site_inversion_association'
    site_id = Column(Integer, ForeignKey('sites.id'), primary_key=True)
    inversion_id = Column(Integer, ForeignKey('inversion_configurations.id'), primary_key=True)
    offset = Column(Integer, nullable=True)
    site = relationship("Site")
    inversion = relationship("InversionConfiguration")

engine = create_engine('sqlite:///distributed_live_filter.db')


def createDB():
    Base.metadata.create_all(engine)


def save_site(site_to_save):
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    new_site = Site(**site_to_save)
    session.add(new_site)
    session.commit()

def save_inversion(inversion_to_save):
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    new_inversion = InversionConfiguration(**inversion_to_save)
    session.add(new_inversion)
    session.commit()

def get_inversions():
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session.query(InversionConfiguration).all()

def get_db_session():
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    return DBSession()

if __name__ == "__main__":
    print ("Re-creating database tables.")
    createDB()