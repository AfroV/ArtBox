How to download a backup of XCOPY's artworks (The advanced version of right click and save)

The script is working: to run you need python installed (https://www.python.org/downloads/) and running a IPFS locally to download the file. this is faster and does not run into request limiting. The ArtBoxes are designed to always have running the IPFS. (https://docs.ipfs.tech/install/ipfs-desktop/)  You can use the desktop version.


The CSV files here is list of where the IPFS can find the media file and meta data.

To run the script python on the x.csv:  

python csv_backup.py x.csv  --workers 3  


(workers tag is to speed up the downloading. 3 id ideal.) 

This will then create a "ipfs_backup" folder and add the media files there under subfolder files. There will also be downloaded metadata (.JSON)  and html files (IPFS HTTP gateway directory listing page ).