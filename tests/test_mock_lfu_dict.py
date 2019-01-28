from service.utils import LFUDict
from . import GeorefMockTest

DEFAULT_SIZE = 10


class LFUDictTest(GeorefMockTest):
    def setUp(self):
        self.lfu_dict = LFUDict(DEFAULT_SIZE)
        super().setUp()

    def test_insert_read(self):
        """Los diccionarios LFU deberían aceptar las operaciones de
        inserción y consulta."""
        self.lfu_dict['foo'] = 'bar'
        self.lfu_dict['test'] = 'working'

        self.assertTrue(self.lfu_dict['foo'] == 'bar' and
                        self.lfu_dict['test'] == 'working', self.lfu_dict)

    def test_contains(self):
        """Los diccionarios LFU deberían aceptar la operación de consulta de
        presencia de una key."""
        self.lfu_dict['foo'] = 'bar'

        self.assertTrue('foo' in self.lfu_dict, self.lfu_dict)

    def test_len(self):
        """Los diccionarios LFU deberían aceptar la operación de consulta de
        cantidad de ítems."""
        self.lfu_dict['foo'] = 'bar'
        self.lfu_dict['test'] = 'working'
        self.lfu_dict['baz'] = 'qux'

        self.assertEqual(len(self.lfu_dict), 3, self.lfu_dict)

    def test_max_len(self):
        """Los diccionarios LFU nunca deberían tener más ítems que 'size'."""
        for i in range(DEFAULT_SIZE + 10):
            self.lfu_dict['key{}'.format(i)] = i

        self.assertEqual(len(self.lfu_dict), DEFAULT_SIZE, self.lfu_dict)

    def test_key_deleted_score_0(self):
        """Los diccionarios LFU deberían eliminar las keys menos utilizadas."""
        lfu_dict = LFUDict(2)
        lfu_dict['foo'] = 'foo'
        lfu_dict['bar'] = 'bar'
        lfu_dict['quux'] = 'quux'
        lfu_dict['quux']  # pylint: disable=pointless-statement
        lfu_dict['quuz'] = 'quuz'

        self.assertTrue('foo' not in lfu_dict and 'bar' not in lfu_dict,
                        lfu_dict)

    def test_key_deleted(self):
        """Los diccionarios LFU deberían eliminar las keys menos utilizadas,
        incluso cuando todas las keys fueron accedidas una vez o más."""
        lfu_dict = LFUDict(2)
        lfu_dict['foo'] = 'foo'
        for _ in range(3):
            lfu_dict['foo']  # pylint: disable=pointless-statement

        lfu_dict['bar'] = 'bar'
        for _ in range(4):
            lfu_dict['bar']  # pylint: disable=pointless-statement

        lfu_dict['quuz'] = 'quuz'

        self.assertTrue('foo' not in lfu_dict and 'bar' in lfu_dict,
                        lfu_dict)
