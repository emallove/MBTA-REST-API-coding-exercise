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
all_stop_ids = {}

def get_all_route_ids():
  url = (f"{base_url}/routes?"
         f"&{api_key}"
         f"&fields[route]=short_name,long_name"
         f"&filter[type]=0,1")

  r = requests.get(url)
  for e in r.json()["data"]:
    all_route_ids[e["id"]] = e["attributes"]["long_name"]
  return all_route_ids

def get_all_stop_ids():
  url = (f"{base_url}/stops?"
         f"&{api_key}"
         f"&fields[stops]=short_name"
         f"&filter[route_type]=0,1")

  r = requests.get(url)
  j = r.json()
  for e in j["data"]:
    all_stop_ids[e["id"]] = e["attributes"]["name"]
  return all_stop_ids

get_all_route_ids()
get_all_stop_ids()

######################################################################

routes_stops_dict = {} 
stops_routes_dict = {} 

# Now gather all the trips (with route and stops included) by route id
for route_id in all_route_ids.keys():
  url = (f"{base_url}/trips?"
         f"&{api_key}"
         f"&include=route,stops"
         f"&page[limit]=500"
         f"&filter[route]={route_id}"
         f"&fields[trip]=name"
         f"&page[limit]=100")

  r = requests.get(url)
  j = r.json()

  for trip in j["data"]:
    for stop in trip["relationships"]["stops"]["data"]:

      # Only proceed if the stop is on a route_type=0,1
      if stop["id"] not in all_stop_ids:
        continue

      # Build dict's of { route => stops } and { stop => routes }
      if route_id not in routes_stops_dict:
        routes_stops_dict[route_id] = set()

      routes_stops_dict[route_id].add((stop["id"], all_stop_ids[stop["id"]]))

      if stop["id"] not in stops_routes_dict:
        stops_routes_dict[stop["id"]] = set()

      stops_routes_dict[stop["id"]].add((route_id, all_route_ids[route_id]))

# print("routes_stops_dict")
# pprint(routes_stops_dict)
# print("stops_routes_dict")
# pprint(stops_routes_dict)

print("\nStops connecting two or more subway routes:\n")
for stop_id,routes in stops_routes_dict.items():
  if len(stops_routes_dict[stop_id]) > 1:
    print("\tStop: %s, Routes: %s" %
          (all_stop_ids[stop_id],
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


