'''
Adam Gleichsner
amg188@case.edu

eecs325
Project 2
'''
import socket, struct, time, select
import matplotlib.pyplot as mpl


'''
main()
Reads all target ip addresses from file targets.txt and iterates
through them, running traceroute on each one to get the number
of hops and rtt of a trace to said ip
'''
def main():
    targets = [line.strip() for line in open('targets.txt')]
    output = open('trace_results.txt', "w")
    for target in targets:
        results = traceroute(target, True)
        #If we have successfully tracerouted the address, store the data
        if results is not None:
            output.write("%s\t%d\t%d\n" % (results[0], results[1], results[2]))
    output.close()

    make_graph()


'''
make_graph()
Using a basic scatterplot in matplotlib.pyplot, we plot hops
versus rtt for each traceroute recorded in results.txt
'''
def make_graph():
    in_data = open('trace_results.txt', "r")
    rtt = []
    hops = []
    for line in in_data:
        #File is tab delineated
        split_data = line.split('\t')
        hops.append(split_data[1])
        #Each route is newline separated, so remove the \n
        rtt.append(split_data[2].strip())

    #Plot hops v rtt as red circles, label axis, and show
    mpl.plot(hops, rtt, 'ro')
    mpl.grid(color='b', linestyle='-', linewidth=1)
    mpl.ylabel('RTT(ms)')
    mpl.xlabel('Hops(#)')
    xmin, xmax = mpl.xlim()
    ymin, ymax = mpl.ylim()
    mpl.xlim((xmin - 1, xmax + 1))
    mpl.ylim((ymin - 5, ymax + 5))
    mpl.show()


'''
traceroute(target)
General while True structure and exception handling of sockets
inspired by Learning by doing: Traceroute tutorial by Oracle, here:
https://blogs.oracle.com/ksplice/entry/learning_by_doing_writing_your

Finds number of hops by running a binary search on the udp packets
by changing the ttl according to the icmp return messages

Socket timeouts occur every 7 seconds, but will wait until we exceed
a maximum ttl of 64
'''
def traceroute(target, verbose):
    timeout = 0     #Keep track of if we've timed out so we can adjust ttl accordingly
    port = 33433
    # icmp = socket.getprotobyname('icmp')
    # udp = socket.getprotobyname('udp')
    # Values to monitor range of possible ttls, start at 16
    max_ttl = 64
    cur_ttl = 16
    bot_ttl = 0
    top_ttl = 0

    # **Uncomment for debugging**
    # old_ttl = 0

    # Keep track if we have found our range of possible values
    has_been_smallest = False
    has_been_largest = False

    #Always run until we find the route or timeout
    while True:
        # **Uncomment for debugging**
        # old_ttl = cur_ttl

        #Setup the socket fresh each time
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, cur_ttl)
        
        recv_socket.bind(("", port))
        send_socket.sendto("", (target, port))
        #Timeout after 7 seconds of listening
        listen = select.select([recv_socket], [], [], 7.0)
        try:
            #If we have a response, read it
            if listen[0]:
                #Get the incoming packet
                recv_packet, cur_addr = recv_socket.recvfrom(1024)
                #Unpack to get the icmp return code
                code_type, code = struct.unpack("bb", recv_packet[20:22])
            
                # TTL is too small
                if (code_type == 11):    
                    # If we are hitting the bottom of the range for the first time, setup the range
                    # and activate the flags for future reference
                    if (not has_been_smallest):
                        has_been_smallest = True
                        bot_ttl = cur_ttl
                    # If we've hit the largest, then we can start to narrow down the right ttl
                    if (has_been_largest):
                        bot_ttl = cur_ttl
                        cur_ttl = (top_ttl + bot_ttl)/2
                    # We need to find a value that's too large
                    else:
                        cur_ttl *=  2
                # TTL is too large
                elif (code_type == 3):
                    # If this is the first time we're too large, setup range and flags
                    if (not has_been_largest):
                        has_been_largest = True
                        top_ttl = cur_ttl
                    # If we have a complete range, shrink ttl
                    if (has_been_smallest):
                        top_ttl = cur_ttl
                        cur_ttl = (top_ttl + bot_ttl)/2
                    #If we've never timed out, we need to find the smallest
                    elif(timeout == 0):
                        cur_ttl /= 2
                    # Otherwise, we need to find the smallest ttl still
                    else:
                        cur_ttl = 4
                #We aren't concerned with other codes, so in those cases we want to effectively timeout
                else:
                    #Double our ttl to try to find a working value and adjust our range if needed
                    cur_ttl *= 2
                    if has_been_largest and cur_ttl > top_ttl:
                        top_ttl = cur_ttl

                # **Uncomment for debugging**
                # print("%d\t%d, %d\t%s\t[%d, %d]" % (old_ttl, code_type, code, cur_addr[0], bot_ttl, top_ttl))
            else:
                #Double our ttl to try to find a working value and adjust our range if needed
                cur_ttl *= 2
                if has_been_largest and cur_ttl > top_ttl:
                    top_ttl = cur_ttl
        except socket.error:
            print(socket.error)
        finally:
            send_socket.close()
            recv_socket.close()

        #If we've narrowed down our range
        if top_ttl - bot_ttl <= 1 and has_been_smallest and has_been_largest:
            #If we're at the right ttl
            if code_type == 11:
                ttl = top_ttl
            else:
                ttl = bot_ttl
            #Get the traceroute data by running a single trace for timing
            addr, rtt = raw_traceroute(target, ttl)
            #If we've actually hit the target
            if addr == target:
                if verbose:
                    print("%s\t%d hops\t%dms" % (addr, ttl, rtt))
                return addr, ttl, rtt    
        #Timeout
        if cur_ttl > max_ttl:
            if verbose:
                print("%s\tError: Unable to reach target" % target)
            return None


'''
raw_traceroute(target, ttl)
Quick traceroute that only runs once at the given ttl, also
times the trace so we can use it later for graphing
'''
def raw_traceroute(target, ttl):
    port = 33433
    # icmp = socket.getprotobyname('icmp')
    # udp = socket.getprotobyname('udp')
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.getprotobyname('udp'))
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    recv_socket.bind(("", port))
    recv_socket.settimeout(30)
    # Start timing in milliseconds
    t0 = time.time() * 1000.00
    t1 = 0
    send_socket.sendto("", (target, port))

    try:
        #If we receive something, stop the clock
        recv_packet, curr_addr = recv_socket.recvfrom(1024)
        t1 = time.time() * 1000.00
    except socket.error:
        pass
    finally:
        send_socket.close()
        recv_socket.close()

    #If we didn't get an answer, return Nones
    if (t1 == 0):
        return None, None
    else:
        return curr_addr[0], t1 - t0

# Boilerplate - Start program
if __name__ == "__main__":
    main()