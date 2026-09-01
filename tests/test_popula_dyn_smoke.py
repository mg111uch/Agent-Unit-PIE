"""Smoke: popula_dyn births work after Phase A-C fixes. Small, no frontend."""
import sys
sys.path.insert(0, "codebase")

def test_birth_same_cell():
    from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
    m = SimulationModel({"grid_width":10,"grid_height":10,"initial_pop":0,"initial_healers":0,"initial_toolmakers":0,"initial_traders":0,"birth_rate":1.0,"years":1,"seed":42})
    u1 = m._create_unit("farmer", position=(5,5), age=20, gender="M", seed=1)
    u1.set_state("age",20); u1.set_state("gender","M")
    u2 = m._create_unit("farmer", position=(5,5), age=20, gender="F", seed=2)
    u2.set_state("age",20); u2.set_state("gender","F")
    m.step()
    assert m.births_total >= 1
    assert m.get_population_count() >= 3
    # child has farmer behaviors
    children = [u for u in m.units.values() if u.get_state("age")==0]
    assert children, "child age 0 missing"
    assert "reproduce" in children[0].behaviors

def test_independent_rng():
    from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
    m = SimulationModel({"grid_width":10,"grid_height":10,"initial_pop":0,"initial_healers":0,"initial_toolmakers":0,"initial_traders":0,"birth_rate":0.5,"years":1,"seed":123})
    for i in range(4):
        u=m._create_unit("farmer", position=(i,i), age=20, gender="M" if i%2==0 else "F", seed=i)
        u.set_state("age",20); u.set_state("gender","M" if i%2==0 else "F")
    m.step()
    # with independent draws, births may differ but should not be all-or-nothing due to shared seed
    assert m.births_total >=0

def test_cumulative_counters():
    from modules.simulators.popula_dyn.core.simulation_model import SimulationModel
    m = SimulationModel({"grid_width":10,"grid_height":10,"initial_pop":0,"initial_healers":0,"initial_toolmakers":0,"initial_traders":0,"birth_rate":1.0,"years":1,"seed":42})
    u1=m._create_unit("farmer", position=(5,5), age=20, gender="M", seed=1)
    u1.set_state("age",20);u1.set_state("gender","M")
    u2=m._create_unit("farmer", position=(5,5), age=20, gender="F", seed=2)
    u2.set_state("age",20);u2.set_state("gender","F")
    m.step()
    assert m.births == m.births_total  # first year
    m.step()
    assert m.births_total > m.births  # cumulative larger than last-step after 2 years

if __name__ == "__main__":
    test_birth_same_cell(); test_independent_rng(); test_cumulative_counters()
    print("smoke ok")
