#!/usr/bin/python3

#GPLv2 license

import sys
import re
import sqlite3
import csv
import string

# if len(sys.argv) <= 2:
# 	print("##### ERRORE #####")
# 	print("Formato comando:")
# 	print("./aBAT Export_Phones Export_Users")
# 	exit()

def regexp(expr, item):
	reg = re.compile(expr, flags=re.IGNORECASE)
	return reg.search(item) is not None

def asciify(string):
    ''' Returns the string without non ASCII characters'''
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

conn = sqlite3.connect(':memory:')
#conn = sqlite3.connect('database.db')
conn.create_function("REGEXP", 2, regexp)
c = conn.cursor()
c.execute('CREATE TABLE users (FirstName TEXT, LastName TEXT, UserID TEXT)')
c.execute('CREATE TABLE phones (DeviceName TEXT, Description TEXT, DeviceType TEXT, DirectoryNumber TEXT)')
c.execute('CREATE TABLE nophones (DeviceName TEXT, Description TEXT, DeviceType TEXT, DirectoryNumber TEXT)')
conn.commit()

print("Importazione file")

with open("input/Export_Phones", encoding="utf-8") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		if len(re.findall('SEP', row[0])) == 1:   #Carica solo i telefoni VoIP Cisco
			c.execute('INSERT INTO phones values (?,?,?,?)',(row[0], row[1], row[36],row[130]))

with open("input/Export_Users", encoding="utf-8") as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		c.execute('INSERT INTO users values (?,?,?)',(row[0], row[2], row[3]))

c.execute('INSERT INTO nophones SELECT * FROM phones')

conn.commit()

#Apertura file output
userupdate = open("output/Update_Users.txt", "w")
phoneupdateNC = open("output/Update_Phones_NC.txt", "w")
phoneupdateCN = open("output/Update_Phones_CN.txt", "w")

userupdate.write("USER ID, CONTROLLED DEVICE 1\n")
phoneupdateNC.write("MAC ADDRESS,DESCRIPTION,DIRECTORY NUMBER  1,LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1\n")
phoneupdateCN.write("MAC ADDRESS,DESCRIPTION,DIRECTORY NUMBER  1,LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1\n")

#Spara tutti gli utenti
c.execute('SELECT * FROM users ORDER BY LastName')
result= c.fetchall()

counter=0
troppi=0
total=len(result)

for row in result:
	counter = counter + 1
	if counter/100 == int(counter/100):
		print("Elaborazione", counter, "di", total)

	query = "SELECT * FROM phones WHERE "
	nomi = str(row[0] + ' ' + row[1]).split() #Unisci nome e cognome, dividi singole parole

	for i in nomi:
		query = query + "Description REGEXP '" + i.replace('\'','') + "' AND " #Crea array di len(arr) REGEX, togli gli apostrofi

	query = query[:-5] #Togli l'ultimo AND

	c.execute(query)
	risultati=c.fetchall()

	if len(risultati) == 1:

		SEP = str(row[2])
		Description = str(risultati[0][0])
		MAC = Description[3:]
		FirstName = str(row[0]).title()
		LastName = str(row[1]).title()
		LineNumber = str(risultati[0][3])
		NC = FirstName +" "+ LastName
		CN = LastName +" "+ FirstName

		riga = SEP +","+ Description +"\n"    #RossiM,SEP12345
		    #Mac Address,  Description, Dir Num 1, LINE DESCRIPTION  1,LINE TEXT LABEL  1,ASCII LINE TEXT LABEL  1,ALERTING NAME  1,ASCII ALERTING NAME  1,DISPLAY  1,ASCII DISPLAY  1
		nomeCog = MAC +","+ NC +","+ LineNumber+","+  NC		    +","+	NC         +","+   asciify(NC)      +","+  NC        +","+  asciify(NC)     +","+  NC  +","+  asciify(NC)+"\n"
		cogNome = MAC +","+ CN +","+ LineNumber+","+  CN		    +","+	CN         +","+   asciify(CN)      +","+  CN        +","+  asciify(CN)     +","+  CN  +","+  asciify(CN)+"\n"
#		cogNome = MAC +","+ CN +","+ LineNumber+","			"\n"

		userupdate.write(riga)
		phoneupdateNC.write(nomeCog)
		phoneupdateCN.write(cogNome)

		query = "DELETE FROM nophones WHERE DeviceName == '"+str(risultati[0][0])+"'"
		c.execute(query)

	elif len(risultati) > 1:
		troppi = troppi + 1

for i in c.execute('SELECT DISTINCT DeviceType FROM nophones').fetchall():
	telvuoti = open("output/Vuoto_"+i[0].replace(' ','_')+".txt","w")
	telvuoti.write("USER ID, CONTROLLED DEVICE 1\n")

	query = 'SELECT Description, DeviceName FROM nophones WHERE DeviceType == \''+i[0]+'\' ORDER BY Description'
	c.execute(query)
	result=c.fetchall()

	for row in result:
		telvuoti.write(row[0] + "," + row[1].title())
		telvuoti.write("\n")

	telvuoti.close()

conn.commit()
conn.close()
userupdate.close()
phoneupdateNC.close()
phoneupdateCN.close()

# somma = uno+troppi
# print("Zero= ", zero, "Uno: ", uno, "Di piu: ", troppi)
# print(somma)

# for telefono in risultati:
# 	query = "DELETE FROM nophones WHERE DeviceName == "+str(telefono[0])
# 	c.execute(query)
