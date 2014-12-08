'''
Adam Gleichsner
amg188@case.edu

eecs325
Project 2
'''
import socket, struct, time, select
import matplotlib.pyplot as mpl
import urllib, os
from math import radians, cos, sin, asin, sqrt
from rttMeasurement import traceroute
from scipy.stats.stats import pearsonr

'''
main()
Reads all target ip addresses from file targets.txt and iterates
through them, running traceroute on each one to get the number
of hops and rtt of a trace to said ip
'''
def main():
    targets = [line.strip() for line in open('targets.txt')]
    output = open('geo_results.txt', "w")
    distance = 0

    try:
        if os.stat('trace_results.txt').st_size > 0:
            traces_exist = True
        else:
            trace_output = open('trace_results.txt', "w")
            traces_exist = False
    except OSError:
        traces_exist = False

    for target in targets:
        target_location = get_geolocation(target)
        this_location = get_geolocation("")
        distance = calculate_distance(this_location, target_location)
        print("(%fkm)" % distance)
        output.write("%s\t%f\n" % (target, distance))

        #If we don't have any correlating traceroute results, run that too
        if not traces_exist:
            #Run traceroute in non-verbose mode
            trace_results = traceroute(target, False)
            #If we have successfully tracerouted the address, store the data
            if trace_results is not None:
                output.write("%s\t%d\t%d\n" % (trace_results[0], trace_results[1], trace_results[2]))
    output.close()

    make_graph()

'''
calculate_distance(start, destination)
Given two geographic locations, calculate the distance using the haversine
formula

Implementation inspired by stack overflow solution
'''
def calculate_distance(start, destination): 
    # Get lat/lon in radians
    sLat, sLon, dLat, dLon = map(radians, [start[0], start[1], destination[0], destination[1]])

    # Haversine
    deltaLat = dLat - sLat
    deltaLon = dLon - sLon

    a = sin(deltaLat/2)**2 + cos(sLat) * cos(dLat) * sin(deltaLon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km


'''
get_geolocation(target)
Sends a request to freegeoip.net to get the latitude and longitude of
the target ip.
'''
def get_geolocation(target):
    print(getattr(object,  name, default))
    lat = 0.0
    lon = 0.0
    request = urllib.urlopen("http://freegeoip.net/xml/" + target)
    for line in request:
        if "<Latitude>" in line:
            lat = float(line.replace("<Latitude>", "").replace("</Latitude>", ""))
        elif "<Longitude>" in line:
            lon = float(line.replace("<Longitude>", "").replace("</Longitude>", ""))
    if len(target) > 0:
        print("Location for %s is %f, %f" % (target, lat, lon)),
    return lat, lon

'''
make_graph()
Using a basic scatterplot in matplotlib.pyplot, we plot hops versus distance
and rtt versus distance, as well as calculating and outputing the Pearson's r
value between all three sets of data.
'''
def make_graph():
    trace_data = open('trace_results.txt', "r")
    geo_data = open('geo_results.txt', "r")
    
    ips = []
    rtt = []
    hops = []
    dist = []

    for line in trace_data:
        #File is tab delineated
        split_data = line.split('\t')
        ips.append(split_data[0])
        hops.append(int(split_data[1]))
        #Each route is newline separated, so remove the \n
        rtt.append(float(split_data[2].strip()))

    for line in geo_data:
        split_data = line.split('\t')
        if split_data[0] in ips:
            dist.append(float(split_data[1].strip()))

    #Calculate Pearson's r values between each set
    r_hops_dist, _ = pearsonr(hops, dist)
    r_rtt_dist, _ = pearsonr(rtt, dist)
    r_hops_rtt, _ = pearsonr(hops, rtt)

    print("Pearson's r for:\n\t"),
    print("Hops v Distance:%f\n\t" % r_hops_dist),
    print("RTT v Distance:\t%f\n\t" % r_rtt_dist),
    print("Hops v RTT:\t%f" % r_hops_rtt)

    #Plot hops v distance as red circles, adjusta and label axis
    mpl.figure(1)
    mpl.plot(hops, dist, 'ro')
    mpl.grid(color='b', linestyle='-', linewidth=1)
    mpl.ylabel('Distance(km)')
    mpl.xlabel('Hops(#)')
    xmin, xmax = mpl.xlim()
    ymin, ymax = mpl.ylim()
    mpl.xlim((xmin - 1, xmax + 1))
    mpl.ylim((ymin - 100, ymax + 100))

    #Plot rtt v distance as red circles, label axis, and show both figures
    mpl.figure(2)
    mpl.plot(rtt, dist, 'ro')
    mpl.grid(color='b', linestyle='-', linewidth=1)
    mpl.ylabel('Distance(km)')
    mpl.xlabel('RTT(ms)')
    xmin, xmax = mpl.xlim()
    ymin, ymax = mpl.ylim()
    mpl.xlim((xmin - 5, xmax + 5))
    mpl.ylim((ymin - 100, ymax + 100))
    mpl.show()

# Boilerplate - Start program
if __name__ == "__main__":
    main()