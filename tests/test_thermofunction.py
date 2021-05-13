import pytest
import pandas as pd
import pint
from opgee.processes.thermodynamics import Oil, Gas
from opgee.core import ureg
from opgee.stream import Stream

num_digits = 3

@pytest.fixture
def oil_instance():
    API = pint.Quantity(32.8, ureg["degAPI"])
    # gas_comp = pd.Series(data=dict(N2=2.0, CO2=6.0, C1=84.0, C2=4.0,
    #                                C3=2, C4=1, H2S=1))/100
    gas_comp = pd.Series(data=dict(N2=0.004, CO2=0.0, C1=0.966, C2=0.02,
                                   C3=0.01, C4=0.0, H2S=0))
    gas_oil_ratio = 2429.30
    res_temp = ureg.Quantity(200, "degF")
    res_press = ureg.Quantity(1556.6, "psi")
    oil = Oil(API, gas_comp, gas_oil_ratio, res_temp, res_press)

    return oil

def test_gas_specific_gravity(oil_instance):
    gas_SG = oil_instance.gas_specific_gravity()

    # stream = Stream("test_stream",temperature=200.0, pressure=1556.0)
    # bubble_p = oil_instance.bubble_point_pressure()
    assert round(gas_SG, num_digits) == pytest.approx(0.581)

def test_bubble_point_solution_GOR(oil_instance):
    gor_bubble = oil_instance.bubble_point_solution_GOR()
    assert round(gor_bubble, num_digits) == pytest.approx(2822.361)

def test_reservoir_solution_GOR(oil_instance):
    res_GOR = oil_instance.reservoir_solution_GOR()
    assert round(res_GOR, num_digits) == pytest.approx(286.983)

def test_bubble_point_pressure(oil_instance):
    p_bubblepoint = oil_instance.bubble_point_pressure()
    assert round(p_bubblepoint) == pytest.approx(9337)

def test_bubble_point_formation_volume_factor(oil_instance):
    bubble_oil_FVF = oil_instance.bubble_point_formation_volume_factor()
    assert round(bubble_oil_FVF, num_digits) == pytest.approx(1.194)

def test_solution_gas_oil_ratio(oil_instance):
    stream = Stream("test_stream",temperature=200.0, pressure=1556.0)
    solution_gor = oil_instance.solution_gas_oil_ratio(stream)
    assert round(solution_gor, 1) == pytest.approx(286.8)

def test_saturated_formation_volume_factor(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    sat_fvf = oil_instance.saturated_formation_volume_factor(stream)
    assert round(sat_fvf, num_digits) == pytest.approx(1.194)

def test_unsat_formation_volume_factor(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    unsat_fvf = oil_instance.unsat_formation_volume_factor(stream)
    assert round(unsat_fvf, num_digits) == pytest.approx(1.223)

def test_isothermal_compressibility_X(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    iso_compress_x = oil_instance.isothermal_compressibility_X(stream)
    assert round(iso_compress_x, num_digits) == pytest.approx(-0.032)

def test_isothermal_compressibility(oil_instance):
    iso_compress = oil_instance.isothermal_compressibility()
    assert round(iso_compress, num_digits) == pytest.approx(3.05e-6)

def test_formation_volume_factor(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    fvf = oil_instance.formation_volume_factor(stream)
    assert round(fvf, num_digits) == pytest.approx(1.194)

def test_density(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    density = oil_instance.density(stream)
    assert round(density.m, num_digits) == pytest.approx(46.919)

def test_mass_energy_density(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    mass_energy_density = oil_instance.mass_energy_density()
    assert round(mass_energy_density.m, num_digits) == pytest.approx(18279.816)

def test_volume_energy_density(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    volume_energy_density = oil_instance.volume_energy_density(stream)
    assert round(volume_energy_density.m, num_digits) == pytest.approx(4.815)

def test_energy_flow_rate(oil_instance):
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    stream.set_flow_rate("C10", "liquid", 273.7766 / 2)
    stream.set_flow_rate("C9", "liquid", 273.7766 / 2)
    energy_flow_rate = oil_instance.energy_flow_rate(stream)
    assert round(energy_flow_rate.m, num_digits) == pytest.approx(11030.107)

@pytest.fixture
def gas_instance():
    res_temp = ureg.Quantity(200, "degF")
    res_press = ureg.Quantity(1556.6, "psi")
    gas = Gas(res_temp, res_press)
    return gas

def test_stream():
    stream = Stream("test_stream", temperature=200.0, pressure=1556.0)
    stream.set_flow_rate("N2", "gas", 4.90497)
    stream.set_flow_rate("CO2", "gas", 0.889247)
    stream.set_flow_rate("C1", "gas", 87.58050)
    stream.set_flow_rate("C2", "gas", 9.75715)
    stream.set_flow_rate("C3", "gas", 4.37353)
    stream.set_flow_rate("C4", "gas", 2.52654)
    stream.set_flow_rate("H2S", "gas", 0.02086)
    return stream

def test_total_molar_flow_rate(gas_instance):
    stream = test_stream()
    total_molar_flow_rate = gas_instance.total_molar_flow_rate(stream)
    assert round(total_molar_flow_rate.m, num_digits) == pytest.approx(6122900.860)

def test_component_molar_fraction(gas_instance):
    stream = test_stream()
    component_molar_fraction = gas_instance.component_molar_fraction("N2", stream)
    assert round(component_molar_fraction, ndigits=4) == pytest.approx(0.0286)

def test_component_molar_fraction(gas_instance):
    stream = test_stream()
    component_molar_fraction = gas_instance.component_molar_fraction("C1", stream)
    assert round(component_molar_fraction, ndigits=4) == pytest.approx(0.8917)

def test_specific_gravity(gas_instance):
    stream = test_stream()
    specific_gravity = gas_instance.specific_gravity(stream)
    assert round(specific_gravity.m, ndigits=4) == pytest.approx(0.6277)

def test_ratio_of_specific_heat(gas_instance):
    stream = test_stream()
    ratio_of_specific_heat = gas_instance.ratio_of_specific_heat(stream)
    assert round(ratio_of_specific_heat, num_digits) == pytest.approx(1.286)

def test_uncorrelated_pseudocritical_temperature_and_pressure(gas_instance):
    stream = test_stream()
    pseudocritical_temp = gas_instance.uncorrelated_pseudocritical_temperature_and_pressure(stream)["temperature"]
    # pseudocritical_press = gas_instance.uncorrelated_pseudocritical_temperature_and_pressure(stream)["pressure"]
    assert round(pseudocritical_temp.m, ndigits=0) == pytest.approx(361)

def test_uncorrelated_pseudocritical_temperature_and_pressure(gas_instance):
    stream = test_stream()
    # pseudocritical_temp = gas_instance.uncorrelated_pseudocritical_temperature_and_pressure(stream)["temperature"]
    pseudocritical_press = gas_instance.uncorrelated_pseudocritical_temperature_and_pressure(stream)["pressure"]
    assert round(pseudocritical_press.m, ndigits=0) == pytest.approx(670)

def test_correlated_pseudocritical_temperature(gas_instance):
    stream = test_stream()
    corr_pseudocritical_temp = gas_instance.correlated_pseudocritical_temperature(stream)
    assert round(corr_pseudocritical_temp.m, num_digits) == pytest.approx(360.924)

def test_correlated_pseudocritical_pressure(gas_instance):
    stream = test_stream()
    corr_pseudocritical_press = gas_instance.correlated_pseudocritical_pressure(stream)
    assert round(corr_pseudocritical_press.m, num_digits) == pytest.approx(668.4)

def test_reduced_temperature(gas_instance):
    stream = test_stream()
    reduced_temperature = gas_instance.reduced_temperature(stream)
    assert round(reduced_temperature.m, num_digits) == pytest.approx(1.828)

def test_reduced_pressure(gas_instance):
    stream = test_stream()
    reduced_press = gas_instance.reduced_pressure(stream)
    assert round(reduced_press.m, num_digits) == pytest.approx(2.329)

def test_Z_factor(gas_instance):
    stream = test_stream()
    z_factor = gas_instance.Z_factor(stream)
    assert round(z_factor, num_digits) == pytest.approx(0.913)

def test_volume_factor(gas_instance):
    stream = test_stream()
    vol_factor = gas_instance.volume_factor(stream)
    assert round(vol_factor, num_digits) == pytest.approx(0.01094)
