# ABOUT

This package implements `intrange` and `floatrange` classes and a `rangelist`
class to manage them.

`intrange` objects are similar to standard range objects.
They have the option to be *closed* or not.
in addition several methods are overloaded to allow arithmetic operations

`a=intrange(1,20)`

`b=intrange(4,8)`

`a-b` evaluates to `[intrange(1,3,closed=True,group=(1,)),
                     intrange(9,20,closed=True,group=(1,))]`

`b-a` evaluates to `[]`

`b*a = a*b` the intersection of `a` and `b`

`a-1 =  intrange(0,19,closed=True,group=(1,))`

the `group` property allow otherwise overlapping ranges to be treated as distinct.

The `attributes` property allows other metadata to accompany the range object.
It is however, up to the user to decide how to interpret those attributes after
adding the ranges.

## Example usage

The following are some sample operations


`a: intrange(1,20,closed=True)`

`b: intrange(4,8,closed=True)`

`c: intrange(2,8,closed=True)`

`d: intrange(2,8,closed=False)`

`e: intrange(7,40,closed=True)`

`a-b: [intrange(1,3,closed=True,group=(1,)), intrange(9,20,closed=True,group=(1,))]`

`1 in a: True`

`8 in b: True`

`12 in b: False`

`a + b: [intrange(1,20,closed=True,group=(1,))]`

`b + a: [intrange(1,20,closed=True,group=(1,))]`

`a - b: [intrange(1,3,closed=True,group=(1,)), intrange(9,20,closed=True,group=(1,))]`

`b - a: []`

`a * b: intrange(4,8,closed=True)`

`b * a: intrange(4,8,closed=True)`

`a // b : [intrange(1,3,closed=True,group=(1,)), intrange(9,20,closed=True,group=(1,))]`

`b // a: []`

`b // 6: [intrange(4,5,closed=True,group=(1,)), intrange(7,8,closed=True,group=(1,))]`

`b - c: []`

`b-d: [intrange(8,8,closed=True,group=(1,))]`

`rangelist((a,e)) : [intrange(1,20,closed=True,group=(1,)), intrange(7,40,closed=True,group=(1,))]`