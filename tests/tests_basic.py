import unittest
from context import rangers
intrange   = rangers.intrange
floatrange = rangers.floatrange
rangelist  = rangers.rangelist

## tests:

class TestFloatRange(unittest.TestCase):

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

##
if __name__ == "__main__":
    pass
    unittest.main(exit=False)