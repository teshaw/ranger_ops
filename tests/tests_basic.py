import unittest
from context import rangers
intrange   = rangers.intrange
floatrange = rangers.floatrange
rangelist  = rangers.rangelist

## tests:

class TestIntRange(unittest.TestCase):

    def test_intersect(self):
        A = intrange(1,10)
        B = intrange(8,15)
        I = A * B
        self.assertEqual(I,intrange(8,10))

    def test_subtract(self):
        A = intrange(1,10)
        B = intrange(8,15)
        C = intrange(4,6)
        I = A - B # A clipped by B
        self.assertEqual(len(I),1)
        self.assertEqual(I[0],intrange(1,7))
        I = B - A # B clipped by A
        self.assertEqual(len(I),1)
        self.assertEqual(I[0],intrange(11,15))
        I = A - C
        self.assertEqual(len(I),2)
        self.assertEqual(I[0],intrange(1,3))
        self.assertEqual(I[1],intrange(7,10))
        #TODO: test with open ranges
    # def test_add(self):
    #     pass

class TestFloatRange(unittest.TestCase):

    def test_intersect(self):
        A = floatrange(1,10)
        B = floatrange(8,15)
        I = A * B
        self.assertEqual(I,floatrange(8,10))

    def test_subtract(self):
        A = floatrange(1,10)
        B = floatrange(8,15)
        C = floatrange(4,6)
        I = A - B # A clipped by B
        self.assertEqual(len(I),1)
        self.assertEqual(I[0],floatrange(1,8))
        I = B - A # B clipped by A
        self.assertEqual(len(I),1)
        self.assertEqual(I[0],floatrange(10,15))
        I = A - C
        self.assertEqual(len(I),2)
        self.assertEqual(I[0],floatrange(1,4))
        #TODO: test with open ranges
    # def test_add(self):
    #     pass

class TestRangeAdditions(unittest.TestCase):

    def test_addition(self):
        # Happy path tests
        test_cases = [
            (floatrange(0, 5, step_size=1), 2, floatrange(2, 7, step_size=1)),
            (intrange(0, 5), 3, intrange(3, 8)),
            (floatrange(0, 5, step_size=1), floatrange(5, 10, step_size=1), rangelist([floatrange(0, 10, step_size=1)])),
            (intrange(0, 5), intrange(5, 10), rangelist([intrange(0, 10)])),
            (floatrange(0, 5, step_size=1), floatrange(10, 15, step_size=1), rangelist([floatrange(0, 5, step_size=1), floatrange(10, 15, step_size=1)])),
            (intrange(0, 5), intrange(10, 15), rangelist([intrange(0, 5), intrange(10, 15)])),
        ]

        for range_obj, other, expected_result in test_cases:
            with self.subTest(range_obj=range_obj, other=other):
                result = range_obj + other
                self.assertEqual(result, expected_result)

    def test_edge_cases(self):
        # Edge cases
        test_cases = [
            (floatrange(0, 0, step_size=1), 0, floatrange(0, 0, step_size=1)),
            (intrange(0, 0), 0, intrange(0, 0)),
            (floatrange(0, 5, step_size=1), floatrange(0, 5, step_size=1), rangelist([floatrange(0, 5, step_size=1)])),
            (intrange(0, 5), intrange(0, 5), rangelist([intrange(0, 5)])),
        ]

        for range_obj, other, expected_result in test_cases:
            with self.subTest(range_obj=range_obj, other=other):
                result = range_obj + other
                self.assertEqual(result, expected_result)

    def test_error_cases(self):
        # Error cases
        test_cases = [
            (floatrange(0, 5, step_size=1), "a", TypeError),
            (intrange(0, 5), {}, TypeError),
            (floatrange(0, 5, step_size=1), None, TypeError),
            (intrange(0, 5), [], TypeError),
        ]

        for range_obj, other, expected_exception in test_cases:
            with self.subTest(range_obj=range_obj, other=other):
                with self.assertRaises(expected_exception):
                    _ = range_obj + other

if __name__ == "__main__":
    unittest.main(exit=False)