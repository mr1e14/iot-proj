import unittest


def load_tests(loader, standard_tests, pattern):
    return unittest.defaultTestLoader.discover('iot_app.test')


if __name__ == '__main__':
    unittest.main()
