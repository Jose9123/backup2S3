import subprocess, os, time, shutil, boto3, botocore



# Let's use Amazon S3
s3 = boto3.resource('s3')
# initialize
now = time.time()
onedays_ago = now - 60*60*24*1
bucketname = 'bucket-name'
bucket = s3.Bucket(bucketname)

driveLetter = 'T:' 
networkPath = '\\\\127.0.0.1\\windows-share-name$'
user = 'username' 
password = 'password'

# Disconnect anything on drive letter T
def unMapDrive():	
	winCMD = 'NET USE ' + driveLetter + ' /delete'
	# print(winCMD)
	subprocess.Popen(winCMD, stdout=subprocess.PIPE, shell=True)
	time.sleep(3)

# Connect to map network drive to letter Q
def mapDrive(): 
	winCMD = 'NET USE ' + driveLetter + ' ' + networkPath + ' /User:' + user + ' ' + password
	# print(winCMD)
	subprocess.Popen(winCMD, stdout=subprocess.PIPE, shell=True)
	time.sleep(3)

def isDriveMapped(path):
     try:
     	return os.path.exists(path)
     except:
     	return False

def copyBackupFileLocally():
	for name in os.listdir(driveLetter):
		if name.endswith(".7z") & ((os.path.getctime(driveLetter + '\\' + name) > onedays_ago)):
			print("Copying: " + name + " to " + os.getcwd() + "...")
			shutil.copy((driveLetter + '\\' + name), os.getcwd())
			return name

def copyBackupFile2S3(filename):
	fileFullPath = os.getcwd() + "\\" + filename
	filekey = "bucket-path/" + filename
	bucketExists = True
	try:
	    s3.meta.client.head_bucket(Bucket=bucketname)
	except botocore.exceptions.ClientError as e:
	    # If a client error is thrown, then check that it was a 404 error.
	    # If it was a 404 error, then the bucket does not exist.
	    error_code = int(e.response['Error']['Code'])
	    if error_code == 404:
	        bucketExists = False
	if bucketExists:
		print("Copying: " + filename + " to " + bucketname + filekey + "on S3 ...")
		s3.meta.client.upload_file(fileFullPath, bucketname, filekey)	

def purgeOldFiles():
	for f in os.listdir():
		creation_time = os.path.getctime(f)
		if ((now - creation_time) // (24 * 3600) >= 7) & (f.endswith(".7z")):
			os.remove(f)
			print('{} removed'.format(f))

if not isDriveMapped(driveLetter):
	mapDrive()

filename = copyBackupFileLocally()
copyBackupFile2S3(filename)
unMapDrive()
purgeOldFiles()