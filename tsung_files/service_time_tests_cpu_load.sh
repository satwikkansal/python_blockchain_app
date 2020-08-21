#!/bin/bash

for i in {0..15..1}
do
        tsung -f ../service_time_flight_counter_test_cpu_load.xml start

done

