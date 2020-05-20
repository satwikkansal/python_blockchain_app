#!/bin/bash

names=$(grep "Log directory is" file_di_log.txt | awk -F '/' '{print $6}') 

for i in {0..15..1}
do

	
done