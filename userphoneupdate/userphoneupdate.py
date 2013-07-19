#!/usr/bin/python3

#GPLv2 license

import sys
import re
import sqlite3
import csv
import string

def regexp(expr, item):
	reg = re.compile(expr, flags=re.IGNORECASE)
	return reg.search(item) is not None

def asciify(string):
    # Returns the string without non ASCII characters
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

conn = sqlite3.connect(':memory:')
conn.create_function("REGEXP", 2, regexp)
c = conn.cursor()
c.execute('CREATE TABLE users (FirstName TEXT, LastName TEXT, UserID TEXT)')
c.execute('CREATE TABLE phones (DeviceName TEXT, Description TEXT, DeviceType TEXT, DirectoryNumber TEXT)')
c.execute('CREATE TABLE nophones (DeviceName TEXT, Description TEXT, DeviceType TEXT, DirectoryNumber TEXT)')
conn.commit()

print("Importing files")

with open("input/Export_Phones", encoding="utf-8") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		if len(re.findall('SEP', row[0])) == 1:   #Only load phones, exclude CTI ports etc
			c.execute('INSERT INTO phones values (?,?,?,?)',(row[0], row[1], row[36],row[130]))

with open("input/Export_Users", encoding="utf-8") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		c.execute('INSERT INTO users values (?,?,?)',(row[0], row[2], row[3]))

c.execute('INSERT INTO nophones SELECT * FROM phones') #Copy phones table to nophones

conn.commit()

#Open output files
userupdate = 	open("output/Update_Users.txt", "w")
phoneupdateFL = open("output/Update_Phones_FL.txt", "w")	# Update phone descriptions with FirstName LastName
phoneupdateLF = open("output/Update_Phones_LF.txt", "w")	# or LastName FirstName
multiple = 		open("output/Multiple_Phones.txt","w")

#Write CSV headers
userupdate.write("USER ID, CONTROLLED DEVICE 1\n")
phoneupdateFL.write("MAC ADDRESS,DESCRIPTION,DIRECTORY NUMBER  1,LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1\n")
phoneupdateLF.write("MAC ADDRESS,DESCRIPTION,DIRECTORY NUMBER  1,LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1\n")

#Get all users ordered by last name
c.execute('SELECT * FROM users ORDER BY LastName')
userdump = c.fetchall()

counter=0
total=len(userdump)

for row in userdump:
	counter = counter + 1
	if counter/100 == int(counter/100):
		print("Processing", counter, "out of", total)

	query = "SELECT * FROM phones WHERE "
	names = str(row[0] + ' ' + row[1]).split() #Merge first and last name, then split at every space ['Anne', 'Mary', 'Von', 'Munchausen']

	for i in names:
		query = query + "Description REGEXP '" + i.replace('\'','') + "' AND " #Create query of len(arr) REGEX, sanitize and drop apostrophes

	query = query[:-5] #delete last AND

	c.execute(query)
	phonedump=c.fetchall()

	if len(phonedump) > 0:
		SEP = str(row[2])
		Description = str(phonedump[0][0])
		MAC = Description[3:]
		FirstName = str(row[0]).title()
		LastName = str(row[1]).title()
		LineNumber = str(phonedump[0][3])
		FL = FirstName +" "+ LastName
		LF = LastName +" "+ FirstName

	if len(phonedump) == 1:

		line = SEP +","+ Description +"\n"    #JonesM,SEP12345
		    #Mac Address,  Description, Dir Num 1, LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1
		firstLast = MAC +","+ FL +","+ LineNumber+","+  FL		    +","+	FL         +","+   asciify(FL)      +","+  FL        +","+  asciify(FL)     +","+  FL  +","+  asciify(FL)+"\n"
		lastFirst = MAC +","+ LF +","+ LineNumber+","+  LF		    +","+	LF         +","+   asciify(LF)      +","+  LF        +","+  asciify(LF)     +","+  LF  +","+  asciify(LF)+"\n"

		userupdate.write(line)
		phoneupdateFL.write(firstLast)
		phoneupdateLF.write(lastFirst)

		query = "DELETE FROM nophones WHERE DeviceName == '"+str(phonedump[0][0])+"'" #If a phone is found, delete it from the nophones table
		c.execute(query)															#so that only unmatched phones remain

	elif len(phonedump) > 1:  #If the user has more than one phone
		multiple.write("   " + FirstName + LastName+"\n")
		
		for i in phonedump:
			line = str(i)+"\n"
			multiple.write(line)

		multiple.write("\n")


for i in c.execute('SELECT DISTINCT DeviceType FROM nophones').fetchall():  # Create lists of unmatched phones divided
	emptyphone = open("output/Empty_"+i[0].replace(' ','_')+".txt","w")		# per phone model
	emptyphone.write("USER ID, CONTROLLED DEVICE 1\n")

	query = 'SELECT Description, DeviceName FROM nophones WHERE DeviceType == \''+i[0]+'\' ORDER BY Description'
	c.execute(query)
	result=c.fetchall()

	for row in result:
		emptyphone.write(row[0].title() + "," + row[1])
		emptyphone.write("\n")

	emptyphone.close()

conn.commit()
conn.close()
userupdate.close()
phoneupdateFL.close()
phoneupdateLF.close()
multiple.close()