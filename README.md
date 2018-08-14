# parksim
Amusement Park simulator using SimPy

This is a simple amusement park simulator to generate synthetic data for park visit experiences.  It uses Python's SimPy discrete event simulation package to manage simulation time. This is currently very simplistic and I invite others to add capability, turn it into a package, and extend for your own park modeling needs.  

Rudimentary records are kept and stored in a pickled object at the end of the run to facilitate some post-run analytics. Each visitor keeps tracks of the rides they experience.  The rides keep track of all the wait-times experienced by visitors.  

The park configuration file (config_park.csv) is a simple format with one line per venue.  A few venue types are listed to allow for differentiated experiences according to the venue type (ride, restaurant, etc.) eventually, but no such behavior is currently implemented.  The locations of each venue are derived from the pixel locations in the included park image.  There is a hard-coded scaling factor currently used to make travel time somewhat reflect actual travel times, for this particular source image size. 

**Execution**
- Run the simulator by simply executing it as a script 'python3 parksim.py'
- It will create a parksim_records.p pickle object for post-processing the simulation

**To Do**
- improve the ride choice algorithm to include locality
- Add a time-specific wave of visitors, instead of a steady flow (use distributions from the python random package)
- Refactor routines so parksim can be included as a module in user programs / notebooks. 
