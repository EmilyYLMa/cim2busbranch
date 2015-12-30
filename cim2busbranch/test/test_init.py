from mock import patch

import cim2busbranch


pytest_plugins = 'cim2busbranch.test.support'


# @patch('cim2busbranch.cim2bb.transform')
# @patch('PyCIM.cimread')
# def test_transform(cimread_mock, transform_mock):
#     import pytest; pytest.skip()
#     cim_path = '/spam/eggs.rdf'
#     cim = {}
#     case = 'ohai'

#     cimread_mock.return_value = cim
#     transform_mock.return_value = case

#     ret = cim2busbranch.transform(cim_path)
#     assert ret is case
#     cimread_mock.assert_called_once_with(cim_path)
#     transform_mock.assert_called_once_with(cim)

#     cimread_mock.reset_mock()
#     transform_mock.reset_mock()

#     ret = cim2busbranch.transform(cim)
#     assert ret is case
#     assert cimread_mock.call_count == 0
#     transform_mock.assert_called_once_with(cim)


def test_run_pypower(case, ppc):
    import pytest; pytest.skip()
    cim_path = '/spam/eggs.rdf'
    case = []
    pp_case = []

    with patch('cim2busbranch.transform') as transform_mock:
        with patch('cim2busbranch.ext_pypower.create') as create_mock:

            create_mock.return_value = pp_case
            transform_mock.return_value = case

            ret = cim2busbranch.run_pypower(cim_path)
            assert ret is pp_case
            transform_mock.assert_called_once_with(cim_path)
            create_mock.assert_called_once_with(case)

            transform_mock.reset_mock()
            create_mock.reset_mock()

            ret = cim2busbranch.pypower_case(case)
            assert ret is pp_case
            assert transform_mock.call_count == 0
            create_mock.assert_called_once_with(case)
