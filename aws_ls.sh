
for b in $(cat $1); do aws s3 ls --recursive s3://$b > /tmp/111; while read -r line; do date=$(echo $line | awk '{print $1}'); size=$(echo $line | awk '{print $3}'); file=$(echo $line | awk '{$1=$2=$3=""; print $0}'); echo $b, $date, $size, $file >> ./results.csv;  done < /tmp/111  ;done
