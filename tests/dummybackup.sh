#! /bin/bash
i=1
j=1
while [ $i -ne 100 ] 
do
    let "i=i+1"
    let "j=i%67"
    case "$j" in
	"0")
	    echo "Backup -- special status _home_"
	    ;;
	"11")
	    echo "Backup -- special status _info_"
	    ;;
	"22")
	    echo "Backup -- error" $i
	    ;;
	"44")
	    echo ""
	    ;;
	"66")
	    r=$RANDOM
	    echo $r
	    let "rr = r%3"
	    echo $rr
	    if [ $rr -eq 0 ]
	    then
		echo "Backup -- fatal error" $r
    		exit $r
	    fi
	    ;;
	*)
	    echo "status" $i 
	    ;;
    esac
    sleep 0.02
done


