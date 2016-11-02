from falcon import testing
import hunterprice
import falcon
import model
import json


class MyTestCase(testing.TestCase):
    def setUp(self):
        super(MyTestCase, self).setUp()

        self.db_session = model.testing_session()
        self.usermail = 'a@b.com'
        self.user = {'name': 'ark', 'password': '1234', 'email': self.usermail}

        user = model.User(**self.user)
        self.db_session.add(user)
        self.db_session.commit()
        self.user['id'] = user.id

        self.list = {
            'owner': user.id,
            'name': 'list 1',
            'products': [],
            'description': 'La lista de los jugos'}

        list_ = model.List(**self.list)
        self.db_session.add(list_)
        self.db_session.commit()
        self.list['id'] = list_.id

        self.product = {
            'name': 'soda',
            'unit': 'lt',
            'amount': '2',
            'description': 'A lot of sugar'
        }
        product = model.Product(**self.product)
        self.db_session.add(product)
        self.db_session.commit()
        self.product['id'] = product.id

        self.app = hunterprice.create_api(self.db_session)

    def tearDown(self):
        self.db_session.query(model.List).delete()
        self.db_session.query(model.Product).delete()
        self.db_session.query(model.User).delete()
        self.db_session.commit()


class TestHunterPrice(MyTestCase):

    def test_get_all_users(self):
        result = self.simulate_get('/users')
        self.assertEqual(len(result.json), 1)

    def test_get_user(self):
        result = self.simulate_get('/users/{}'.format(self.usermail))
        self.assertEqual(result.json, self.user)

    def test_get_all_lists(self):
        result = self.simulate_get('/users/{}/lists'.format(self.usermail))
        self.assertEqual(len(result.json), 1)

    def test_get_list(self):
        uri = '/users/{}/lists/{}'.format(self.usermail, self.list['id'])
        result = self.simulate_get(uri)
        rj = result.json
        del(rj['creation_time'])
        self.assertDictEqual(rj, self.list)

    def test_post_list(self):
        uri = '/users/{}/lists'.format(self.usermail)
        payload = {
            'owner': self.user['id'],
            'name': 'list 2',
            'description': 'Lista de compras'}
        headers = {'content-type': 'application/json'}
        result = self.simulate_post(
            uri, body=json.dumps(payload), headers=headers)
        rj = result.json
        del(rj['id'])
        del(rj['creation_time'])
        self.assertDictEqual(rj, payload)

    def test_put_list(self):
        uri = '/users/{}/lists/{}'.format(self.usermail, self.list['id'])
        payload = {
            'id': self.list['id'],
            'owner': self.user['id'],
            'name': 'list 3',
            'products': [],
            'description': 'Fiesta!'}
        headers = {'content-type': 'application/json'}
        result = self.simulate_put(
            uri, body=json.dumps(payload), headers=headers)
        rj = result.json
        del(rj['creation_time'])
        self.assertDictEqual(rj, payload)

    def test_put_list_missing_user(self):
        uri = '/users/nomail.com/lists/{}'.format(self.list['id'])
        headers = {'content-type': 'application/json'}
        result = self.simulate_put(
            uri, body=json.dumps({}), headers=headers)
        self.assertEqual(result.status_code, 404)

    def test_put_list_missing_list(self):
        uri = '/users/{}/lists/-1'.format(self.usermail)
        headers = {'content-type': 'application/json'}
        result = self.simulate_put(
            uri, body=json.dumps({}), headers=headers)
        self.assertEqual(result.status_code, 404)

    def test_put_list_missing_product(self):
        uri = '/users/{}/lists/{}'.format(self.usermail, self.list['id'])
        payload = {
            'id': self.list['id'],
            'owner': self.user['id'],
            'name': 'list 4',
            'products': [-1],
            'description': 'Fiesta!'}
        headers = {'content-type': 'application/json'}
        result = self.simulate_put(
            uri, body=json.dumps(payload), headers=headers)
        self.assertEqual(result.status_code, 404)

    def test_get_products(self):
        result = self.simulate_get('/products')
        self.assertEqual(len(result.json), 1)

    def test_post_product(self):
        uri = '/products'
        payload = {
            'name': 'Milk',
            'description': 'Fresh soy milk',
            'unit': 'ml',
            'amount': 750
        }
        headers = {'content-type': 'application/json'}
        result = self.simulate_post(
            uri, body=json.dumps(payload), headers=headers)
        rj = result.json
        del(rj['id'])
        self.assertDictEqual(rj, payload)

    def test_post_negative_content_type(self):
        uri = '/users/{}/lists'.format(self.usermail)
        payload = {
            'owner': self.user['id'],
            'name': 'list 2',
            'description': 'Lista de compras'}
        headers = {'content-type': 'application/jwt'}
        self.simulate_post(
            uri, body=json.dumps(payload), headers=headers)
        self.assertRaises(falcon.HTTPNotAcceptable)

    def test_post_none_body(self):
        uri = '/users/{}/lists'.format(self.usermail)
        headers = {'content-type': 'application/json'}
        self.simulate_post(uri, headers=headers)
        self.assertRaises(falcon.HTTPBadRequest)

    def test_post_malformed_json(self):
        uri = '/users/{}/lists'.format(self.usermail)
        headers = {'content-type': 'application/json'}
        self.simulate_post(uri, headers=headers, body='{')
        self.assertRaises(falcon.HTTPBadRequest)

    def test_get_negative_accept(self):
        headers = {'accept': 'application/jwt'}
        self.simulate_get('/products', headers=headers)
        self.assertRaises(falcon.falcon.HTTPNotAcceptable)

    def test_get_missing_user(self):
        self.simulate_get('/users/nomail.com')
        self.assertRaises(falcon.errors.HTTPNotFound)

    def test_get_missing_list(self):
        uri = '/users/{}/lists/0'.format(self.usermail)
        result = self.simulate_get(uri)
        self.assertEqual(result.status_code, 404)

    def test_get_missing_user_list(self):
        uri = '/users/nomail.com/lists/0'
        result = self.simulate_get(uri)
        self.assertEqual(result.status_code, 404)

    def test_get_missing_user_lists(self):
        uri = '/users/nomail.com/lists'
        result = self.simulate_get(uri)
        self.assertEqual(result.status_code, 404)

    def test_post_missing_user_lists(self):
        uri = '/users/nomail.com/lists'
        headers = {'content-type': 'application/json'}
        result = self.simulate_post(uri, body=json.dumps({}), headers=headers)
        self.assertEqual(result.status_code, 404)

    def test_post_negative_list_type(self):
        uri = '/users/{}/lists'.format(self.usermail)
        payload = {
            'owner': self.user['id'],
            'type': 'not valid field',
            'name': 'list 2',
            'description': 'Lista de compras'}
        headers = {'content-type': 'application/json'}
        result = self.simulate_post(
            uri, body=json.dumps(payload), headers=headers)
        self.assertEqual(result.status_code, 400)
