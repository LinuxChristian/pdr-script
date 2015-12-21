import sqlite3 as lite
import numpy as np

if __name__ == "__main__":
    con = None
    
    # Connect to database
    try:
        con = lite.connect('pdr.db')
        cur = con.cursor()    

    except lite.Error, e:

        print "Error %s:" % e.args[0]
        sys.exit(1)

    f = np.genfromtxt('postnummer-areal.csv', skip_header = 1, delimiter=',')
    
    try:
        for zips in f:
            cur.execute('UPDATE Zips SET area='+str(zips[2])+' WHERE zip="'+str(int(zips[0]))+'"')
    finally:
        con.commit()
        cur.close()
        print("Done")

