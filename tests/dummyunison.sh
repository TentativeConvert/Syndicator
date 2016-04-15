#! /bin/bash
i=1
while [ $i -ne 10000 ] 
do
    let "i=((i+1)%40)"
    case "$i" in
	"1")
	    echo "UNISON 2.48.3 started propagating changes at 04:51:06.96 on 24 Jan 2016"
	    ;;
	"2")
	    echo "[BGN] Copying Dropbox/Untitled Document from /home/marcus to //reh//home/reh/zibrowius"
	    ;;
	"3")
	    echo "Shortcut: copied /home/reh/zibrowius/Dropbox/Untitled Document from local file /home/reh/zibrowius/Dropbox/WORK/Research/Output/Thesis/DSpace/.itmp"
	    ;;
	"4")
	    echo "[END] Copying Dropbox/Untitled Document"
	    ;;
	"5")
	    echo "UNISON 2.48.3 finished propagating changes at 04:51:07.04 on 24 Jan 2016"
	    ;;
	"6")
	    echo "Synchronization complete at 04:51:07  (1 item transferred, 0 skipped, 0 failed)"
	    sleep 5
	    ;;
	"7")
	    echo "UNISON 2.48.3 started propagating changes at 04:51:08.26 on 24 Jan 2016"
	    ;;
	"8")
	    echo "[BGN] Copying Dropbox/test.txt from /home/marcus to //reh//home/reh/zibrowius"
	    ;;
	"9")
	    echo "Shortcut: copied /home/reh/zibrowius/Dropbox/test.txt from local file /home/reh/zibrowius/Dropbox/Untitled Document"
	    ;;
	"10")
	    echo "[END] Copying Dropbox/test.txt"
	    ;;
	"11")
	    echo "[BGN] Deleting Dropbox/Untitled Document from //reh//home/reh/zibrowius"
	    ;;
	"12")
	    echo "[END] Deleting Dropbox/Untitled Document"
	    ;;
	"13")
	    echo "UNISON 2.48.3 finished propagating changes at 04:51:08.36 on 24 Jan 2016"
	    ;;
	"14")
	    echo "Synchronization complete at 04:51:08  (2 items transferred, 0 skipped, 0 failed)"
	    sleep 5
	    ;;
	"15")
	    echo "UNISON 2.48.3 started propagating changes at 04:55:31.13 on 24 Jan 2016"
	    ;;
	"16")
	    echo "[BGN] Deleting Dropbox/test.txt from //reh//home/reh/zibrowius"
	    ;;
	"17")
	    echo "[END] Deleting Dropbox/test.txt"
	    ;;
	"18")
	    echo "UNISON 2.48.3 finished propagating changes at 04:55:31.15 on 24 Jan 2016"
	    ;;
	"19")
	    echo "Synchronization complete at 04:55:31  (1 item transferred, 0 skipped, 0 failed)"
	    sleep 5
	    ;;
	"20")
	    echo "UNISON 2.48.3 started propagating changes at 04:55:59.13 on 24 Jan 2016"
	    ;;
	"21")
	    echo "[BGN] Copying Dropbox/Untitled Document from /home/marcus to //reh//home/reh/zibrowius"
	    ;;
	"22")
	    echo "[END] Copying Dropbox/Untitled Document"
	    ;;
	"23")
	    echo "UNISON 2.48.3 finished propagating changes at 04:55:59.25 on 24 Jan 2016"
	    ;;
	"24")
	    echo "Synchronization complete at 04:55:59  (1 item transferred, 0 skipped, 0 failed)"
	    sleep 5
	    ;;
	"25")
	    echo "UNISON 2.48.3 started propagating changes at 04:56:05.82 on 24 Jan 2016"
	    ;;
	"26")
	    echo "[BGN] Copying Dropbox/new-file-with-a-long-name.txt from /home/marcus to //reh//home/reh/zibrowius"
	    ;;
	"27")
	    echo "Shortcut: copied /home/reh/zibrowius/Dropbox/new-file-with-a-long-name.txt from local file /home/reh/zibrowius/Dropbox/Untitled Document"
	    ;;
	"28")
	    echo "[END] Copying Dropbox/new-file-with-a-long-name.txt"
	    ;;
	"29")
	    echo "[BGN] Deleting Dropbox/Untitled Document from //reh//home/reh/zibrowius"
	    ;;
	"30")
	    echo "[END] Deleting Dropbox/Untitled Document"
	    ;;
	"31")
	    echo "UNISON 2.48.3 finished propagating changes at 04:56:05.91 on 24 Jan 2016"
	    ;;
	"32")
	    echo "Synchronization complete at 04:56:06  (2 items transferred, 0 skipped, 0 failed)"
	    sleep 5
	    ;;
	*)
	    echo $i "Keine Nachricht ist auch eine Nachricht." 
	    ;;
    esac
    sleep 0.02
done


