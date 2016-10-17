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

        resp.body = json.dumps(req.context['result'])


class UsersResource:

    def __init__(self, session):
        self.session = session
        self.lg = logging.getLogger('hunterprice.' + __name__)

    def on_get(self, req, resp):
        data = []
        for u in self.session.query(model.user).all():
            data.append(model.entity2dict(u))
        resp.context['result'] = data


class UserResource:

    def __init__(self, session):
        self.session = session
        self.lg = logging.getLogger('hunterprice.' + __name__)

    def on_get(self, req, resp, email):
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        req.context['result'] = model.entity2dict(user)


class UserListsResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp, email):
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound()
        data = []
        for l in user.lists:
            data.append(model.entity2dict(l))

        req.context['result'] = data

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
        print('>><<', model.entity2dict(list_))
        req.context['result'] = model.entity2dict(list_)


class UserListResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp, email, lid):
        lid = int(lid)
        user = self.session.query(model.User).filter_by(email=email).first()
        if user is None:
            raise falcon.errors.HTTPNotFound('User not found')
        list_ = None
        for l in user.lists:
            if l.id == lid:
                list_ = l
                break
        if list_ is None:
            raise falcon.errors.HTTPNotFound()

        list_.products
        req.context['result'] = model.entity2dict(list_)


class ProductsResource:

    def __init__(self, session):
        self.session = session

    def on_get(self, req, resp):
        products = self.session.query(model.Product).all()
        data = []
        for p in products:
            data.append(model.entity2dict(p))
        req.context['result'] = data

    def on_post(self, req, resp):
        data = req.context['data']
        product = model.Product(**data)
        self.session.add(product)
        self.session.commit()
        product.id
        req.context['result'] = model.entity2dict(product)

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
