#!/usr/bin/env python3

import requests
import json
from pprint import pprint

api_key = "api_key=ENTER_YOUR_API_KEY"
base_url = "https://api-v3.mbta.com"
route_types_filter = "0,1"

all_routes = {}
all_stops = {}

class Stop:
  def __init__(self, idx=None, name=None, parent_station=None, routes=[], is_connecting=False):
      self.idx = idx
      self.name = name
      self.parent_station = parent_station
      self.routes = routes
      self.is_connecting = is_connecting

  def __repr__(self):
       return ", ".join((
               "idx=" + str(self.idx),
               "name=" + str(self.name),
               "parent_station=" + str(self.parent_station),
               "routes=" + str(self.routes)))

  def is_on_route(self, route_idx):
    for route in self.routes:
      if (route_idx) == route.idx:
        return True

    return False
 
class Route:
  def __init__(self):
      self.idx = None
      self.name = None
      self.stops = None

  def __init__(self, idx=None, name=None, stops=[], num_stops=None):
      self.idx = idx
      self.name = name
      self.stops = stops
      self.num_stops = num_stops

  def __repr__(self):
       return ", ".join((
                 "idx=" + str(self.idx),
                 "name=" + str(self.name),
                 "stops=" + str(self.stops),
                 "num_stops=" + str(self.num_stops)))
 
  def has_stop(self, idx, station):
    for stop_id in self.stops:
      if (stop_id == idx or stop_id == station):
        return True
  
    return False

def get_stop_by_name(name):
  for stop_id, stop in all_stops.items():
    if stop.name == name:
      return stop

  return None

def get_routes_by_stop(stop_id):
  for route_id, route in all_routes.items():
    if route.has_stop(stop_id, stop_id):
      return stop.routes

  return None

#
# Boston's transportation system, the MBTA (https://mbta.com/), has a website with APIs
# https://api-v3.mbta.com/docs/swagger/index.html.
#
# You will not need an API key, but you might get rate-limited without one.
#
# The MBTA's documentation https://api-v3.mbta.com/docs/swagger/index.html is written using
# OpenAPI/Swagger. If you haven't used Swagger before, this tutorial walks through the basics on an
# example project: https://idratherbewriting.com/learnapidoc/pubapis_swagger.html
# The MBTA developer site recommends tools for generating code from their documentation. We
# advise you not to use these tools because they are heavyweight and unnecessary. Writing your own
# client code to interact directly with the APIs is most likely easier, and better demonstrates the
# skills we're interested in reviewing.
#

#####################################################################################################
# Question 1
#
# Write a program that retrieves data representing all, what we'll call "subway" routes: "Light Rail"
# (type 0) and “Heavy Rail” (type 1). The program should list their “long names” on the console.
# Partial example of long name output: Red Line, Blue Line, Orange Line...
#
# There are two ways to filter results for subway-only routes. Think about the two options below
# and choose:
#
# 1. Download all results from https://api-v3.mbta.com/routes then filter locally
# 2. Rely on the server API (i.e., https://api-v3.mbta.com/routes?filter[type]=0,1) to
#    filter before results are received.
#
# Please document your decision and your reasons for it.
#

routes_stops_dict = {}

def gather_all_route_ids():

  url = (f"{base_url}/routes?filter[type]=0,1"
         f"&fields[route]=long_name"
         f"&include=stop,line")

  r = requests.get(url)
  j = r.json()

  route_ids = []
  for e in j["data"]:
    all_routes[e["id"]] = Route(idx=e["id"],
            name=e["attributes"]["long_name"])

  for route_idx in all_routes.keys():
    url = f"{base_url}/stops?filter[route]={route_idx}"
    r = requests.get(url)
    j = r.json()

    # FIXME: Why must we clear stops here?
    all_routes[route_idx].stops = []

    for stop in j["data"]:
      all_routes[route_idx].stops.append(stop["id"])

    all_routes[route_idx].num_stops = len(j["data"])

gather_all_route_ids()

def get_routes_with_max_and_min_stops():

  # Display min and max of stop count across routes
  max_stops = 0
  min_stops = 2**32
  for route_id, route in all_routes.items():
    if route.num_stops > max_stops:
      max_stops_route = route.name
      max_stops = route.num_stops
    if route.num_stops < min_stops:
      min_stops_route = route.name
      min_stops = route.num_stops

  print("Route %s has the fewest stops with %d stops." % (min_stops_route, min_stops))
  print("Route %s has the most stops with %d stops." %   (max_stops_route, max_stops))

#####################################################################
print("\n\n" + ("#" * 70))
print("Question 1: \n")
#####################################################################

get_routes_with_max_and_min_stops()

#####################################################################################################
# Question 2
#
# Extend your program so it displays the following additional information.
#
# 1. The name of the subway route with the most stops as well as a count of its stops.
# 2. The name of the subway route with the fewest stops as well as a count of its stops.
# 3. A list of the stops that connect two or more subway routes along with the relevant route
#    names for each of those stops.
#

def get_stop_routes(stop_idx, parent_station):
  ret = set()
  for route_id, route in all_routes.items():
    if (route.has_stop(stop_idx, parent_station)):
      ret.add(route_id)
    
  return list(ret)


# Build lookup tables of routes and stops by id => name

def find_stop_name(name):
  for stop in all_stops.values():
    if name == stop.name:
      return True

  return False
     

def get_all_stops():
  url = (f"{base_url}/stops?"
         f"&{api_key}"
         f"&fields[stops]=short_name,parent_station"
         f"&filter[route_type]=0,1")

  r = requests.get(url)
  j = r.json()

  for e in j["data"]:

    stop_idx = e["id"]
    stop_name = e["attributes"]["name"]
    parent_station_id = e["relationships"]["parent_station"]["data"]["id"]

    if stop_idx not in all_stops and not find_stop_name(stop_name):
      all_stops[stop_idx] = Stop(
        idx = stop_idx,
        name = stop_name,
        parent_station = parent_station_id,
        routes = get_stop_routes(stop_idx, parent_station_id)
      )

# FIXME: This could do the two-tiered if-statement to find the stop name
# checking stop name and parent_station name
def get_stop_name(identifier):
  url = (f"{base_url}/stops/"
         f"{identifier}/"
         f"&fields[stops]=short_name")

get_all_stops()

connecting_stops = {}

def find_connecting_stops():
  """
  Gather all stops, which fall on two routes

  """

  # FIXME: Only considers Green line (should also include Red, Orange, Blue),
  #       because stops such as "Park Street", which are on two routes (of
  #       different color), are only listed as being on Green Line routes.
  print("\nStops connecting two or more subway routes:\n")
  for stop_id, stop in all_stops.items():
    if len(stop.routes) > 1:
      connecting_stops[stop_id] = stop
      print("\tStop: %s, Routes: %s" %
            (stop.name, ", ".join(stop.routes)))

#####################################################################
print("\n\n" + ("#" * 70))
print("Question 2: \n")
#####################################################################

find_connecting_stops()

#####################################################################################################
# Question 3
#
# Extend your program again such that the user can provide any two stops on the subway routes
# you listed for question 1.
#
# List a rail route you could travel to get from one stop to the other. We will not evaluate your
# solution based upon the efficiency or cleverness of your route-finding solution. Pick a simple
# solution that answers the question. We will want you to understand and be able to explain how
# your algorithm performs.
#
# Examples:
# 1. Davis to Kendall -> Redline
# 2. Ashmont to Arlington -> Redline, Greenline
#
# Hint: It might be tempting to hardcode things in your algorithm that are specific to the MBTA
# system, but we believe it will make things easier for you to generalize your solution so that it
# could work for different and/or larger subway systems.
#
# How you handle input, represent train routes, and present output is your choice.


# In the list of stops, find intersections of routes.
def get_route(stop_a_name, stop_b_name):

  # Get route of stop-A
  stop_a = get_stop_by_name(stop_a_name)
  stop_b = get_stop_by_name(stop_b_name)
  stop_a_routes = set(stop_a.routes)
  stop_b_routes = set(stop_b.routes)
  hops = []
  intersection = stop_a_routes.intersection(stop_b_routes)

  if len(intersection):
    hops.append(list(intersection)[0])
  else:
    hops.append(list(stop_a_routes)[0])
    for cs in connecting_stops:
      stop = all_stops[cs]

      intersection_a = stop_a_routes.intersection(stop.routes)
      intersection_b = stop_b_routes.intersection(stop.routes)

      if len(intersection_a) and len(intersection_b):
        hops.append(list(intersection_b)[0])

  print("To get from '%s' to '%s', take these routes: %s" % 
        (stop_a_name, stop_b_name, hops))

  return hops

#####################################################################
print("\n\n" + ("#" * 70))
print("Question 3: \n")
#####################################################################

get_route("Davis", "Kendall/MIT")
get_route("Ashmont", "Arlington")
get_route("Aquarium", "Chinatown")
get_route("Riverway", "Beachmont")
get_route("Riverway", "Beachmont")
get_route("Wellington", "Braintree")

# TODO: Expected: BlueLine, GreenLine, RedLine
# get_route("Airport", "Harvard")


