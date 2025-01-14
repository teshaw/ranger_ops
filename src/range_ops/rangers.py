from collections import namedtuple
import pandas as pd
from uuid import uuid4,UUID

## decorators
# def _allow_for(*args,types=(int,),**kwargs):
#     def wrapper(*args,**kwargs):
#         if isinstance(args[1],types):
#             fun(*args,**kwargs)
#         else:
#             msg=(f"{fun.__name__} is not implemented for objects of type "
#                 f"{type(args[0])}")
#             raise NotImplementedError(msg)
#     return wrapper

## classes
class rangelist(list):

    def __init__(self,*args,**kwargs):
        """
        Initializes a rangelist object.

        Args:
            __sort_key__ : callable
            The `__sort_key__` attribute is used to order ranges.
            This allows preferred items to be used when clipping unique ranges.
            a functional call is expected

            other *args and **kwargs are passed to the super() list init method

        """
        if "__sort_key__" in kwargs:
            self.__sort_key__ = kwargs.pop("__sort_key__")
        else:
            self.__sort_key__ = None
        super().__init__(*args,**kwargs)

    def extent(self):
        return sum((x.extent() for x in self))

    # def __iter__(self):
    #     for elem in self:
    #         yield(elem)
    def __mul__(self,other):
        """intersection of two rangelists"""
        diff = self - other
        return self - diff

    def __sub__(self,other):
        """for A - B, return A ranges not covered by B range"""
        if isinstance(other,(intrange,floatrange)):
            result=rangelist()
            for s in self:
                new=s-other
                if isinstance(new,rangelist):
                    for n in new:
                        result.append(n)
                elif isinstance(new,type(s)):
                    result.append(new)
            return result
        elif isinstance(other,(rangelist,list)):
            ResultList=rangelist()
            for s in self:
                for o in other:
                    s-=o
                if s or s.extent():
                    if isinstance(s,(rangelist,)):
                        for _s in s:
                            ResultList.append(_s)
                    elif isinstance(s,(intrange,floatrange)):
                        ResultList.append(s)
            return ResultList
        else:
            msg=(f"- operator not defined between objects of type {type(self)} "
                 f"and {type(other)}"
                 )
            raise NotImplementedError(msg)

    # def __add__(self,other):
    #     pass

    def groupdict(self):
        from collections import defaultdict
        groupdict=defaultdict(rangelist)
        for r in self:
            try:
                groupdict[r._group].append(r)
            except AttributeError:
                print("AARGH")#DEBUG
        return groupdict

    @staticmethod
    def __ungroup__(groupdict):
        """
        Static method to ungroup a dictionary of ranges.

        reverts the .groupdict() method result
        intended for internal use

        Args:
            groupdict: A dictionary containing ranges grouped by keys.

        Returns:
            rangelist: A new rangelist object containing all the ungrouped ranges.

        Examples:
            >>> R = rangelist()
            >>> R.append(floatrange(1,10,group=(1,)))
            >>> R.append(floatrange(8,15,group=(1,)))
            >>> R.append(floatrange(3,13,group=(2,)))
            >>> print("R",R)
            >>> groupdict = R.groupdict()
            >>> print(groupdict)
            >>> result = rangelist.__ungroup__(groupdict)
            >>> print(result)
        """
        ungrouped=[]
        # used a plain list because we plan to overload __add__ in rangelist
        #TODO: check how += operator overloading compares with "+" op overload?
        for v in groupdict.values():
            if isinstance(v,(rangelist,list)):
                ungrouped.extend(iter(v))
            elif isinstance(v,(intrange,floatrange)):
                ungrouped.append(v)
        return rangelist(ungrouped)

    def __group_attributes__(self,with_uuid=False):
        regrouped = [r.__group_attributes__(with_uuid=with_uuid) for r in self]
        return rangelist(regrouped)

    def __ungroup_attributes__(self):
        degrouped = [r.__ungroup_attributes__() for r in self]
        return rangelist(degrouped)

    def unique(self):
        """remove duplicate range parts according to grouping"""
        #TODO: consider adding ignore grouping option?
        GD = self.groupdict()
        for grp in GD:
            GD[grp] = self.__unique__(GD[grp])
        return self.__ungroup__(GD)


    def duplicates(self):
        '''excluded duplicate portions'''
        U = self.unique().__group_attributes__(with_uuid=True)
        S = self.__group_attributes__(with_uuid=True)
        return (S - U).__ungroup_attributes__()

    def __unique__(self,inputRangeList,strict=False):
        '''underlying method for clipping range elements to remove duplicates'''
        UniqRange = rangelist()
        Overlaps = rangelist()
        iter_over_ranges = sorted(inputRangeList,key=self.__sort_key__)
        for r in iter_over_ranges:
            for u in UniqRange:
                r-=u
                if not r.extent():
                    break
            if isinstance(r,(rangelist,list)):
                for _r in r:
                    UniqRange.append(_r)
            elif isinstance(r,(intrange,floatrange)) and r.extent()>0:
                UniqRange.append(r)
            else:
                raise ValueError(f"{r} was unexpected element in rangelist")
        return UniqRange

    def __merge__(self):
        MergedRange = rangelist()
        for r in sorted(self.unique()):
            if MergedRange:
                M = MergedRange.pop()
                M += r
                if isinstance(M,(rangelist,list)):
                    for _m in M:
                        MergedRange.append(_m)
                elif isinstance(M,(intrange,floatrange)) and M.extent()>0:
                    MergedRange.append(M)
            else:
                MergedRange.append(r)
        return MergedRange

    def merge(self):
        """consolidate adjacent/overlapping ranges."""
        gd=self.groupdict()
        for grp in gd:
            gd[grp]=gd[grp].__merge__()
        return self.__ungroup__(gd)

    def disect(self):
        """slice up ranges where portions overlap"""
        raise NotImplementedError("disect method not implemented")

    def to_dataframe(self):
        return pd.DataFrame((x._astuple() for x in self))

    @staticmethod
    def from_dataframe(df,start,end,groupby,step_size=0.1):
        result = rangelist()
        for rng,row in df.set_index([start,end]).iterrows():
            result.append(floatrange(*rng,step_size,group=tuple(row[groupby])))
        return result

class intrange(object):
    """Closed range object of all integer values between min and max.

    :param min_val: range start
    :type min_val: int


    :param max_val: range end
    :type max_val: int

    :param closed: whether to include the max_val, defaults to True
    :type closed: bool

    :param group: way of categorising ranges,
        used to sort and group them for other operations, defaults to (1,)
    :type group: tuple, can be other immutable objects,
        but usage should be consistent for a collection of ranges

    :param attributes: any other properties associated with the range
    :type attributes: dict


    """

    def __init__(self, min_val, max_val, closed=True, group=(1,), attributes=None, uuid=uuid4()):
        self._start=int(min(min_val,max_val))
        self._end=int(max(min_val,max_val))
        self._closed=1 if closed else 0
        self._open = 1-self._closed
        self._group=group
        if attributes is None:
            attributes = {}
        self._attributes=attributes
        self._uuid = uuid or uuid4()
        assert isinstance(self._uuid,UUID), "attribute 'uuid' must be a UUID instance"
        assert "group" not in attributes,"reserved keyword 'group' should not be in attributes"
        assert "uuid" not in attributes,"reserved keyword 'uuid' should not be in attributes"

    def __repr__(self):
        '''string representing constructor for the object'''
        S = self._start
        E = self._end
        C = bool(self._closed)
        G=self._group
        A=self._attributes
        attrib = f",attributes={A}" if A else ""
        return f"intrange({S},{E},closed={C},group={G}{attrib})"

    def __str__(self):
        '''simplified fundamental range '''
        S = self._start
        E = self._end
        C = bool(self._closed)
        # G=self._group
        # A=self._attributes
        return f"intrange({S},{E},closed={C})"

    def __contains__(self, other):
        # enable O(1) determination of whether a value is in your range
        # (assume step size is 1)
        msg="test value must be an int or another intrange"
        assert isinstance(other,(int,float,intrange,floatrange)), msg
        if isinstance(self,intrange) and isinstance(other,int):
            return other in range(self._start,self._end+self._closed)
        elif isinstance(self,intrange) and isinstance(other,float):
            if self._closed:
                return self._start <= other <= self._end
            else:
                return self._start <= other <= (self._end - self._open)
        elif isinstance(other,(intrange,floatrange)):
            same_group = other._group == self._group
            if not same_group:
                return False
            starts_in = other._start in self
            ends_in  = other._end in self
            return starts_in or ends_in

    def __adjoins__(self,other):
        """whether self._end 'connects' to other._start

            :return: True|False
            :rtype: bool
            """
        return (self._end+self._closed)==other._start

    def __iter__(self):
        # enable iteration over your object
        # (assume step size is 1)
        yield from range(self._start, self._end+self._closed)

    def __len__(self):
        # return length (assuming step size of 1)
        return self._end-self._start + self._closed

    def extent(self):
        if isinstance(self,intrange):
            return self._end - self._start + self._closed
        elif isinstance(self,floatrange):
            return self._end-self._start

    def __comparison_key__(self,other):
        """sorting key as tuple of (group,start,end,and common attributes)"""
        if isinstance(other,intrange):
            s_attrib=(self._attributes[a] for a in self._attributes if a in other._attributes)
            return (self._group,self._start,self._end,*s_attrib)
        else:
            return NotImplementedError

    def __validranges__(self,*args):
        '''test that inputs are valid int or float ranges'''
        if isinstance(self,intrange):
            numeric=int
        elif isinstance(self,floatrange):
            numeric=float
        same=all(isinstance(obj,(type(self),numeric)) for obj in (self,*args))
        if same:
            return True
        else:
            raise TypeError

    def __group_attributes__(self,with_uuid=False):
        ''''''
        D = self._attributes.copy()
        if with_uuid:
            D['uuid'] = self._uuid
        D['group'] = self._group
        group = namedtuple("attributes",D.keys())(**D)
        return type(self)(self._start,self._end,group=group,uuid=self._uuid)

    def __ungroup_attributes__(self):
        ''''''
        D = dict(self._group._asdict())
        group  = D.pop("group")
        if "uuid" in D:
            uuid = D.pop("uuid")
        return type(self)(self._start,self._end,group=group,attributes=D,uuid=self._uuid)

    ## operator overloading
    def __lt__(self,other):
        s_key = self.__comparison_key__(other)
        o_key = other.__comparison_key__(self)
        return s_key < o_key

    def __gt__(self,other):
        s_key = self.__comparison_key__(other)
        o_key = other.__comparison_key__(self)
        return s_key > o_key

    def __le__(self,other):
        s_key = self.__comparison_key__(other)
        o_key = other.__comparison_key__(self)
        return s_key <= o_key

    def __ge__(self,other):
        s_key = self.__comparison_key__(other)
        o_key = other.__comparison_key__(self)
        return s_key >= o_key

    def __eq__(self,other):
        ''''''
        def equate(d1,d2):
            k1 = set(d1.keys())
            k2 = set(d2.keys())
            if len(k1) == len(k2) == len(k2.union(k1)):
                return all(d1[k] == d2[k] for k in k1)
            else:
                return False

        eq = ((self._start == other._start) and
              (self._end == other._end) and
              (self._closed == other._closed) and
              (self._group == other._group) and
              equate(self._attributes,other._attributes)
              )

        return eq

    def __sub__(self,other):
        '''difference of self from other'''
        if isinstance(other,(int,float)):
            return type(self)(self._start-other,self._end-other,uuid=self._uuid)
        elif isinstance(other,rangelist):
            current = self
            for elem in other:
                current -= elem
            return current
        elif self.__validranges__(other):
            # both_closed=self._closed and other._closed
            start_equal=self._start == other._start
            end_equal = (self._end+self._closed) == (other._end + other._closed)

            if other in self or self in other:
                starts_in = other._start in self
                ends_in  = other._end in self
                result=rangelist()
                if starts_in and not start_equal:
                    if isinstance(self,floatrange):
                        new = floatrange(self._start,other._start,
                                          step_size=self.step_size,
                                          group=self._group,
                                          attributes=self._attributes,
                                          uuid=self._uuid
                                         )
                    elif isinstance(self,intrange):
                        new = intrange(self._start,other._start-1,
                                        closed=True,
                                        group=self._group,
                                        attributes=self._attributes,
                                        uuid=self._uuid
                                        )

                    result.append(new)
                if ends_in and not end_equal:
                    if isinstance(self,floatrange):
                        new = floatrange(other._end+other._closed,
                                        self._end,
                                        step_size=self.step_size,
                                        group=self._group,
                                        attributes=self._attributes,
                                        uuid=self._uuid
                                        )
                    elif isinstance(self,intrange):
                        new = intrange(other._end+other._closed,
                                        self._end,
                                        closed=self._closed,
                                        group=self._group,
                                        attributes=self._attributes,
                                        uuid=self._uuid
                                        )
                    result.append(new)
                return result
            else:
                return rangelist((self,))

    def __add__(self,other):
        '''union of two ranges'''
        if isinstance(other,int):
            if isinstance(self,floatrange):
                return floatrange(self._start+other,self._end+other,
                              step_size=self.step_size,
                              group=self._group,
                              attributes=self._attributes,
                              uuid=self._uuid)
            elif isinstance(self,intrange):
                return intrange(self._start+other,self._end+other,
                              closed=self._closed,
                              group=self._group,
                              attributes=self._attributes,
                              uuid=self._uuid)
        elif self.__validranges__(other):
            result=rangelist()
            adjacent=(self.__adjoins__(other) or other.__adjoins__(self))
            if other in self or self in other or adjacent:
                result.append(type(self)(min(self._start,other._start),
                                         max(self._end,other._end),
                                         group=self._group,
                                         uuid=self._uuid
                                         )
                                )
                #TODO: how should attributes be handled?
            else:
                for i in sorted((self,other)):
                    result.append(i)
            return result

    #@_allow_for(types=(int,intrange,floatrange))
    def __mul__(self,other):
        '''intersection of two ranges'''
        if self.__validranges__(other):
            if other in self or self in other:
                newObj=type(self)
                return newObj(max(self._start, other._start),
                              min(self._end, other._end),
                              )
            else:
                if isinstance(self,floatrange):
                    return floatrange(0,0)
                elif isinstance(self,intrange):
                    return intrange(0,0,closed=False)


    def __floordiv__(self,other):
        '''remainder of self not intersecting other'''
        if isinstance(other,int):
            # cut the range at the point
            return self - type(self)(other,other)
        elif isinstance(other,float):
            # this will raise a type error if self is an intrange...
            return self - floatrange(other,other)
        if self.__validranges__(other):
            if other not in self and self not in other:
                return rangelist([self])
            intN = self*other
            return self-intN

    ## outputs
    def _astuple(self):
        names=("start","end","uuid")+tuple(self._attributes.keys())
        rangeTuple=namedtuple('rangeTuple',names)
        return rangeTuple(self._start,self._end,self._uuid,*self._attributes.values())

##
class floatrange(intrange):
    """range object of floating point stepped values between min and max.

    :param min_val: range start
    :type min_val: float


    :param max_val: range end
    :type max_val: float

    :param group: way of categorising ranges,
        used to sort and group them for other operations, defaults to (1,)
    :type group: tuple, can be other immutable objects,
        but ideally usage should be consistent for a collection of ranges

    :param attributes: any other properties associated with the range
    :type attributes: dict
    """
    def __init__(self,min_val,max_val,step_size=0.1,group=(1,),attributes={},uuid=None):
        self._start=float(min(min_val,max_val))
        self._end=float(max(min_val,max_val))
        self.step_size=step_size
        self._closed=0
        self._group=group
        self._attributes=attributes
        self._uuid = uuid or uuid4()
        assert isinstance(self._uuid,UUID), "attribute 'uuid' must be a UUID instance"
        assert "group" not in attributes,"reserved keyword 'group' should not be in attributes"
        assert "uuid" not in attributes,"reserved keyword 'uuid' should not be in attributes"


    def __len__(self):
        return (self._end-self._start)//self.step_size

    def extent(self):
        '''

        '''
        return (self._end-self._start)

    def __contains__(self, other):
        '''
        enable O(1) determination of whether a value is in your range
        '''
        msg="test value must be an int/float, or another intrange/floatrange"
        assert isinstance(other,(int,float,intrange,floatrange)),msg
        if isinstance(other,(int,float)):
            return self._start <= other <= self._end
        elif isinstance(other,(intrange,floatrange)):
            same_group = other._group == self._group
            if not same_group:
                return False
            starts_in = other._start in self
            ends_in  = other._end in self
            return starts_in or ends_in

    def __iter__(self):
        # enable iteration over your object
        # (assume step size is 1)
        n=self._start
        while n <=self._end:
            yield(n)
            n+=self.step_size

    def __repr__(self):
        '''string representing constructor for the object'''
        S = self._start
        E = self._end
        G=self._group
        A=self._attributes
        attrib = f",attributes={A}" if A else ""
        return f"floatrange({S},{E},group={G}{attrib})"

    def __str__(self):
        '''simplified fundamental range elements'''
        S = self._start
        E = self._end
        C = bool(self._closed)
        G=self._group
        # A=self._attributes
        return f"floatrange({S},{E},group={G})"

##
if __name__ == "__main__":
    ## TEMP TESTING BLOCK
    a=intrange(1,20)
    b=intrange(4,8)
    c=intrange(2,8)
    d=intrange(2,8,closed=False)
    e=intrange(7,40)

    variables=["a","b","c","d","e"]
    for n in variables:
        print(n,eval(n),sep=": ")

    print("a-b", a-b,sep=": ")

    print("1 in a",1 in a,sep=": ")
    print("8 in b",8 in b,sep=": ")
    print("12 in b",12 in b,sep=": ")

    operator_overloading=["a + b", "b + a", "a - b","b - a",
                          "a * b", "b * a", "a // b ",
                          "b // a", "b // 6",
                          "b - c", "b-d"]
    for ex in operator_overloading:
        print(ex,eval(ex),sep=": ")


    R = rangelist((a,e))
    print("rangelist((a,e))",":",R)
    ##
    X1 = floatrange(0,8,group=("a",),attributes={'date':"2024-01-01"})
    X2 = floatrange(6,14,group=("a",),attributes={'date':"2024-01-02"})
    X3 = floatrange(7,15,group=("a",),attributes={'date':"2024-01-03"})
    Y1 = floatrange(13,18,group=("b",),attributes={'date':"2024-01-05"})

    XY = rangelist((X1,X2,X3,Y1))

    print("XY list:")
    print(*XY,sep="\n")
    print("unique:")
    print(*XY.unique(),sep="\n")
    print("duplicates:")
    print(*(repr(xy) for xy in XY),sep="\n")

    for elem in XY:
        elem._attributes.pop("date")
    print("XY list:")
    print(*XY,sep="\n")
    print("unique:")
    print(*XY.unique(),sep="\n")
    print("duplicates:")
    print(*(repr(xy) for xy in XY.duplicates()),sep="\n")

    import pandas as pd

    df = pd.DataFrame.from_dict({'A':[1,2,3,4,5],'B':[10,10,10,10,10]})

    R=rangelist.from_dataframe(df,"A","B",[],step_size=0.1)
    print(R)
    print(R.unique())


