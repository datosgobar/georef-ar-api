from service.utils import LRUDict
from . import GeorefMockTest

DEFAULT_SIZE = 10


class LRUDictTest(GeorefMockTest):
    def setUp(self):
        self.lru_dict = LRUDict(DEFAULT_SIZE)
        super().setUp()

    def test_insert_read(self):
        """Los diccionarios LRU deberían aceptar las operaciones de
        inserción y consulta."""
        self.lru_dict['foo'] = 'bar'
        self.lru_dict['test'] = 'working'

        self.assertTrue(self.lru_dict['foo'] == 'bar' and
                        self.lru_dict['test'] == 'working', self.lru_dict)

    def test_contains(self):
        """Los diccionarios LRU deberían aceptar la operación de consulta de
        presencia de una key."""
        self.lru_dict['foo'] = 'bar'

        self.assertTrue('foo' in self.lru_dict, self.lru_dict)

    def test_len(self):
        """Los diccionarios LRU deberían aceptar la operación de consulta de
        cantidad de ítems."""
        self.lru_dict['foo'] = 'bar'
        self.lru_dict['test'] = 'working'
        self.lru_dict['baz'] = 'qux'

        self.assertEqual(len(self.lru_dict), 3, self.lru_dict)

    def test_max_len(self):
        """Los diccionarios LRU nunca deberían tener más ítems que 'size'."""
        for i in range(DEFAULT_SIZE + 10):
            self.lru_dict['key{}'.format(i)] = i

        self.assertEqual(len(self.lru_dict), DEFAULT_SIZE, self.lru_dict)

    def test_key_deleted_score_0(self):
        """Los diccionarios LRU deberían eliminar las keys menos utilizadas."""
        lru_dict = LRUDict(2)
        lru_dict['foo'] = 'foo'
        lru_dict['bar'] = 'bar'
        lru_dict['quux'] = 'quux'
        lru_dict['quux']  # pylint: disable=pointless-statement
        lru_dict['quuz'] = 'quuz'

        self.assertTrue('foo' not in lru_dict and 'bar' not in lru_dict,
                        lru_dict)

    def test_key_deleted(self):
        """Los diccionarios LRU deberían eliminar las keys menos utilizadas,
        incluso cuando todas las keys fueron accedidas una vez o más."""
        lru_dict = LRUDict(2)
        lru_dict['foo'] = 'foo'
        for _ in range(3):
            lru_dict['foo']  # pylint: disable=pointless-statement

        lru_dict['bar'] = 'bar'
        for _ in range(4):
            lru_dict['bar']  # pylint: disable=pointless-statement

        lru_dict['quuz'] = 'quuz'

        self.assertTrue('foo' not in lru_dict and 'bar' in lru_dict,
                        lru_dict)
