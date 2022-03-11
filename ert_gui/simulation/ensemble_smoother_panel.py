from qtpy.QtWidgets import QFormLayout, QLabel

from ert_gui.ertnotifier import ErtNotifier
from ert_gui.ertwidgets import addHelpToWidget, AnalysisModuleSelector
from ert_gui.ertwidgets.caseselector import CaseSelector
from ert_gui.ertwidgets.models.activerealizationsmodel import ActiveRealizationsModel
from ert_gui.ertwidgets.models.ertmodel import (
    get_runnable_realizations_mask,
)
from ert_gui.ertwidgets.models.targetcasemodel import TargetCaseModel
from ert_gui.ertwidgets.stringbox import StringBox
from ert_shared.ide.keywords.definitions import RangeStringArgument, ProperNameArgument
from ert_gui.simulation import SimulationConfigPanel
from ert_shared.libres_facade import LibresFacade
from ert_shared.models import EnsembleSmoother
from res.enkf import EnKFMain


class EnsembleSmootherPanel(SimulationConfigPanel):
    def __init__(self, ert: EnKFMain, notifier: ErtNotifier):
        super().__init__(EnsembleSmoother)
        self.ert = ert
        facade = LibresFacade(ert)
        layout = QFormLayout()

        self._case_selector = CaseSelector(facade, notifier)
        layout.addRow("Current case:", self._case_selector)

        run_path_label = QLabel("<b>%s</b>" % facade.run_path)
        addHelpToWidget(run_path_label, "config/simulation/runpath")
        layout.addRow("Runpath:", run_path_label)

        number_of_realizations_label = QLabel("<b>%d</b>" % facade.get_ensemble_size())
        addHelpToWidget(
            number_of_realizations_label, "config/ensemble/num_realizations"
        )
        layout.addRow(QLabel("Number of realizations:"), number_of_realizations_label)

        self._target_case_model = TargetCaseModel(facade, notifier)
        self._target_case_field = StringBox(
            self._target_case_model, "config/simulation/target_case"
        )
        self._target_case_field.setValidator(ProperNameArgument())
        layout.addRow("Target case:", self._target_case_field)

        self._analysis_module_selector = AnalysisModuleSelector(
            facade,
            iterable=False,
            help_link="config/analysis/analysis_module",
        )
        layout.addRow("Analysis Module:", self._analysis_module_selector)

        active_realizations_model = ActiveRealizationsModel(facade)
        self._active_realizations_field = StringBox(
            active_realizations_model, "config/simulation/active_realizations"
        )
        self._active_realizations_field.setValidator(
            RangeStringArgument(facade.get_ensemble_size())
        )
        layout.addRow("Active realizations", self._active_realizations_field)

        self.setLayout(layout)

        self._target_case_field.getValidationSupport().validationChanged.connect(
            self.simulationConfigurationChanged
        )
        self._active_realizations_field.getValidationSupport().validationChanged.connect(
            self.simulationConfigurationChanged
        )
        self._case_selector.currentIndexChanged.connect(self._realizations_from_fs)

        self._realizations_from_fs()  # update with the current case

    def isConfigurationValid(self):
        return (
            self._target_case_field.isValid()
            and self._active_realizations_field.isValid()
        )

    def getSimulationArguments(self):
        arguments = {
            "active_realizations": self._active_realizations_field.model.getActiveRealizationsMask(),
            "target_case": self._target_case_model.getValue(),
            "analysis_module": self._analysis_module_selector.getSelectedAnalysisModuleName(),
        }
        return arguments

    def _realizations_from_fs(self):
        case = str(self._case_selector.currentText())
        mask = get_runnable_realizations_mask(self.ert, case)
        self._active_realizations_field.model.setValueFromMask(mask)
