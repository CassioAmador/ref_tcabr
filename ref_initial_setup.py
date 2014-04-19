import sqlite3
from os import getcwd
from sys import argv

lugar='/home/GRS/TCABR'
arq='shot_number'
database='%s/%s.db' % (lugar,arq)
if len(argv)>1:
    if argv[1]=='mirror':
        database='%s/%s_test.db' % (lugar,arq)
    elif argv[1]=='clean':
        database='%s/%s_clean.db' % (lugar,arq)

def initdatabase():
    arq='ref'
    if argv[1]=='data':
        database='%s/%s.db' % (lugar,arq)
    elif argv[1]=='mirror':
        database='%s/%s_test.db' % (lugar,arq)
    elif argv[1]=='clean':
        database='%s/%s_clean.db' % (lugar,arq)
    
    con=sqlite3.connect(database)
    print 'Creating database: %s' % database
    cur=con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS  ff
(date text, shot int, freq_start real, angle real, rate int, start_time int)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS sf
(date text, shot int, sweep int, freq_start real, freq_end start, angle real, rate int,start_time int, interv_sweep int)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS hf
(date text, shot int, freq_table text, time_step int, restart_table int, angle real, rate real,start_time int)''')

    con.close()
    print 'database created!'

def initshotlist():
    con=sqlite3.connect(database)
    c=con.cursor()
    c.execute('''CREATE TABLE shot (shot_number INT)''')
    c.execute("INSERT INTO shot VALUES (?)", (0,))
    con.commit()
    con.close()

if __name__=='__main__':
    print 'Edit me first!!!!'
#    initshotlist()
#    add_shot()
#    while(last_shot()!=25422):
#        add_shot()        
#    initdatabase()
