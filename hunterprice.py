#!/bin/env python
import logging
import falcon
import model
import json


class RequireJSON(object):

    def process_request(self, req, resp):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(
                'This API only supports responses encoded as JSON.',
                href='http://docs.examples.com/api/json')

        if req.method in ('POST', 'PUT'):
            if 'application/json' not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(
                    'This API only supports requests encoded as JSON.',
                    href='http://docs.examples.com/api/json')


class JSONTranslator(object):

    def process_request(self, req, resp):
        # req.stream corresponds to the WSGI wsgi.input environ variable,
        # and allows you to read bytes from the request body.
        #
        if req.content_length in (None, 0):
            return
        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        try:
            req.context['data'] = json.loads(body.decode('utf-8'))

        except (ValueError, UnicodeDecodeError):
            raise falcon.HTTPError(falcon.HTTP_753,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect or not encoded as '
                                   'UTF-8.')

    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return

        resp.body = json.dumps(req.context['result'], default=model.entity2dict)


class UsersResource:

    def __init__(self, session):
        self.session = session
        self.lg = logging.getLogger('hunterprice.' + __name__)

    def on_get(self, req, resp):
        req.context['result'] = self.session.query(model.User).all()


class UserResource:

    def __init__(self, session):
        self.session = session
        self.lg = logging.getLogger('hunterprice.' + __name__)

    def on_get(self, req, resp, email):
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        req.context['result'] = user


class UserListsResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp, email):
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        req.context['result'] = user.lists

    def on_post(self, req, resp, email):
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        data = req.context['data']
        try:
            data['owner'] = user.id
            list_ = model.List(**data)
        except TypeError as e:
            raise falcon.HTTPBadRequest('Invalid parameter', e.args[0])
        self.session.add(list_)
        self.session.commit()
        list_.id
        req.context['result'] = list_


class UserListResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp, email, lid):
        lid = int(lid)
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        try:
            list_ = [l for l in user.lists if l.id == lid][0]
        except IndexError:
            raise falcon.errors.HTTPNotFound()

        list_.products
        req.context['result'] = list_

    def on_put(self, req, resp, email, lid):
        lid = int(lid)
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        try:
            list_ = [l for l in user.lists if l.id == lid][0]
        except IndexError:
            raise falcon.errors.HTTPNotFound()

        data = req.context['data']
        if 'products' in data.keys():
            products = data['products']
            query = self.session.query(model.Product)
            eproducts = query.filter(model.Product.id.in_(products)).all()
            if len(products) > len(eproducts):
                raise falcon.errors.HTTPNotFound()

            list_.products = eproducts
            del(data['products'])
        for k, v in data.items():
            setattr(list_, k, v)
        self.session.commit()
        list_.products
        req.context['result'] = list_


class ProductsResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp):
        req.context['result'] = self.session.query(model.Product).all()

    def on_post(self, req, resp):
        data = req.context['data']
        product = model.Product(**data)
        self.session.add(product)
        self.session.commit()
        product.id
        req.context['result'] = product

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT)

db_session = model.defaut_session()
api = falcon.API(middleware=[RequireJSON(), JSONTranslator()])
api.add_route('/users', UsersResource(db_session))
api.add_route('/users/{email}', UserResource(db_session))
api.add_route('/users/{email}/lists', UserListsResource(db_session))
api.add_route('/users/{email}/lists/{lid}', UserListResource(db_session))
api.add_route('/products', ProductsResource(db_session))
application = api
