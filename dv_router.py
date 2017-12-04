"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter(basics.DVRouterBase):
    # NO_LOG = True # Set to True on an instance to disable its logging
    # POISON_MODE = True # Can override POISON_MODE here
    # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):

        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        self.routing_table = dict()
        self.neighbor_info = dict()

        # Have a separate dictionary that stored the port as key, latency as value (whenever a link goes up)
        self.link_up = dict()


    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        if latency < INFINITY:
            self.link_up[port] = latency
            for port in self.link_up:
                for dest, val_list in self.routing_table.items():
                    latency = val_list[1]
                    if val_list[0] == port:
                        latency = INFINITY
                    new_packet = basics.RoutePacket(dest, latency)
                    self.send(new_packet, port, flood = False)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity goes down.

        The port number used by the link is passed in.

        """

        for key, val in self.routing_table.items():
            if port == val[0]:
                if key in self.neighbor_info and self.neighbor_info.get(key)[0] != port:
                    self.routing_table[key] = self.neighbor_info.get(key)
                elif self.POISON_MODE == True:
                    self.routing_table[key] = [port, INFINITY, api.current_time()]
                else:
                    del self.routing_table[key]

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        if isinstance(packet, basics.RoutePacket):
            #self.log("RX %s on %s (%s)", packet, port, api.current_time())
            if packet.destination not in self.routing_table:
                # we will now populate our routing table with the packet as the key, and the port and latency as the values
                # update the packet's latency: double check if this latency update is correct?
                packet.latency = packet.latency + self.link_up.get(port)
                        # send to everyone except where the packet came from
                self.routing_table[packet.destination] = [port, packet.latency, api.current_time()]
            else:
                potential_new_latency = packet.latency + self.link_up.get(port)
                current_latency = self.routing_table.get(packet.destination)[1]
                if port == self.routing_table[packet.destination][0]:
                    if potential_new_latency >= current_latency and packet.destination in self.neighbor_info:
                        if self.neighbor_info[packet.destination][1] <= potential_new_latency:
                            self.routing_table[packet.destination] = self.neighbor_info[packet.destination]
                        else:
                            self.routing_table[packet.destination] = [port, potential_new_latency, api.current_time()]
                    else:
                        self.routing_table[packet.destination] = [port, potential_new_latency, api.current_time()]
                elif potential_new_latency <= current_latency:
                    self.routing_table[packet.destination] = [port, potential_new_latency, api.current_time()]
        # create a route packet and flood that

            #self.log(str(self.routing_table))
        # also create a different host/neighbor dictionary so you can always keep track of your neighbors for emergencies
        elif isinstance(packet, basics.HostDiscoveryPacket):
            if packet.src not in self.routing_table:
                self.routing_table[packet.src] = [port, self.link_up.get(port), None]
                self.neighbor_info[packet.src] = [port, self.link_up.get(port), None]
            else:
                self.neighbor_info[packet.src] = [port, self.link_up.get(port), None]
                potential_new_latency = self.link_up.get(port)
                current_latency = self.routing_table.get(packet.src)[1]
                if potential_new_latency <= current_latency:
                    self.routing_table[packet.src] = [port, potential_new_latency, None]
        else:
            #self.log("RX %s on %s (%s)", packet, port, api.current_time())
            #self.log(str(self.routing_table))
            if packet.dst in self.routing_table:
                if self.routing_table[packet.dst][0] != port and self.routing_table[packet.dst][1]<INFINITY:
                    self.send(packet, self.routing_table[packet.dst][0], flood= False)

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        #will make expire_routes pass.

        #If time has expired, you remove the entry from the routing table.
        for key, val in self.routing_table.items():
            if val[2] != None:
                if api.current_time() - val[2] > self.ROUTE_TIMEOUT:
                    if self.POISON_MODE:
                        self.routing_table[key][1] = INFINITY
                    else:
                        del self.routing_table[key]

        for port in self.link_up:
            for dest, val_list in self.routing_table.items():
                if self.POISON_MODE == True:
                    latency = val_list[1]
                    if val_list[0] == port:
                        latency = INFINITY
                    new_packet = basics.RoutePacket(dest, latency)
                    self.send(new_packet, port, flood=False)
                else:
                    latency = val_list[1]
                    if val_list[0] != port:
                        new_packet = basics.RoutePacket(dest,latency)
                        self.send(new_packet, port, flood= False)






