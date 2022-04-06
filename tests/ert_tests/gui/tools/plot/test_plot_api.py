import os
import shutil
from unittest import TestCase
from unittest.mock import MagicMock
import pytest
from utils import SOURCE_DIR
from ert_utils import tmpdir
from pandas import DataFrame
from ert_shared.services import Storage
from ert_gui.tools.plot.plot_api import PlotApi
from ert_shared.libres_facade import LibresFacade
from res.enkf import EnKFMain, ResConfig

_KEY_DEFS = (
    {
        "key": "BPR:1,3,8",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "BPR:445",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "FOPT",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "FOPTH",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "WGOR:OP1",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "WGORH:OP1",
        "index_type": "VALUE",
        "observations": [],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "WOPR:OP1",
        "index_type": "VALUE",
        "observations": [
            "WOPR_OP1_108",
            "WOPR_OP1_190",
            "WOPR_OP1_144",
            "WOPR_OP1_9",
            "WOPR_OP1_72",
            "WOPR_OP1_36",
        ],
        "has_refcase": True,
        "dimensionality": 2,
        "metadata": {"data_origin": "Summary"},
        "log_scale": False,
    },
    {
        "key": "SNAKE_OIL_PARAM:BPR_138_PERSISTENCE",
        "index_type": None,
        "observations": [],
        "has_refcase": False,
        "dimensionality": 1,
        "metadata": {"data_origin": "Gen KW"},
        "log_scale": False,
    },
    {
        "key": "SNAKE_OIL_GPR_DIFF@199",
        "index_type": "INDEX",
        "observations": [],
        "has_refcase": False,
        "dimensionality": 2,
        "metadata": {"data_origin": "Gen Data"},
        "log_scale": False,
    },
    {
        "key": "SNAKE_OIL_WPR_DIFF@199",
        "index_type": "INDEX",
        "observations": ["WPR_DIFF_1"],
        "has_refcase": False,
        "dimensionality": 2,
        "metadata": {"data_origin": "Gen Data"},
        "log_scale": False,
    },
)


class PlotApiTest(TestCase):
    def api(self):
        config_file = "snake_oil.ert"

        rc = ResConfig(user_config_file=config_file)
        rc.convertToCReference(None)
        ert = EnKFMain(rc)
        facade = LibresFacade(ert)
        api = PlotApi(facade)
        return api

    @tmpdir(SOURCE_DIR / "test-data/local/snake_oil")
    def test_all_keys_present(self):
        api = self.api()

        key_defs = api.all_data_type_keys()
        keys = {x["key"] for x in key_defs}
        expected = {
            "BPR:1,3,8",
            "BPR:445",
            "BPR:5,5,5",
            "BPR:721",
            "FGIP",
            "FGIPH",
            "FGOR",
            "FGORH",
            "FGPR",
            "FGPRH",
            "FGPT",
            "FGPTH",
            "FOIP",
            "FOIPH",
            "FOPR",
            "FOPRH",
            "FOPT",
            "FOPTH",
            "FWCT",
            "FWCTH",
            "FWIP",
            "FWIPH",
            "FWPR",
            "FWPRH",
            "FWPT",
            "FWPTH",
            "TIME",
            "WGOR:OP1",
            "WGOR:OP2",
            "WGORH:OP1",
            "WGORH:OP2",
            "WGPR:OP1",
            "WGPR:OP2",
            "WGPRH:OP1",
            "WGPRH:OP2",
            "WOPR:OP1",
            "WOPR:OP2",
            "WOPRH:OP1",
            "WOPRH:OP2",
            "WWCT:OP1",
            "WWCT:OP2",
            "WWCTH:OP1",
            "WWCTH:OP2",
            "WWPR:OP1",
            "WWPR:OP2",
            "WWPRH:OP1",
            "WWPRH:OP2",
            "SNAKE_OIL_PARAM:BPR_138_PERSISTENCE",
            "SNAKE_OIL_PARAM:BPR_555_PERSISTENCE",
            "SNAKE_OIL_PARAM:OP1_DIVERGENCE_SCALE",
            "SNAKE_OIL_PARAM:OP1_OCTAVES",
            "SNAKE_OIL_PARAM:OP1_OFFSET",
            "SNAKE_OIL_PARAM:OP1_PERSISTENCE",
            "SNAKE_OIL_PARAM:OP2_DIVERGENCE_SCALE",
            "SNAKE_OIL_PARAM:OP2_OCTAVES",
            "SNAKE_OIL_PARAM:OP2_OFFSET",
            "SNAKE_OIL_PARAM:OP2_PERSISTENCE",
            "SNAKE_OIL_GPR_DIFF@199",
            "SNAKE_OIL_OPR_DIFF@199",
            "SNAKE_OIL_WPR_DIFF@199",
        }
        self.assertSetEqual(expected, keys)

    @tmpdir(SOURCE_DIR / "test-data/local/snake_oil")
    def test_observation_key_present(self):
        api = self.api()
        key_defs = api.all_data_type_keys()
        expected_obs = {
            "FOPR": ["FOPR"],
            "WOPR:OP1": [
                "WOPR_OP1_108",
                "WOPR_OP1_190",
                "WOPR_OP1_144",
                "WOPR_OP1_9",
                "WOPR_OP1_72",
                "WOPR_OP1_36",
            ],
            "SNAKE_OIL_WPR_DIFF@199": ["WPR_DIFF_1"],
        }

        for key_def in key_defs:
            if key_def["key"] in expected_obs:
                expected = expected_obs[key_def["key"]]
                self.assertEqual(expected, key_def["observations"])
            else:
                self.assertEqual(0, len(key_def["observations"]))


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def test_key_def_structure(api):
    shutil.rmtree("storage", ignore_errors=True)
    key_defs = api.all_data_type_keys()
    fopr = next(x for x in key_defs if x["key"] == "FOPR")

    expected = {
        "dimensionality": 2,
        "has_refcase": True,
        "index_type": "VALUE",
        "key": "FOPR",
        "metadata": {"data_origin": "Summary"},
        "observations": ["FOPR"],
        "log_scale": False,
    }

    assert fopr == expected


def mocked_requests_get(*args, **kwargs):
    ensemble = {
        "/ensembles/ens_id_1": {"name": "ensemble_1"},
        "/ensembles/ens_id_2": {"name": ".ensemble_2"},
        "/ensembles/ens_id_3": {"name": "default_0"},
        "/ensembles/ens_id_4": {"name": "default_1"},
    }
    observations = {
        "/ensembles/ens_id_3/records/WOPR:OP1/observations": {
            "name": "WOPR:OP1",
            "errors": [0.05, 0.07],
            "values": [0.1, 0.7],
            "x_axis": ["2010-03-31T00:00:00", "2010-12-26T00:00:00"],
        },
        "/ensembles/ens_id_4/records/WOPR:OP1/observations": {
            "name": "WOPR:OP1",
            "errors": [0.05, 0.07],
            "values": [0.1, 0.7],
            "x_axis": ["2010-03-31T00:00:00", "2010-12-26T00:00:00"],
        },
        "/ensembles/ens_id_3/records/SNAKE_OIL_WPR_DIFF@199/observations": {
            "name": "SNAKE_OIL_WPR_DIFF",
            "errors": [0.05, 0.07, 0.05],
            "values": [0.1, 0.7, 0.5],
            "x_axis": [
                "2010-03-31T00:00:00",
                "2010-12-26T00:00:00",
                "2011-12-21T00:00:00",
            ],
        },
        "/ensembles/ens_id_4/records/SNAKE_OIL_WPR_DIFF@199/observations": {
            "name": "WOPR:OP1",
            "errors": [0.05, 0.07, 0.05],
            "values": [0.1, 0.7, 0.5],
            "x_axis": [
                "2010-03-31T00:00:00",
                "2010-12-26T00:00:00",
                "2011-12-21T00:00:00",
            ],
        },
    }

    if args[0] in ensemble:
        return MockResponse({"userdata": ensemble[args[0]]}, 200)
    elif args[0] in observations:
        return MockResponse(
            [observations[args[0]]],
            200,
        )
    elif "/experiments" in args[0]:
        return MockResponse(
            [
                {
                    "name": "default",
                    "id": "exp_1",
                    "ensemble_ids": ["ens_id_1", "ens_id_2", "ens_id_3", "ens_id_4"],
                    "priors": {},
                    "userdata": {},
                }
            ],
            200,
        )

    return MockResponse(None, 404)


def test_case_structure(api):
    cases = [case["name"] for case in api.get_all_cases_not_running()]
    hidden_case = [
        case["name"] for case in api.get_all_cases_not_running() if case["hidden"]
    ]
    expected = ["ensemble_1", ".ensemble_2", "default_0", "default_1"]

    assert cases == expected
    assert hidden_case == [".ensemble_2"]


@pytest.fixture
def api(tmpdir, source_root, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def session():
        yield MagicMock(get=mocked_requests_get)

    monkeypatch.setattr(Storage, "session", session)

    with tmpdir.as_cwd():
        test_data_root = source_root / "test-data" / "local"
        test_data_dir = os.path.join(test_data_root, "snake_oil")
        shutil.copytree(test_data_dir, "test_data")
        os.chdir("test_data")
        config_file = "snake_oil.ert"
        rc = ResConfig(user_config_file=config_file)
        rc.convertToCReference(None)
        ert = EnKFMain(rc)
        facade = LibresFacade(ert)
        api = PlotApi(facade)
        yield api


def get_id(val):
    return f"case name: {val}"


def get_key_name(val):
    return f"key_def: {val['key']}"


@pytest.mark.parametrize("case_name", ["default_0", "default_1"], ids=get_id)
@pytest.mark.parametrize("key_def", _KEY_DEFS, ids=get_key_name)
def test_no_storage(case_name, key_def, api):
    shutil.rmtree("storage", ignore_errors=True)
    obs = key_def["observations"]
    obs_data = api.observations_for_key(case_name, key_def["key"])
    data = api.data_for_key(case_name, key_def["key"])
    assert isinstance(obs_data, DataFrame)
    assert isinstance(data, DataFrame)
    assert data.empty


@pytest.mark.parametrize("case_name", ["default_0", "default_1"], ids=get_id)
@pytest.mark.parametrize("key_def", _KEY_DEFS, ids=get_key_name)
def test_can_load_data_and_observations(case_name, key_def, api):
    obs = key_def["observations"]
    obs_data = api.observations_for_key(case_name, key_def["key"])
    data = api.data_for_key(case_name, key_def["key"])

    assert isinstance(data, DataFrame)
    assert not data.empty

    assert isinstance(obs_data, DataFrame)
    if len(obs) > 0:
        assert not obs_data.empty
