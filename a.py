#!/usr/bin/env python3

import requests
import json
from pprint import pprint

api_key = "api_key=d2e03097f9c24dcfa494d95f9f3c3b81"
base_url = "https://api-v3.mbta.com"
route_types_filter = "0,1"


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


url = (f"{base_url}/routes?filter[type]=0,1"
       f"&fields[route]=long_name"
       f"&include=stop")

r = requests.get(url)

route_ids = []
for e in r.json()["data"]:
  route_ids.append(e["id"])

routes_stops_dict = {}
for route_id in route_ids:
  url = f"{base_url}/stops?filter[route]={route_id}"
  r = requests.get(url)
  num_stops = len(r.json()["data"])
  routes_stops_dict[route_id] = num_stops

# Display min and max of stop count across routes
max_stops = max(routes_stops_dict.values())
min_stops = min(routes_stops_dict.values())
for route, stops in routes_stops_dict.items():
  if stops == max_stops:
    print("Route %s has the most stops with %d stops." % (route, stops))
  if stops == min_stops:
    print("Route %s has the fewest stops with %d stops." % (route, stops))

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

# Build lookup tables of routes and stops by id => name
all_route_ids = {}
def get_all_route_ids():
  url = (f"{base_url}/routes?"
         f"&{api_key}"
         f"&fields[route]=short_name,long_name"
         f"&filter[type]=0,1")

  r = requests.get(url)
  for e in r.json()["data"]:
    all_route_ids[e["id"]] = e["attributes"]["long_name"]

  return all_route_ids

all_stop_ids = {}
all_parent_station_ids = {}

def get_all_stop_ids():
  url = (f"{base_url}/stops?"
         f"&{api_key}"
         f"&fields[stops]=short_name,parent_station"
         f"&filter[route_type]=0,1")

  r = requests.get(url)
  j = r.json()

  for e in j["data"]:

    # Unforunately, multiple IDs key to the same stop, e.g.,
    #  '70273': 'Capen Street',
    #  '70274': 'Capen Street',
    #  '70275': 'Mattapan',
    #  '70276': 'Mattapan',
    #  ...
    if e["attributes"]["name"] not in all_stop_ids.values():
      all_stop_ids[e["id"]] = e["attributes"]["name"]

    p_station_id = e["relationships"]["parent_station"]["data"]["id"]

    if p_station_id not in all_parent_station_ids:
      all_parent_station_ids[p_station_id] =  e["attributes"]["name"]

  return all_stop_ids

def get_stop_name(identifier):
  url = (f"{base_url}/stops/"
         f"{identifier}/"
         f"&fields[stops]=short_name")

get_all_route_ids()
get_all_stop_ids()

######################################################################

routes_stops_dict = {} 
stops_routes_dict = {} 

# Now gather all the trips (with route and stops included) by route id
for route_id in all_route_ids.keys():
  url = (f"{base_url}/stops?"
         f"&{api_key}"
         f"&filter[route]={route_id}"
         f"&fields[trip]=name")

  r = requests.get(url)
  j = r.json()

  for stop in j["data"]:

    stop_id = stop["id"]

    # Build dict's of { route => stops } and { stop => routes }
    if route_id not in routes_stops_dict:
      routes_stops_dict[route_id] = set()

    if stop["id"] in all_stop_ids:
      stop_name = all_stop_ids[stop["id"]]
    elif stop["id"] in all_parent_station_ids:
      stop_name = all_parent_station_ids[stop["id"]]
    else:
      stop_name = "Stop not found"

    routes_stops_dict[route_id].add((stop_id, stop_name))

    if stop_id not in stops_routes_dict:
      stops_routes_dict[stop_id] = set()

    stops_routes_dict[stop_id].add((route_id, all_route_ids[route_id]))

# FIXME: Only considers Green line (should also include Red, Orange, Blue),
#       because stops such as "Park Street", which are on two routes (of
#       different color), are only listed as being on Green Line routes.
print("\nStops connecting two or more subway routes:\n")
for stop_id,routes in stops_routes_dict.items():
  if len(stops_routes_dict[stop_id]) > 1:

    if stop_id in all_stop_ids:
      stop_name = all_stop_ids[stop_id]
    elif stop_id in all_parent_station_ids:
      stop_name = all_parent_station_ids[stop_id]
    else:
      stop_name = "Stop not found"

    print("\tStop: %s, Routes: %s" %
          (stop_name,
           [v[1] for v in stops_routes_dict[stop_id]]))

exit()

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


# In the list of trips, find destination

