import itertools
import random
import simpy

from logger import arrival_logger, dock_logger
from objects.fuel_barge import FuelBarge
from objects.priority_filter_store import MyPriorityFilterStore
from objects.ship import Ship, SpecialShip
from objects.tug import Tug
from system_monitor import SystemMonitor

# -------------------------
# SIMPY CONFIGURATION
# -------------------------
SHIP_ARRIVAL_MEAN = 0.2
SHIP_ARRIVAL_LAMBDA = 1 / SHIP_ARRIVAL_MEAN

N_TUGS = 8
N_DOCKS = 20
N_FUEL_BARGES = 8

BUNKERING_TIME_MEAN = 2
BUNKERING_TIME_STD = 0.25

CARGO_TIME_MEAN = 4
CARGO_TIME_STD = 0.50

SIM_TIME = 120 # (hours in real world)


def init_harbour(
    env, 
    tugs: MyPriorityFilterStore, 
    fuel_barges: simpy.Store, 
    monitor: SystemMonitor):
    """Initializes <simpy.Store> resources, inserting related objects.
    
    :param <env>: simulation (simpy) environment
    :param <tugs>: MyPriorityFilterStore resource instance
    :param <fuel_barges>: simpy Store resource instance
    :param <monitor>: SystemMonitor class instance
    """

    # Spawn tugs
    for id in range(N_TUGS):
        t = Tug(env, id, tugs, monitor)
        yield tugs.put(t)

    # Spawn fuel barges
    for id in range(N_FUEL_BARGES):
        b = FuelBarge(env, id)
        yield fuel_barges.put(b)

def ship_arrival(
    env: simpy.Environment, 
    docks: simpy.PriorityResource, 
    tugs: MyPriorityFilterStore, 
    fuel_barges: simpy.Store):
    """Simulates periodic ship arrival with an exponential distribution.
    
    :param <env>: simulation (simpy) environment
    :param <docks>: simpy PriorityResource instance
    :param <tugs>: MyPriorityFilterStore resource instance
    :param <fuel_barges>: simpy Store resource instance
    """

    # Periodically simulate arrival of new ships
    for i in itertools.count():
        next_ship = random.expovariate(SHIP_ARRIVAL_LAMBDA)
        yield env.timeout(next_ship)

        s : Ship

        # 20% of ships will be of higher priority (special ships)
        if random.randint(1, 10) > 2:
            s = Ship(i)
            arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} arrived!')
        else:
            s = SpecialShip(i)
            arrival_logger.info(f'[{env.now:.3f}]: Special ship {s.id} arrived!')
        
        am.new_ship(s.priority)

        # Start ship docking process
        env.process(ship_docking(env, s, docks, tugs, fuel_barges))


def ship_docking(
    env: simpy.Environment,
    s: Ship, 
    docks: simpy.PriorityResource, 
    tugs: MyPriorityFilterStore, 
    fuel_barges: simpy.Store):
    """Simulates docking of a ship performed by a tug with a gaussian distribution.
    
    :param <env>: simulation (simpy) environment
    :param <s>: Ship class instance
    :param <docks>: simpy PriorityResource instance
    :param <tugs>: MyPriorityFilterStore resource instance
    :param <fuel_barges>: simpy Store resource instance
    """

    # Request a dock
    start = env.now
    dock = docks.request(priority=s.priority, preempt=False)
    yield dock
    arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} obtained dock.')

    # Request a tug
    tug = yield tugs.get(priority=s.priority)
    am.add_to_entrance_queue(env.now - start)
    arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} obtained tug {tug.id}.')

    # Simulate docking
    am.start_docking(s.priority)
    arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} starts docking.')
    yield  env.process(tug.transport())

    # Docking completed
    am.docking_completed()
    arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} completed docking.')
    yield tugs.put(tug)

    # Start ship at dock process
    env.process(ship_at_dock(env, s, docks, dock, fuel_barges))


def ship_at_dock(
    env: simpy.Environment, 
    s: Ship,
    docks: simpy.PriorityResource,
    dock,
    fuel_barges: simpy.Store):
    """Simulates docking of a ship performed by a tug with a gaussian distribution.
    
    :param <env>: simulation (simpy) environment
    :param <s>: Ship class instance
    :param <docks>: simpy PriorityResource instance
    :param <dock>: resource obtained by a get request on a PriorityResource
    :param <fuel_barges>: simpy Store resource instance
    """

    # Wait on ship unload and ship bunkering processes
    yield env.process(
        ship_cargo(env, s)) & env.process(ship_bunkering(env, s, fuel_barges))

    # Start exiting harbour

    # Request a tug
    start = env.now
    tug = yield tugs.get(priority=s.priority-1)
    am.add_to_exit_queue(env.now - start)
    am.tug_locked()

    am.ship_supplied()
    docks.release(dock)

    # Simulate un-docking
    yield env.process(tug.transport())

    # Ship exited
    yield tugs.put(tug)
    am.tug_released()
    am.ship_exited()
    arrival_logger.info(f'[{env.now:.3f}]: Ship {s.id} exited.')


def ship_cargo(env: simpy.Environment, s: Ship):
    """Simulates cargo loading/unloading with a gaussian distribution.
    
    :param <env>: simulation (simpy) environment
    :param <s>: Ship class instance
    """

    # Simulate loading/unloading
    dock_logger.info(f'[{env.now:.3f}]: Ship {s.id} starts unloading.')
    yield env.timeout(abs(random.gauss(CARGO_TIME_MEAN, CARGO_TIME_STD)))
    dock_logger.info(f'[{env.now:.3f}]: Ship {s.id} completed unloading.')


def ship_bunkering(env: simpy.Environment, s: Ship, fuel_barges: simpy.Store):
    """Simulates ship bunkering performed by a fuel barge with a gaussian distribution. A barge is not released until ship bunkering completed.
    
    :param <env>: simulation (simpy) environment
    :param <s>: Ship class instance
    :param <fuel_barges>: simpy Store resource instance
    """

    supplied: bool = False

    # Request a barge
    start = env.now
    barge = yield fuel_barges.get()
    am.add_to_bunkering_queue(env.now - start)

    # Start bunkering
    am.start_bunkering()
    while not supplied:

        dock_logger.info(f'[{env.now:.3f}]: Ship {s.id} with fuel {s.fuel_capacity:.0f}:{s.fuel_level:.0f} bunkering from barge {barge.id} with level {barge.fuel_tank.level:.0f}.')

        fuel_missing = s.fuel_capacity - s.fuel_level

        # Barge full, level not enough -> take all and barge refuel
        if barge.fuel_tank.level == barge.fuel_capacity and barge.fuel_tank.level < fuel_missing:
            yield barge.fuel_tank.get(barge.fuel_capacity)
            yield env.timeout(
                abs(random.gauss(BUNKERING_TIME_MEAN, BUNKERING_TIME_STD)))
            s.fuel_level += barge.fuel_capacity
            yield env.process(barge.barge_refuel())

        # Barge level is enough -> take needed and release    
        elif barge.fuel_tank.level >= fuel_missing: 
            yield barge.fuel_tank.get(fuel_missing)
            yield env.timeout(
                abs(random.gauss(BUNKERING_TIME_MEAN, BUNKERING_TIME_STD)))
            s.fuel_level += fuel_missing
            supplied = True
            barge.check_fuel_tank()

        # Barge level not full and not enough -> take all and barge refuel
        else:
            s.fuel_level += barge.fuel_tank.level
            yield barge.fuel_tank.get(barge.fuel_tank.level)
            yield env.process(barge.barge_refuel())

    # Bunkering completed
    dock_logger.info(f'[{env.now:.3f}]: Ship {s.id} supplied.')
    yield fuel_barges.put(barge)
    am.bunkering_completed()


if __name__ == '__main__':

    am = SystemMonitor()
    env = simpy.Environment()
    am.init(env, N_DOCKS, N_TUGS, N_FUEL_BARGES)

    # Resources
    tugs = MyPriorityFilterStore(env, capacity=N_TUGS)
    docks = simpy.PriorityResource(env, capacity=N_DOCKS)
    fuel_barges = simpy.Store(env, capacity=N_FUEL_BARGES)

    # Simulation
    env.process(init_harbour(env, tugs, fuel_barges, am))
    env.process(ship_arrival(env, docks, tugs, fuel_barges))
    env.run(until=SIM_TIME)

    # Plot results
    am.plot_arrivals()
    am.plot_dockings()
    am.store_queues_times()
