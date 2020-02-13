#!/usr/bin/env python
# -*- coding: utf-8 -*-

def InventoryIterator(inventory, time=None):
    """
    inventory is a SC3 inventory object
    """

    nnet = inventory.networkCount()
    for inet in range(nnet):
        network = inventory.network(inet)
        nsta = network.stationCount()
        for ista in range(nsta):
            station = network.station(ista)

            if time is not None:
                # If a time is specified, only yield inventory
                # items matching this time.

                # If the start time of an inventory item is not
                # known, this item is ignored.
                try:
                    start = station.start()
                except:
                    continue

                if time < start:
                    continue

                # If the end time of an inventory item is not
                # known it is considered "open end"
                try:
                    end = station.end()
                    if time > end:
                        continue
                except:
                    pass

                # At this point we know that this is an operational
                # station at the specified time

            for iloc in range(station.sensorLocationCount()):
                location = station.sensorLocation(iloc)

                for istr in range(location.streamCount()):
                    stream = location.stream(istr)

                    yield network, station, location, stream

