import os
import sys
from sqlalchemy import exc, Column, ForeignKey, Integer, String, Float, PickleType, Boolean, exists, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///distributed_live_filter.db')
Base.metadata.bind = engine
session = sessionmaker(bind=engine)()


class DataError(Exception):
    pass


class BaseMixin(object):
    @classmethod
    def create(cls, obj=None, **kw):
        if obj is None:
            obj = cls(**kw)
        try:
            session.add(obj)
            session.commit()
            return obj
        except exc.IntegrityError:
            session.rollback()
            raise DataError

    @classmethod
    def update(cls):
        session.commit()

    @classmethod
    def get_all(cls):
        return session.query(cls).all()

    @classmethod
    def get_by_field(cls, field, value):
        return session.query(cls).filter(field == value)


class SiteInversionAssociation(Base, BaseMixin):
    __tablename__ = 'site_inversion_association'
    site_id = Column(Integer, ForeignKey('sites.id'), primary_key=True)
    inversion_id = Column(Integer, ForeignKey('inversion_configurations.id'), primary_key=True)
    offset = Column(Integer, nullable=True)
    site = relationship("Site")
    inversion = relationship("InversionConfiguration")

    @classmethod
    def get_offset_by_site_and_inversion(cls, site, inversion):
        return session.query(cls).filter(and_(cls.site == site,
                                              cls.inversion == inversion))[0].offset


class Site(Base, BaseMixin):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(10), nullable=False, unique=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    ele = Column(Float, nullable=False)

    @classmethod
    def get_sites_missing_offset(cls, inversion):
        return session.query(cls).outerjoin(SiteInversionAssociation) \
            .filter(~exists().where(SiteInversionAssociation.inversion == inversion))

    @classmethod
    def get_sites_by_offset_and_inversion(cls, inversion, offset):
        return session.query(cls).join((SiteInversionAssociation.site, cls)) \
                .filter(and_(SiteInversionAssociation.inversion == inversion,
                             SiteInversionAssociation.offset >= offset)).all()

class KalmanConfiguration(Base, BaseMixin):
    __tablename__ = 'kalman_configuration'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    max_offset = Column(Float, nullable=False)
    min_r = Column(Float, nullable=False)
    eq_pause = Column(Float, nullable=False)
    eq_threshold = Column(Float, nullable=False)
    mes_wait = Column(Integer, nullable=False)
    kill_limit = Column(Integer, nullable=False)


class InversionConfiguration(Base, BaseMixin):
    __tablename__ = 'inversion_configurations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    min_offset = Column(Float, nullable=False)
    sub_inputs = Column(PickleType)
    smooth_mat = Column(PickleType)
    mask = Column(PickleType)
    faults = Column(PickleType)
    site_map = Column(PickleType)
    offset = Column(PickleType)
    smoothing = Column(Boolean, nullable=False)
    corner_fix = Column(Boolean, nullable=False)
    short_smoothing = Column(Boolean, nullable=False)
    convergence = Column(Float, nullable=False)
    kalman_configuration_id = Column(Integer, ForeignKey('kalman_configuration.id'))
    kalman_configuration = relationship("KalmanConfiguration")
    delay_timespan = Column(Integer, nullable=False)


class MeasurementSource(Base):
    __tablename__ = 'measurement_source'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'measurement_source'

    }


class SavedMeasurementSource(MeasurementSource):
    filename = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'saved_measurement_source'
    }


class RabbitMQSource(MeasurementSource):
    host = Column(String)
    user_id = Column(String)
    password = Column(String)
    virtual_host = Column(String)
    exchange_name = Column(String)
    port = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'rabbit_mq_measurement_source'
    }


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)


class ReportDestination(Base):
    __tablename__ = 'report_destination'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'report_destination'

    }


class TextFileReportDestination(ReportDestination):
    text_filename = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'text_file_report_destination'
    }


class MongoDBReportDestination(ReportDestination):
    mongo_host = Column(String)
    mongo_port = Column(Integer)
    mongo_user_id = Column(String)
    mongo_password = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'mongo_db_report_destination'
    }


class RabbitMQReportDestination(ReportDestination):
    rabbit_mq_host = Column(String)
    rabbit_mq_user_id = Column(String)
    rabbit_mq_password = Column(String)
    rabbit_mq_virtual_host = Column(String)
    rabbit_mq_exchange_name = Column(String)
    rabbit_mq_model = Column(String)
    rabbit_mq_port = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'rabbit_mq_report_destination'
    }


class MeasurementSourceInversionAssociation(Base):
    __tablename__ = 'measurement_source_inversion_association'
    measurement_source_id = Column(Integer, ForeignKey('measurement_source.id'), primary_key=True)
    inversion_id = Column(Integer, ForeignKey('inversion_configurations.id'), primary_key=True)
    measurement_source = relationship("MeasurementSource")
    inversion = relationship("InversionConfiguration")


class ReportDestinationInversionAssociation(Base):
    __tablename__ = 'report_destination_inversion_association'
    report_destination_id = Column(Integer, ForeignKey('report_destination.id'), primary_key=True)
    inversion_id = Column(Integer, ForeignKey('inversion_configurations.id'), primary_key=True)
    report_destination = relationship("ReportDestination")
    inversion = relationship("InversionConfiguration")


if __name__ == "__main__":
    print ("Re-creating database tables.")
    Base.metadata.create_all(engine)