import socket, struct, time, select

def main():
    targets = [line.strip() for line in open('targets.txt')]
    
    print("Start")
    for target in targets:
        traceroute(target)

def traceroute(target):
    timeout = 0
    max_ttl = 64
    port = 33433
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    
    old_ttl = 16
    cur_ttl = 16
    bot_ttl = 0
    top_ttl = 0

    has_been_smallest = False
    has_been_largest = False

    while True:
        recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, cur_ttl)
        recv_socket.bind(("", port))
        send_socket.sendto("", (target, port))
        listen = select.select([recv_socket], [], [], 7.0)
        try:
            if listen[0]:
                recv_packet, _ = recv_socket.recvfrom(1024)
                ip_header = struct.unpack('!BBHHHBBH4s4s' , recv_packet[0:20])
                source_addr = socket.inet_ntoa(ip_header[8]);
                code_type, code = struct.unpack("bb", recv_packet[20:22])
                # source_addr = struct.unpack("HH", recv_packet[12:16])
                # print(source_addr)
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
                    # Otherwise, we need to find the smallest ttl still
                    else:
                        cur_ttl /= 2
                # TTL is just right
                else:
                    #If we're finding our smallest ttl still
                    if (not has_been_smallest):
                        cur_ttl /= 2
                    else:
                        #If we're finding our largest ttl still
                        if (not has_been_largest):
                            cur_ttl *= 2
                        #Otherwise we're done
            else:
                cur_ttl *= 2
                timeout += 1
        except socket.error:
            print(socket.error)
        finally:
            send_socket.close()
            recv_socket.close()

        if top_ttl - bot_ttl <= 1 and has_been_smallest and has_been_largest:# and source_addr == target:
            if code_type == 11:
                ttl = top_ttl
            else:
                ttl = bot_ttl
            addr, rtt = raw_traceroute(target, ttl)
            if addr == target:
                print("%s\t%d hops\t%dms" % (addr, ttl, rtt))
                return addr, ttl, rtt    

        if timeout > 3 or cur_ttl >= max_ttl:
            print("%s\tError: Unable to reach target" % target)
            return None

def raw_traceroute(target, ttl):
    port = 33433
    icmp = socket.getprotobyname('icmp')
    udp = socket.getprotobyname('udp')
    
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, udp)
    t0 = time.time() * 1000
    t1 = 0
    send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
    recv_socket.bind(("", port))
    recv_socket.settimeout(30)
    send_socket.sendto("", (target, port))
    
    try:
        recv_packet, curr_addr = recv_socket.recvfrom(1024)
        t1 = time.time() * 1000 
    except socket.error:
        pass
    finally:
        send_socket.close()
        recv_socket.close()

    if (t1 == 0):
        return None, 0
    else:
        return curr_addr[0], t1 - t0

# Boilerplate - Start program
if __name__ == "__main__":
    main()