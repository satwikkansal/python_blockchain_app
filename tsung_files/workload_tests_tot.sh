#!/bin/bash

#arr=(workload_tests_085L.xml workload_tests_08L.xml workload_tests_05L.xml workload_tests_03L.xml)
arr=(workload_tests_085L.xml workload_tests_08L.xml)
#arr=(workload_tests_03L.xml)

for name in "${arr[@]}"
do

        echo "$name"

        for i in {0..14..1}
        do
                tsung -f $name start

        done

done


