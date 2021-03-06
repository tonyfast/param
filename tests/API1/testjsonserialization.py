"""
Testing JSON serialization of parameters and the corresponding schemas.
"""

import json
import datetime
import param
from unittest import SkipTest
from . import API1TestCase

try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None

try:
    import numpy as np
    ndarray = np.array([[1,2,3],[4,5,6]])
except:
    np, ndarray = None, None

try:
    import pandas as pd
    df1 = pd.DataFrame({'A':[1,2,3], 'B':[1.1,2.2,3.3]})
    df2 = pd.DataFrame({'A':[1.1,2.2,3.3], 'B':[1.1,2.2,3.3]})
except:
    pd, df1, df2 = None, None, None


simple_list = [1]

class TestSet(param.Parameterized):

    numpy_params = ['r']
    pandas_params = ['s','t','u']
    conditionally_unsafe = ['f', 'o']

    a = param.Integer(default=5, doc='Example doc', bounds=(2,30), inclusive_bounds=(True, False))
    b = param.Number(default=4.3, allow_None=True)
    c = param.String(default='foo')
    d = param.Boolean(default=False)
    e = param.List([1,2,3], class_=int)
    f = param.List([1,2,3])
    g = param.Date(default=datetime.datetime.now())
    h = param.Tuple(default=(1,2,3), length=3)
    i = param.NumericTuple(default=(1,2,3,4))
    j = param.XYCoordinates(default=(32.1, 51.5))
    k = param.Integer(default=1)
    l = param.Range(default=(1.1,2.3), bounds=(1,3))
    m = param.String(default='baz', allow_None=True)
    n = param.ObjectSelector(default=3, objects=[3,'foo'], allow_None=False)
    o = param.ObjectSelector(default=simple_list, objects=[simple_list], allow_None=False)
    p = param.ListSelector(default=[1,4,5], objects=[1,2,3,4,5,6])
    q = param.CalendarDate(default=datetime.date.today())
    r = None if np is None else param.Array(default=ndarray)
    s = None if pd is None else param.DataFrame(default=df1, columns=2)
    t = None if pd is None else param.DataFrame(default=pd.DataFrame(
        {'A':[1,2,3], 'B':[1.1,2.2,3.3]}), columns=(1,4), rows=(2,5))
    u = None if pd is None else param.DataFrame(default=df2, columns=['A', 'B'])
    v = param.Dict({'1':2})


test = TestSet(a=29)


class TestJSONSerialization(API1TestCase):

    def test_serialize_integer_class(self):
        serialization = TestSet.param.serialize_parameters(subset=['a'], mode='json')
        deserialized = json.loads(serialization)
        self.assertEqual(TestSet.a, 5)
        self.assertEqual(deserialized, {'a':TestSet.a})

    def test_serialize_integer_instance(self):
        serialization = test.param.serialize_parameters(subset=['a'], mode='json')
        deserialized = json.loads(serialization)
        self.assertEqual(test.a, 29)
        self.assertEqual(deserialized, {'a':test.a})

    def test_serialize_integer_schema_class(self):
        if validate is None:
            raise SkipTest('jsonschema needed for schema validation testing')
        param_schema = TestSet.param.schema(safe=True, subset=['a'], mode='json')
        schema = {"type" : "object", "properties" : param_schema}
        serialized = json.loads(TestSet.param.serialize_parameters(subset=['a']))
        self.assertEqual({'a':
                          {'type': 'integer', 'minimum': 2, 'exclusiveMaximum': 30,
                           'description': 'Example doc', 'title': 'A'}},
                         param_schema)
        validate(instance=serialized, schema=schema)

    def test_serialize_integer_schema_class_invalid(self):
        if validate is None:
            raise SkipTest('jsonschema needed for schema validation testing')
        param_schema = TestSet.param.schema(safe=True, subset=['a'], mode='json')
        schema = {"type" : "object", "properties" : param_schema}
        self.assertEqual({'a':
                          {'type': 'integer', 'minimum': 2, 'exclusiveMaximum': 30,
                           'description': 'Example doc', 'title': 'A'}},
                         param_schema)

        exception = "1 is not of type 'object'"
        with self.assertRaisesRegexp(ValidationError, exception):
            validate(instance=1, schema=schema)

    def test_serialize_integer_schema_instance(self):
        if validate is None:
            raise SkipTest('jsonschema needed for schema validation testing')
        param_schema = test.param.schema(safe=True, subset=['a'], mode='json')
        schema = {"type" : "object", "properties" : param_schema}
        serialized = json.loads(test.param.serialize_parameters(subset=['a']))
        self.assertEqual({'a':
                          {'type': 'integer', 'minimum': 2, 'exclusiveMaximum': 30,
                           'description': 'Example doc', 'title': 'A'}},
                         param_schema)
        validate(instance=serialized, schema=schema)

    def test_instance_serialization(self):
        excluded = test.numpy_params + test.pandas_params
        for param_name in list(test.param):
            if param_name in excluded:
                continue
            original_value = getattr(test, param_name)
            serialization = test.param.serialize_parameters(subset=[param_name], mode='json')
            json_loaded = json.loads(serialization)
            deserialized_values = test.param.deserialize_parameters(json_loaded)
            deserialized_value = deserialized_values[param_name]
            self.assertEqual(original_value, deserialized_value)

    def test_numpy_instance_serialization(self):
        if np is None:
            raise SkipTest('Numpy needed test array serialization')

        for param_name in test.numpy_params:
            original_value = getattr(test, param_name)
            serialization = test.param.serialize_parameters(subset=[param_name], mode='json')
            json_loaded = json.loads(serialization)
            deserialized_values = test.param.deserialize_parameters(json_loaded)
            deserialized_value = deserialized_values[param_name]
            self.assertEqual(np.array_equal(original_value, deserialized_value), True)

    def test_numpy_schemas_always_unsafe(self):
        if np is None:
            raise SkipTest('Numpy needed test array serialization')

        for param_name in test.numpy_params:
            with self.assertRaisesRegexp(param.serializer.UnsafeserializableException,''):
                test.param.schema(safe=True, subset=[param_name], mode='json')

    def test_pandas_instance_serialization(self):
        if pd is None:
            raise SkipTest('Pandas needed to test dataframe serialization')

        for param_name in test.pandas_params:
            original_value = getattr(test, param_name)
            serialization = test.param.serialize_parameters(subset=[param_name], mode='json')
            json_loaded = json.loads(serialization)
            deserialized_values = test.param.deserialize_parameters(json_loaded)
            deserialized_value = deserialized_values[param_name]
            self.assertEqual(original_value.equals(deserialized_value), True)

    def test_pandas_schemas_always_unsafe(self):
        if pd is None:
            raise SkipTest('Pandas needed test dataframe serialization')

        for param_name in test.pandas_params:
            with self.assertRaisesRegexp(param.serializer.UnsafeserializableException,''):
                test.param.schema(safe=True, subset=[param_name], mode='json')

    def test_class_instance_schemas_match_and_validate_unsafe(self):
        if validate is None:
            raise SkipTest('jsonschema needed for schema validation testing')

        for param_name in list(test.param):
            class_schema = TestSet.param.schema(safe=False, subset=[param_name], mode='json')
            instance_schema = test.param.schema(safe=False, subset=[param_name], mode='json')
            self.assertEqual(class_schema, instance_schema)

            instance_serialization_val = test.param.serialize_parameters(subset=[param_name])
            validate(instance=instance_serialization_val, schema=class_schema)

            class_serialization_val = TestSet.param.serialize_parameters(subset=[param_name])
            validate(instance=class_serialization_val, schema=class_schema)


    def test_conditionally_unsafe(self):
        for param_name in test.conditionally_unsafe:
            with self.assertRaisesRegexp(param.serializer.UnsafeserializableException,''):
                test.param.schema(safe=True, subset=[param_name], mode='json')
