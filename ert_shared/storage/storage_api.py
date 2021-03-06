from io import StringIO

import pandas as pd
from ert_shared.storage.blob_api import BlobApi
from ert_shared.storage.rdb_api import RdbApi


class StorageApi(object):
    def __init__(self, rdb_api, blob_api):
        self._rdb_api = rdb_api
        self._blob_api = blob_api

    def _ensemble_minimal(self, ensemble):
        if ensemble is None:
            return None
        return {
            "name": ensemble.name,
            "time_created": ensemble.time_created.isoformat(),
            "ensemble_ref": ensemble.id,
            "parent": {
                "ensemble_ref": ensemble.parent.ensemble_reference.id,
                "name": ensemble.parent.ensemble_reference.name,
            }
            if ensemble.parent is not None
            else {},
            "children": [
                {
                    "ensemble_ref": child.ensemble_result.id,
                    "name": child.ensemble_result.name,
                }
                for child in ensemble.children
            ],
        }

    def get_ensembles(self, filter=None):
        data = [
            self._ensemble_minimal(ensemble)
            for ensemble in self._rdb_api.get_all_ensembles()
        ]

        return {"ensembles": data}

    def get_realization(self, ensemble_id, realization_idx, filter):
        realization = self._rdb_api.get_realization_by_realization_idx(
            ensemble_id=ensemble_id, realization_idx=realization_idx
        )

        if realization is None:
            return None

        response_definitions = self._rdb_api.get_response_definitions_by_ensemble_id(
            ensemble_id=ensemble_id
        )
        responses = [
            {
                "name": resp_def.name,
                "response": self._rdb_api.get_response_by_realization_id(
                    response_definition_id=resp_def.id,
                    realization_id=realization.id,
                ),
            }
            for resp_def in response_definitions
        ]

        parameter_definitions = self._rdb_api.get_parameter_definitions_by_ensemble_id(
            ensemble_id=ensemble_id
        )
        parameters = [
            {
                "name": param_def.name,
                "parameter": self._rdb_api.get_parameter_by_realization_id(
                    parameter_definition_id=param_def.id,
                    realization_id=realization.id,
                ),
            }
            for param_def in parameter_definitions
        ]

        return_schema = {
            "name": realization.index,
            "responses": [
                {"name": res["name"], "data_ref": res["response"].values_ref}
                for res in responses
            ],
            "parameters": [
                {"name": par["name"], "data_ref": par["parameter"].value_ref}
                for par in parameters
            ],
        }

        return return_schema

    def _calculate_misfit(
        self, obs_value, response_values, obs_stds, obs_data_indexes, obs_index
    ):
        observation_std = obs_stds[obs_index]
        response_index = obs_data_indexes[obs_index]
        response_value = response_values[response_index]
        difference = response_value - obs_value
        misfit = (difference / observation_std) ** 2
        sign = difference > 0

        return {"value": misfit, "sign": sign, "obs_index": obs_index}

    def get_response(self, ensemble_id, response_name, filter):
        bundle = self._rdb_api.get_response_bundle(
            response_name=response_name, ensemble_id=ensemble_id
        )
        if bundle is None:
            return None

        observation_links = bundle.observation_links
        responses = bundle.responses
        univariate_misfits = {}
        for resp in responses:
            resp_values = list(self._blob_api.get_blob(resp.values_ref).data)
            univariate_misfits[resp.realization.index] = {}
            for link in observation_links:
                observation = link.observation
                obs_values = list(self._blob_api.get_blob(observation.values_ref).data)
                obs_stds = list(self._blob_api.get_blob(observation.stds_ref).data)
                obs_data_indexes = list(
                    self._blob_api.get_blob(observation.data_indexes_ref).data
                )
                misfits = []
                for obs_index, obs_value in enumerate(obs_values):
                    misfits.append(
                        self._calculate_misfit(
                            obs_value,
                            resp_values,
                            obs_stds,
                            obs_data_indexes,
                            obs_index,
                        )
                    )
                univariate_misfits[resp.realization.index][observation.name] = misfits

        return_schema = {
            "name": response_name,
            "ensemble_id": ensemble_id,
            "realizations": [
                {
                    "name": resp.realization.index,
                    "realization_ref": resp.realization.index,
                    "data_ref": resp.values_ref,
                    "summarized_misfits": {
                        misfit.observation_response_definition_link.observation.name: misfit.value
                        for misfit in resp.misfits
                    },
                    "univariate_misfits": {
                        obs_name: misfits
                        for obs_name, misfits in univariate_misfits[
                            resp.realization.index
                        ].items()
                    },
                }
                for resp in responses
            ],
            "axis": {"data_ref": bundle.indexes_ref},
        }
        if len(observation_links) > 0:
            return_schema["observations"] = [
                self._obs_to_json(link.observation, link.active_ref)
                for link in observation_links
            ]

        return return_schema

    def get_response_data(self, ensemble_id, response_name):
        bundle = self._rdb_api.get_response_bundle(
            response_name=response_name, ensemble_id=ensemble_id
        )
        if bundle is None:
            return None
        responses = bundle.responses

        ids = [resp.values_ref for resp in responses]
        return ids

    def get_data(self, id):
        blob = self._blob_api.get_blob(id)
        if blob is None:
            return None
        return blob.data

    def get_datas(self, id):
        for response in self._blob_api.get_blobs(id):
            yield response.data

    def get_observation(self, name):
        obs = self._rdb_api.get_observation(name)
        return None if obs is None else self._obs_to_json(obs)

    def get_observation_attributes(self, name):
        attrs = self._rdb_api.get_observation_attributes(name)
        return None if attrs is None else {"attributes": attrs}

    def get_observation_attribute(self, name, attribute):
        attr = self._rdb_api.get_observation_attribute(name, attribute)
        return None if attr is None else {"attributes": {attribute: attr}}

    def set_observation_attribute(self, name, attribute, value):
        obs = self._rdb_api.add_observation_attribute(name, attribute, value)
        if obs is None:
            return None
        return self._obs_to_json(obs)

    def get_ensemble(self, ensemble_id):
        ens = self._rdb_api.get_ensemble_by_id(ensemble_id)

        if ens is None:
            return None

        return_schema = self._ensemble_minimal(ens)
        return_schema.update(
            {
                "realizations": [
                    {"name": real.index, "realization_ref": real.index}
                    for real in self._rdb_api.get_realizations_by_ensemble_id(
                        ensemble_id
                    )
                ],
                "responses": [
                    {"name": resp.name, "response_ref": resp.name}
                    for resp in self._rdb_api.get_response_definitions_by_ensemble_id(
                        ensemble_id
                    )
                ],
                "parameters": [
                    self._parameter_minimal(
                        name=par.name,
                        group=par.group,
                        prior=par.prior,
                        parameter_def_id=par.id,
                    )
                    for par in self._rdb_api.get_parameter_definitions_by_ensemble_id(
                        ensemble_id
                    )
                ],
            }
        )
        return return_schema

    def _obs_to_json(self, obs, active_ref=None):
        data = {
            "name": obs.name,
            "data": {
                "values": {"data_ref": obs.values_ref},
                "std": {"data_ref": obs.stds_ref},
                "data_indexes": {"data_ref": obs.data_indexes_ref},
                "key_indexes": {"data_ref": obs.key_indexes_ref},
            },
        }
        if active_ref is not None:
            data["data"]["active_mask"] = {"data_ref": active_ref}

        attrs = obs.get_attributes()
        if len(attrs) > 0:
            data["attributes"] = attrs

        return data

    def _parameter_minimal(self, name, group, prior, parameter_def_id):
        return {
            "key": name,
            "group": group,
            "parameter_ref": parameter_def_id,
            "prior": {
                "function": prior.function,
                "parameter_names": prior.parameter_names,
                "parameter_values": prior.parameter_values,
            }
            if prior is not None
            else {},
        }

    def get_parameter(self, ensemble_id, parameter_def_id):
        bundle = self._rdb_api.get_parameter_bundle(
            parameter_def_id=parameter_def_id, ensemble_id=ensemble_id
        )
        if bundle is None:
            return None

        return_schema = self._parameter_minimal(
            name=bundle.name,
            group=bundle.group,
            prior=bundle.prior,
            parameter_def_id=parameter_def_id,
        )

        return_schema["parameter_realizations"] = [
            {
                "name": param.realization.index,
                "data_ref": param.value_ref,
                "realization": {"realization_ref": param.realization.index},
            }
            for param in bundle.parameters
        ]
        return return_schema

    def get_parameter_data(self, ensemble_id, parameter_def_id):
        bundle = self._rdb_api.get_parameter_bundle(
            parameter_def_id=parameter_def_id, ensemble_id=ensemble_id
        )
        if bundle is None:
            return None

        ids = [param.value_ref for param in bundle.parameters]
        return ids
