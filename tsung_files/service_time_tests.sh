#!/bin/bash

for i in {0..15..1}
do
        tsung -f ../service_time_flight_counter_test.xml start

done

