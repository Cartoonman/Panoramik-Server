#this python program will:
#(1)take a picture 
#(2)get camera info and manipulate it inside the Python program
#(3)get list of files on camera and snip off the handle for the last image taken 
#(4)download the last image to local disk

import subprocess

## example of taking a picture
def takePicture():
    subprocess.call("ptpcam -c", shell=True)

takePicture()

# example of grabbing device info and using it in your python program.
ptpinfo = subprocess.Popen(["ptpcam", "--info"], stdout=subprocess.PIPE)

# although this simply prints to stdout, you can parse
# the response for your program
#for line in ptpinfo.stdout.readlines():
#    print(line.rstrip())

# find the last picture taken. Modify to parse for date or other
files = []
listFiles = subprocess.Popen(["ptpcam", "-L"], stdout=subprocess.PIPE)
for line in listFiles.stdout.readlines():
    files.append(line.rstrip())
lastLine = files[len(files) - 2].split(" ")
lastPicture = lastLine[0][:-1]

print("The handle for the last picture taken is " + lastPicture)

# download the picture
ptpcommand = "ptpcam --get-file=" + lastPicture

subprocess.call(ptpcommand, shell=True)
