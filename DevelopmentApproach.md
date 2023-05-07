# Enabling Faster Iterations

## Previous Learnings

When developing the algorithm the iteration cycle was not very rapid, this was mostly due to my laziness to build something to help. The workflow was:
- Make tweaks to the algorithm
- Validate those tweaks by just 'thinking about it' and some basic validation
- Then load onto the Omega device
- Go for a long drive

This meant that it took days to evaluate any changes made; this became the bottleneck for development of the dynamic sampling algorithm.

## Proposed Approach

By using the previously gathered data, in particular the earlier data that had a near-fixed sampling rate, to create a temporal simulation of the routes taken, using interpolation of location, heading, speed, and any other attribute that was captured to enable a development harness capable having the dynamic sampling algorithm deployed into it making arbitrary samples to the interpolated time-series.

### Details

The methods used to interact with the inertial systems of the Omega should be overloaded so the interface looks identical for both development harness and the production deployment.


### Discussion

#### **Question on time**

*Can we support faster than real-time simulation?*

If not, full simulations could take hours to process; smaller test articles could be generated as quicker simulations for testing particular behaviours. It would be sensible to have a 'warp factor' to warp the simulations perception of time and therefore reduce simulation run-time.

*How would this be done?*

The algorithm would have a minimum polling frequency equal to at least the maximal sample rate, potentially double the maximal sampling rate to roughly follow the Nyquist–Shannon sampling theorem. This will need to be tested to check whether internally sampling at this frequency does not adversely affect the energy consumption of the system.

Thus, given this minimum-internal-sampling-frequency, the various time-series could be computed at initialisation and with each successive call to the 'intertial function(s)' the next element/row/set in the array can be returned. Finally, removing any controls that limit the maximal sampling rate would then allow a speed-up only limited by the machine's processing capability.

*What needs to be done?*
- Gather historical data and create an interpolated dataset
- Create a function that pops and returns the next element in the interpolated test data
- Create switch to disable sampling time-constraint


