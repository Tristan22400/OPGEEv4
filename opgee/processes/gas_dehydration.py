import numpy as np

from ..log import getLogger
from ..process import Process
from ..stream import PHASE_LIQUID
from opgee import ureg
from ..thermodynamics import component_MW
from ..process import run_corr_eqns
from ..energy import Energy, EN_NATURAL_GAS, EN_ELECTRICITY
from ..emissions import Emissions, EM_COMBUSTION, EM_LAND_USE, EM_VENTING, EM_FLARING, EM_FUGITIVES

_logger = getLogger(__name__)


class GasDehydration(Process):
    def _after_init(self):
        super()._after_init()
        self.field = field = self.get_field()
        self.gas = field.gas
        self.std_temp = field.model.const("std-temperature")
        self.std_press = field.model.const("std-pressure")
        self.gas_dehydration_tbl = field.model.gas_dehydration_tbl
        self.mol_to_scf = field.model.const("mol-per-scf")
        self.air_elevation_const = field.model.const("air-elevation-corr")
        self.air_density_ratio = field.model.const("air-density-ratio")
        self.reflux_ratio = field.attr("reflux_ratio")
        self.regeneration_feed_temp = field.attr("regeneration_feed_temp")
        self.eta_reboiler_dehydrator = field.attr("eta_reboiler_dehydrator")
        self.air_cooler_delta_T = field.attr("air_cooler_delta_T")
        self.air_cooler_press_drop = field.attr("air_cooler_press_drop")
        self.air_cooler_fan_eff = field.attr("air_cooler_fan_eff")
        self.air_cooler_speed_reducer_eff = field.attr("air_cooler_speed_reducer_eff")
        self.water_press = field.water.density() * \
                           self.air_cooler_press_drop * \
                           field.model.const("gravitational-acceleration")

    def run(self, analysis):
        self.print_running_msg()

        # mass rate
        input = self.find_input_stream("gas")

        loss_rate = self.venting_fugitive_rate()
        gas_fugitives_temp = self.set_gas_fugitives(input, loss_rate)
        gas_fugitives = self.find_output_stream("gas fugitives")
        gas_fugitives.copy_flow_rates_from(gas_fugitives_temp)
        gas_fugitives.set_temperature_and_pressure(self.std_temp, self.std_press)

        # TODO: gas path will be added here
        gas_to_AGR = self.find_output_stream("gas for AGR")
        gas_to_AGR.copy_flow_rates_from(input)
        gas_to_AGR.subtract_gas_rates_from(gas_fugitives)

        feed_gas_press = input.pressure
        feed_gas_temp = input.temperature

        # how much moister in gas
        water_critical_temp = self.gas.component_Tc["H2O"]
        water_critical_press = self.gas.component_Pc["H2O"]
        tau = ureg.Quantity(1 - feed_gas_temp.to("kelvin").m / water_critical_temp.to("kelvin").m, "dimensionless")
        Tc_over_T = ureg.Quantity(water_critical_temp.to("kelvin").m / feed_gas_temp.to("kelvin").m, "dimensionless")
        pseudo_pressure = self.pseudo_pressure(tau, Tc_over_T, water_critical_press)
        B = 10 ** (6.69449 - 3083.87 / (feed_gas_temp.m + 459.67))
        water_content = 47430 * pseudo_pressure.m / feed_gas_press.to("Pa").m + B
        water_content = ureg.Quantity(water_content, "lb/mmscf")

        gas_volume_rate = self.gas.volume_flow_rate_STP(input)
        gas_multiplier = gas_volume_rate.to("mmscf/day").m / 1.0897  # multiplier for gas load in correlation equation
        water_content_volume = water_content * gas_volume_rate / component_MW["H2O"] / self.mol_to_scf
        water_content_volume = water_content_volume / gas_multiplier

        x1 = feed_gas_press.to("psia").m
        x2 = feed_gas_temp.to("degF").m
        x3 = water_content_volume.to("mmscf/day").m
        x4 = self.reflux_ratio.m
        x5 = self.regeneration_feed_temp.to("degF").m
        corr_result_df = run_corr_eqns(x1, x2, x3, x4, x5, self.gas_dehydration_tbl)
        reboiler_heavy_duty = ureg.Quantity(max(0, corr_result_df["Reboiler"] * gas_multiplier), "kW")
        pump_duty = ureg.Quantity(max(0, corr_result_df["Pump"] * gas_multiplier), "kW")
        condensor_thermal_load = ureg.Quantity(max(0, corr_result_df["Condenser"] * gas_multiplier), "kW")
        water_output = ureg.Quantity(max(0, corr_result_df["Resid water"]), "lb/mmscf")

        reboiler_fuel_use = reboiler_heavy_duty * self.eta_reboiler_dehydrator
        blower_air_quantity = condensor_thermal_load / self.air_elevation_const / self.air_cooler_delta_T
        blower_CFM = blower_air_quantity / self.air_density_ratio
        blower_delivered_hp = blower_CFM * self.water_press / self.air_cooler_fan_eff
        blower_fan_motor_hp = blower_delivered_hp / self.air_cooler_speed_reducer_eff
        air_cooler_energy_consumption = self.get_energy_consumption("Electric_motor", blower_fan_motor_hp)

        # energy-use
        energy_use = self.energy
        energy_use.set_rate(EN_NATURAL_GAS, reboiler_fuel_use)
        energy_use.set_rate(EN_ELECTRICITY, air_cooler_energy_consumption)

        # emissions
        emissions = self.emissions
        energy_for_combustion = energy_use.data.drop("Electricity")
        combustion_emission = (energy_for_combustion * self.process_EF).sum()
        emissions.add_rate(EM_COMBUSTION, "CO2", combustion_emission)

        emissions.add_from_stream(EM_FUGITIVES, gas_fugitives)



    @staticmethod
    def pseudo_pressure(tau, Tc_over_T, critical_pressure):
        """

        :param Tc_over_T:
        :param tau:
        :param critical_pressure: water critical pressure (unit = "Pa")
        :return: (flaot) pseudo pressure (unit = "Pa")
        """

        a1 = -7.85951783
        a2 = 1.84408259
        a3 = -11.7866497
        a4 = 22.6807411
        a5 = -15.9618719
        a6 = 1.80122502

        tau = tau.m
        Tc_over_T = Tc_over_T.m
        critical_pressure = critical_pressure.m

        Pv_over_Pc = np.exp((a1 * tau +
                             a2 * tau ** 1.5 +
                             a3 * tau ** 3 +
                             a4 * tau ** 3.5 +
                             a5 * tau ** 4 +
                             a6 * tau ** 7.5) * Tc_over_T)
        result = Pv_over_Pc * critical_pressure
        return ureg.Quantity(result, "Pa")