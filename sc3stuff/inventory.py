#!/usr/bin/env python
# -*- coding: utf-8 -*-

def InventoryIterator(inventory, time=None):
    """
    inventory is a SC3 inventory object
    """

    nnet = inventory.networkCount()
    for inet in xrange(nnet):
        network = inventory.network(inet)
        nsta = network.stationCount()
        for ista in xrange(nsta):
            station = network.station(ista)

            if time is not None:
                try:
                    start = station.start()
                except:
                    continue

                try:
                    end = station.end()
                    if not start <= now <= end:
                        continue
                except:
                    pass

            # now we know that this is an operational station at the
            # specified time
            for iloc in xrange(station.sensorLocationCount()):
                location = station.sensorLocation(iloc)

                for istr in range(location.streamCount()):
                    stream = location.stream(istr)

                    yield network, station, location, stream

