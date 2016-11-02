from sqlalchemy import Table, ForeignKey, create_engine, func
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import json

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

l_p = Table('listsproducts', Base.metadata,
            Column('list_id', Integer, ForeignKey('lists.id')),
            Column('product_id', Integer, ForeignKey('products.id'))
            )


class List(Base):
    __tablename__ = 'lists'

    id = Column(Integer, primary_key=True)
    owner = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String)
    description = Column(String)
    creation_time = Column(DateTime, default=func.now())

    products = relationship('Product', secondary=l_p, cascade="all")

User.lists = relationship('List', order_by=List.id)


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    unit = Column(String)
    amount = Column(Integer)


def defaut_session():
    engine = create_engine('postgresql://hunter:price@localhost/hunter')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def testing_session():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def entity2dict(entity):
    if isinstance(entity, Base):
        r = {}
        for k, v in entity.__dict__.items():
            if k[0] != '_':
                if isinstance(v, datetime.datetime):
                    v = v.strftime('%y-%m-%dT%H:%M:%S')
                r[k] = v
        return r
    else:
        return entity


if __name__ == '__main__':
    engine = create_engine('postgresql://hunter:price@localhost/hunter')
    print(engine)

    Base.metadata.create_all(engine)
    user = User(name='ark', email='arksega@gmail.com', password='124dfcab3')
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(user)
    session.commit()
