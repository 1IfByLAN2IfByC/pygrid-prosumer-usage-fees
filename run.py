# make the code as Python 3 compatible as possible
import pypsa
import plotly as py
import numpy as np
import pandas as pd
from numpy.random import rand
import time
# define an interpolation function that will let you define a profile
# in hours and interpolate to an arbitray time discritization
def interpolate(series, td):
    tmp = pd.Series(np.zeros((len(td))), index = td)
    tmp = tmp.add(series)
    return tmp.interpolate(method='time')


# make fake pseudorandom hourly loads
hrs = pd.date_range("00:00", "23:30", freq="60min")
t = pd.date_range("00:00", "23:59", freq="5min")

      #0,1,2,3,4,5,6,7,8,9,10,11,12,1 ,2 ,3 ,4 ,5,6,7,8,9,10,11
base= [3,3,3,3,3,6,7,7,8,8,9 ,9 ,10,10,10,10,10,9,9,7,6,5, 4,3]
sunshine = [0,0,0,0,0,0,0,0,0,1,1,2,2,3,3,2,1,0,0,0,0,0,0,0]
sunshine = [i / max(sunshine) for i in sunshine]
profile = lambda base: base + np.var(base)*rand(len(base))
percentCloudy = .05
N_homes = 6 # make sure is even

N_iters = 32
colHeaders = ['Aggregate Demand','Demand (w/solar)',
            'Demand (w/out solar)', 'Home Generation',
            'Gen 1', 'Gen 2', 'Gen 3']

savedOutput = pd.Panel(np.zeros((N_iters, len(t), \
                len(colHeaders))))

savedOutput.minor_axis = colHeaders
for day in xrange(N_iters):
    # setup the grid
    network = pypsa.Network()
    network.set_snapshots(t)

    #add buses
    # we will make nice little california houses all made of ticky tacky
    itr = 0

    # randomly select some houses to get a solar panel
    N_panels = 15
    getPanel = np.random.choice(np.arange(N_homes**2), N_panels)


    # randomly select some of the above to get storage
    N_storage = int(N_panels / 3)
    getStorage = np.random.choice(getPanel, N_storage)
    # do a random draw to see if its cloudy
    cloudy = (0 if rand()< percentCloudy else 1)
    print(cloudy)
    for i in range(N_homes):
        for j in range(N_homes):

            # to make the timeframe of the loads arbitrary, we will
            # create an iterpolant for the loads and sunshine
            loads = pd.Series(profile(base), hrs)
            solar = pd.Series(profile(sunshine), hrs)

            network.add("Bus","Home {}".format(itr),
                       x = (i - N_homes/2),
                       y = (j-N_homes/2))

            # add the loads
            network.add("Load", "{}".format(itr),
                       bus="Home {}".format(itr),
                        p_set = interpolate(loads, t)
                       )

            # add solar panel if chosen
            if itr in getPanel:
                network.add("Generator", "Home Panel {}".format(itr),
                       bus="Home {}".format(itr),
                        p_nom = 15,
                        dispatch='variable',
                        p_max_pu = interpolate(solar, t),
                        p_min_pu = pd.Series(np.zeros((len(t))), t)
                           )

            if itr in getStorage:
                network.add("StorageUnit", "Storage Cell {}".format(itr),
                           bus="Home {}".format(itr),
                           p_nom = 5,
                           standing_loss = .01
                           )


            itr +=1



    # add the bus to for the generation plant
    network.add("Bus", "Gen Bus 1",
            x = 10,
            y = 10
            )

    network.add("Bus", "Gen Bus 2",
            x = 1,
            y = 10
            )

    # this will the the big nasty coal plant
    network.add("Generator", "Gen1",
        bus="Gen Bus 1",
        p_nom = 400
        ,p_nom_max_pu_fixed = .9
        ,p_nom_min_pu_fixed = .6
        ,marginal_cost = 1.0
        )

    # natural gas
    network.add("Generator", "Gen2",
        bus="Gen Bus 2",
        control='Slack',
        dispatch='variable',
        p_max_pu = pd.Series(np.ones((len(t))), t),
        p_min_pu = pd.Series(np.zeros((len(t))), t)
        ,p_nom = 250
        ,marginal_cost = 1.2

                )

    # connect all the houses in a column
    itr = 0
    for i in range(N_homes):
        for j in range(N_homes):
            if itr%N_homes != 0 :
                network.add("Line", "Home Line ({i}, {j})".\
                        format(i=i, j=j),
                       bus0="Home {}".format(itr),
                       bus1="Home {}".format(itr-1),
                       x=80,
                       s_nom=300)

            if j == N_homes-1:
                # add connection to generator
                network.add("Line", "Gen Line 1, {}".\
                        format(i),
                       bus0="Home {}".format(itr),
                       bus1="Gen Bus 1",
                       x=.0001,
                       s_nom=1000)

                network.add("Line", "Gen Line 2, {}".\
                    format(i),
                   bus0="Home {}".format(itr),
                   bus1="Gen Bus 2",
                   x=.0001,
                   s_nom=1000)
            itr +=1

    # make a second subdivision
    itr = N_homes**2
    for i in range(N_homes):
        for j in range(N_homes):

            # to make the timeframe of the loads arbitrary, we will
            # create an iterpolant for the loads and sunshine
            loads = pd.Series(profile(base), hrs)
            solar = pd.Series(profile(sunshine), hrs)

            network.add("Bus","Home {}".format(itr),
                       x = (i - N_homes/2),
                       y = (j-N_homes/2)+20
                        )

            # add the loads
            network.add("Load", "{}".format(itr),
                       bus="Home {}".format(itr),
                        p_set = interpolate(loads, t)
                       )

            itr +=1



    # add a bus at the same location as the first generator bus
    network.add("Bus", "Gen Bus 3",
               x = 10,
               y = 10)

    # add second generator at the first bus
    network.add("Generator", "Gen 3",
               bus="Gen Bus 3",
               p_nom = 600,
               p_nom_max_pu_fixed = .9,
               p_nom_min_pu_fixed = .6,
               marginal_cost = 1.0
               )


    # connect all the houses in a column
    itr = N_homes**2
    for i in range(N_homes):
        for j in range(N_homes):
            if itr%N_homes != 0 :
                network.add("Line", "Home Line ({i}, {j})".\
                        format(i=i+ N_homes**2 , j=j+N_homes**2 ),
                       bus0="Home {}".format(itr),
                       bus1="Home {}".format(itr-1),
                       x=80,
                       s_nom=300)

            if j == 0:
                # add connection to generator
                network.add("Line", "Gen Line 3, {}".\
                        format(i),
                       bus0="Home {}".format(itr),
                       bus1="Gen Bus 3",
                       x=.0001,
                       s_nom=1000)

            itr +=1


    #Do a linear OPF
    network.lopf(t)

    # save the info we are interested in
    aggDemand = network.loads_t.ix['p'].sum(axis=1)
    solarDemand = network.loads_t.ix['p',:,:N_homes**2].sum(axis=1)
    noSolarDemand = network.loads_t.ix['p',:,N_homes**2:].sum(axis=1)
    homeGen = network.generators_t.ix['p',:, :-3].sum(axis=1)
    publicGen = network.generators_t.ix['p', :, -3:]
    macros =pd.concat([aggDemand, solarDemand, noSolarDemand, homeGen, publicGen], axis=1)
    macros.columns = ['Aggregate Demand','Demand (w/solar)', 'Demand (w/out solar)',
                      'Home Generation', 'Gen 1', 'Gen 2', 'Gen 3']

    # save that data to pandas Panel
    # (i know lots of overhead but its already written :))
    if day == 0:
        savedOutput.major_axis = macros.index
    savedOutput.ix[day, :,:] = macros

    print(day)
savedOutput.to_pickle('output.pkl')
