#!/bin/bash

names=$(grep "Log directory is" $1 | awk -F '/' '{print $6}')
readarray -t splitted_names <<<"$names"
#IFS='\n' read -ra splitted_names <<< "$names" 
#splitted_names=$(echo $names | tr "\\n")

#echo $splitted_names

i=0
for name in "${splitted_names[@]}"
do
	(cd /home/lorenzo/.tsung/log/$name && echo "$(/usr/local/lib/tsung/bin/tsung_stats.pl)")
	
	#echo "/home/lorenzo/.tsung/log/$name"
done