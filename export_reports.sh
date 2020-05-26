#!/bin/bash

names=$(grep "Log directory is" $1 | awk -F '/' '{print $6}')

readarray -t splitted_names <<<"$names"

mkdir $2

i=1

for name in "${splitted_names[@]}"
do
	cp /home/lorenzo/.tsung/log/$name/report.html $2/report_$i.html

	i=$((i+1))
done