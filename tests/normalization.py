# -*- coding: utf-8 -*-
from unittest import TestCase


class HouseNumberTest(TestCase):
    """Pruebas relacionadas con la altura de una calle."""
    def test_normalize_when_number_in_range(self):
        """La altura está en el rango de la calle en la base de datos."""
        pass

    def test_normalize_when_number_out_of_range(self):
        """La altura no está en el rango de la calle en la base de datos."""
        pass

    def test_normalize_when_number_not_present(self):
        """La calle no tiene numeración en la base de datos."""
        pass
