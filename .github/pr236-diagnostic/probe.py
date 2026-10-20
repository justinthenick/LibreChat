"""Expose chained exceptions only in the existing synthetic bounded-LLM tests."""
import json
import runpy
import sys
import traceback
import unittest
from pathlib import Path

original_discover = unittest.TestLoader.discover

def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
    return original_discover(self, start_dir, 'test_bounded_llm.py', top_level_dir)

class DiagnosticResult(unittest.TextTestResult):
    def record(self, test, err):
        if err is None:
            return
        chain, seen = [], set()
        error = err[1]
        while error is not None and id(error) not in seen:
            seen.add(id(error))
            chain.append({'type': type(error).__module__ + '.' + type(error).__qualname__,
                          'message': str(error) if type(error) in (AttributeError, TypeError, ImportError, NameError) else '[omitted: exception may contain request data]',
                          'frames': [{'file': frame.filename, 'line': frame.lineno, 'function': frame.name}
                                     for frame in traceback.extract_tb(error.__traceback__)]})
            error = error.__cause__ or error.__context__
        print('SYNTHETIC_EXCEPTION_CHAIN ' + json.dumps({'test': str(test), 'chain': chain}), flush=True)

    def addError(self, test, err):
        self.record(test, err)
        super().addError(test, err)

    def addFailure(self, test, err):
        self.record(test, err)
        super().addFailure(test, err)

    def addSubTest(self, test, subtest, err):
        self.record(subtest, err)
        super().addSubTest(test, subtest, err)

unittest.TestLoader.discover = discover
unittest.TextTestRunner.resultclass = DiagnosticResult
# The original runner clears the environment and installs its network guards.
# The selected test class also forbids DNS, sockets and credential-store access.
runpy.run_path(str(Path('tests/run_tests.py')), run_name='__main__')
