import urllib

db_path="/home/GRS/TCABR"

def read_shot():
    '''Read last shot number form Log Book (updated by the operator).'''
    web='http://sausage.if.usp.br/tcabrLogBook/shot_info.php?last=true'
    # get data
    f = urllib.urlopen(web)
    s = f.read()
    f.close()
    lastshot=s.split('value=')[1].split('"')[1]
    return int(lastshot)

def add_shot(tipo):
    '''Increase one in shot number for tests.'''
    import sqlite3
    if tipo=='mirror':
        database='%s/shot_number_test.db' % (db_path)
    elif tipo=='cleaning_plasma':
        database='%s/shot_number_clean.db' % (db_path)
    con=sqlite3.connect(database)
    c=con.cursor()
    lastshot=[i for i in c.execute('SELECT * FROM shot')][0][0]
    c.execute('DELETE FROM shot WHERE shot_number=%d' % lastshot)
    c.execute('INSERT INTO shot VALUES (?)', (lastshot+1,))
    con.commit()
    con.close()
    print 'Actual shot: %s in database: %s' % (lastshot+1,database.split('/')[-1])

def last_shot(tipo):
    '''Read shot number for tests.'''
    import sqlite3
    if tipo=='mirror':
        database='%s/shot_number_test.db' % (db_path)
    elif tipo=='cleaning_plasma':
        database='%s/shot_number_clean.db' % (db_path)
    con=sqlite3.connect(database)
    c=con.cursor()
    lastshot=[i for i in c.execute('SELECT * FROM shot')][0][0]
    con.close()
    return lastshot

if __name__=='__main__':
    import time
    ls=read_shot()
    print "\nLast shot:"
    print ls
    print "time:"
    print time.strftime("%X %B %d %Y")
    print ""
