#! /bin/bash
i=1
j=1
while [ $i -ne 10000 ] 
do
    let "i=i+1"
    let "j=i%67"
    case "$j" in
	"0")
	    echo "Sync -- special status _good_"
	    sleep 5
	    ;;
	"11")
	    echo "Sync -- special status _info_"
	    sleep 5
	    ;;
	"22")
	    echo "Sync -- error" $i
	    sleep 5
	    ;;
	"33")
	    echo "Sync -- file" $i
	    ;;
	"44")
	    echo ""
	    ;;
	"66")
	    r=$RANDOM
	    echo $r
	    let "rr = r%4"
	    echo $rr
	    if [ $rr -eq 0 ]
	    then
		echo "Sync -- fatal error" $r
    		exit $r
	    fi
	    ;;
	*)
	    echo "status" $i 
	    ;;
    esac
    sleep 0.01
done


