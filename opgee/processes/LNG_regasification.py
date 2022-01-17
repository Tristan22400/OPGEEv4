from ..log import getLogger
from ..process import Process
from .shared import get_energy_carrier
from ..emissions import EM_COMBUSTION, EM_FUGITIVES

_logger = getLogger(__name__)


class LNGRegasification(Process):
    """
    LNG liquefaction calculate emission of transported gas to regasification

    """
    def _after_init(self):
        super()._after_init()
        self.field = field = self.get_field()
        self.gas = field.gas
        self.energy_intensity_regas = self.attr("energy_intensity_regas")
        self.efficiency = self.attr("efficiency")
        self.prime_mover_type = self.attr("prime_mover_type")

    def run(self, analysis):
        self.print_running_msg()

        input = self.find_input_stream("gas")

        if input.is_uninitialized():
            return

        gas_mass_rate = input.total_gas_rate()
        gas_mass_energy_density = self.gas.mass_energy_density(input)
        gas_LHV_rate = gas_mass_rate * gas_mass_energy_density
        total_regasification_requirement = self.energy_intensity_regas * gas_LHV_rate

        energy_consumption = self.get_energy_consumption(self.prime_mover_type, total_regasification_requirement)
        frac_fuel_gas = energy_consumption / gas_LHV_rate
        gas_to_distribution = self.find_output_stream("gas for distribution")
        gas_to_distribution.copy_flow_rates_from(input)
        gas_to_distribution.multiply_flow_rates(1 - frac_fuel_gas.to("frac").m)

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        # emissions
        emissions = self.emissions
        energy_for_combustion = energy_use.data.drop("Electricity")
        combustion_emission = (energy_for_combustion * self.process_EF).sum()
        emissions.set_rate(EM_COMBUSTION, "CO2", combustion_emission)






