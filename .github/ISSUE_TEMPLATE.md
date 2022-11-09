When reporting an issue, include a way to reproduce the bug. For example:

#### Command used to run pytest
````pytest test_example.py````

#### Test file
````python
def test_example():
    assert False
````

#### Output
````
Results (0.12s):
       5 passed
       1 failed
         - faketests/animals/test_one_failing_test.py:16: assert False
````
