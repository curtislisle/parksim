#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 12 10:30:12 2018

@author: clisle
"""


import pandas as pd
import simpy
import random 
from pprint import *
import pickle


RANDOM_SEED = 42
NEW_VISITOR_BATCHES = 200  # Total number of customers
VISITORS_PER_BATCH = 50
INTERVAL_BATCHES = 5.0  # Generate new customers roughly every x clicks
MIN_PATIENCE = 30  # Min. customer patience
MAX_PATIENCE = 60  # Max. customer patience
REPEAT_SAME_RIDE_TIME = 5
MAX_NUMBER_OF_RIDES = 15
LENGTH_OF_STAY = 10*60  # guests leave after 10 hours

attractions_weighted = []

customers = {}

customer_states = ['riding','transit','eating','shopping','leaving']




# extend the SimPy Resource to keep track of all events
class MonitoredResource(simpy.Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        
    def request(self, *args, **kwargs):
        self.data.append(('request',self._env.now, len(self.queue)))
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append(('release',self._env.now, len(self.queue)))
        return super().release(*args, **kwargs)



def initializeAttractionPicker(attractions):
    for a in attractions:
        for i in range(attracts[a]['desirability']):
            attractions_weighted.append(attracts[a]['name'])
    #print(len(attractions_weighted),attractions_weighted)
 
 
def pickNextAttractionName(name,attracts):
    global attractions_weighted
    global customers
    # try to find something we haven't been to, but after 10
    # tries, give up and go for a repeat attraction
    for i in range(10):
        picked = random.choice(attractions_weighted)
        if picked not in customers[name]['rides']:
            break
    #print('picking:',picked)
    return picked
            
def pickNextAttractionName_set(name,attracts):
    weighted_set = set(attractions_weighted)
    visited = set(customers[name]['rides'])
    choices = weighted_set - visited
    pprint(weighted_set)
    print('visited:')
    pprint(visited)
    pprint(choices)
    picked = random.choice(list(choices))
    #print('picking:',picked)
    return picked

# given an attraction record as an argument, request this ride and either wait
# or give up depending on the wait time in the atraction's queue

def takeNextRide(attraction):    
    pass
  

# the scaling of the Magic Kingdom map we are using has 8000 squared units / minute for walking
def calculateTravelToAttraction(person,attract):
    global REPEAT_SAME_RIDE_TIME
    distance =  (person['x']-attract['x'])**2 + (person['y']-attract['y'])**2
    # it always some time even to repeat the same ride
    return distance / 16000.0 + REPEAT_SAME_RIDE_TIME

# declare the visitor to the park.  We have added an __init__ method so that the customer can be assigned to a venue
# as an initial experiment so we if we can create an arbitrary number of rides 

def customer(env, name, attractions):
    done = False
    while not done:
        if name not in customers.keys():
            # first time
            customers[name] = {}
            customers[name]['name'] = name
            customers[name]['starttime'] = env.now
            customers[name]['rides'] = []
            customers[name]['traveltime'] = 0
            customers[name]['waittime']  = 0
            customers[name]['reneges'] = 0
            customers[name]['left'] = ''
            customers[name]['x'] = 585
            customers[name]['y'] = 926
    
        # pick the next attraction
        attract_name = pickNextAttractionName(name,attractions)
        attraction = attractions[attract_name]
        
        # travel to that attraction and wait until we arrive
        time_to_travel = calculateTravelToAttraction(customers[name],attraction)
        #print(name,'traveling to',attract_name, 'with time',time_to_travel)
        customers[name]['traveltime'] += time_to_travel
        yield env.timeout(time_to_travel)
        
        # now we have arrived at the selected attraction
        customers[name]['x'] = attraction['x']
        customers[name]['y'] = attraction['y']    
        arrive = env.now
        attraction['visitor_count'] += 1
        time_in_ride = attractions[attract_name]['timelength']
        # processing to get our patience this time and get in the line at the ride
        with attraction['resource'].request() as req:
            patience = random.uniform(MIN_PATIENCE, MAX_PATIENCE)
            # Wait for the ride or abort at the end of our patience
            results = yield req | env.timeout(patience)
            # calculate our wait time
            wait = env.now - arrive
            attraction['wait_times'].append(wait)
            customers[name]['waittime'] += wait
            if req in results:
                # we actually got on the ride, hooray! calculate the ride
                # time and make it a bit randomized, then wait through the ride
                time_in_ride_random = random.expovariate(1.0 / time_in_ride)
                yield env.timeout(time_in_ride_random)
                # record that we have been to this ride in our records
                customers[name]['rides'].append(attract_name)
                #print('%7.4f %s: Finished' % (env.now, name))
            else:
                # We reneged, the wait was too long
                attraction['reneged_count'] += 1
                customers[name]['reneges'] += 1
                
        # a customer decides they are done after max rides or enough hours
        done_rides = len(customers[name]['rides']) > MAX_NUMBER_OF_RIDES
        done_time = (env.now - customers[name]['starttime']) > LENGTH_OF_STAY
        done = done_rides or done_time
        customers[name]['left'] = 'rides' if done_rides else 'time'
        
      
    
def source(env, batches, number_per_batch, interval, attracts):
    """Source generates customers randomly.  They come in batches (like off a tram)"""
    for i in range(batches):
        for j in range(number_per_batch):
            index = i*j+j
            c = customer(env, 'Customer%06d' % index, attracts)
            #print('customer starting with:',rideToTry)
            env.process(c)
        #t = random.expovariate(1.0 / interval)
        # wait until the next batch arrives
        t = random.gauss(1.0 / interval, (1.0 / interval)/5.0 )
        yield env.timeout(t)
    

def printVisitorInformation():
    #for key in customers:
    #    pprint(customers[key])
    print('-----------------------') 
    rideCount = 0
    waitMin = 9e99
    waitMax = 0
    waitTotal = 0
    timeLeft = 0
    for cust in customers:
        waitTotal += customers[cust]['waittime']
        waitMax = max(waitMax,customers[cust]['waittime'])
        waitMin = min(waitMax,customers[cust]['waittime'])  
        rideCount +=  len(customers[cust]['rides'])
        timeLeft += (1 if customers[cust]['left'] == 'time' else 0)
    waitAvg = waitTotal / len(customers.keys())
    rideAvg = rideCount / len(customers.keys())
    print('Visitors rode',rideAvg,'Waiting - min,avg,max:',waitMin,waitAvg,waitMax)
    print(timeLeft,'of total',len(customers.keys()) ,'visitors left after max time')
    
    
def printAttractionInformation():
    print('-----------------------')    
    for attract in attracts.keys():
        if len(attracts[attract]['wait_times']) > 0:
            average_wait = sum(attracts[attract]['wait_times'])/float(len(attracts[attract]['wait_times']))
        else: 
            average_wait = 0.0
        print(attracts[attract]['name'],'had',attracts[attract]['visitor_count'],
              'visitors with average wait time of',average_wait,
              'and ',attracts[attract]['reneged_count'],' who gave up')


#---------------- main loop -------------------


attractList = pd.read_csv(open("config_park.csv","r"))


# Setup and start the simulation
print('Mini park with renege')
random.seed(RANDOM_SEED)
env = simpy.Environment()

attracts = {}
for index, row in attractList.iterrows():
    rowlist = row.tolist()
    thisname = rowlist[0]
    attracts[thisname] = {}
    attracts[thisname]['name'] = thisname
    attracts[thisname]['type'] = rowlist[2]
    attracts[thisname]['desirability'] = int(rowlist[3])
    attracts[thisname]['capacity'] = int(rowlist[4])
    attracts[thisname]['timelength'] = float(rowlist[5])
    attracts[thisname]['x'] = rowlist[6]
    attracts[thisname]['y'] = rowlist[7]
    #try:
    #    attracts[thisname]['resource'] = simpy.Resource(env, capacity=attracts[thisname]['capacity'])
    #except:
    #    print('something happened assigning this attraction:',attracts[thisname]['name'],attracts[thisname]['capacity'])
    attracts[thisname]['resource'] = MonitoredResource(env, capacity=attracts[thisname]['capacity'])
    attracts[thisname]['wait_times'] = []
    attracts[thisname]['visitor_count'] = 0
    attracts[thisname]['reneged_count'] = 0
    
#pprint(attracts)
initializeAttractionPicker(attracts)
#pprint(attractions_weighted)
    
# Start processes and run
env.process(source(env, NEW_VISITOR_BATCHES, VISITORS_PER_BATCH, INTERVAL_BATCHES, attracts))
env.run()

#pprint(attracts)

#for key in customers:
#    pprint(customers[key])
printVisitorInformation()
printAttractionInformation()

# make records object
records = {'attractions': attracts, 'guests':customers}
print('storing records of the day in the park')
pickle.dump( records, open( "parksim_records.p", "wb" ) )
