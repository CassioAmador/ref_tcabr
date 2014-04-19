def check_libraries():
    modules=['Tkinter','Pmw','sqlite3','ssh','paramiko','serial']
#    modules.append('boi')
    mod_er=[]
    import imp
    print 'Modules:'
    for module in modules:
        try:
            imp.find_module(module)
            print '\t%s:  ok' % module
        except ImportError:
            print '\t%s:  no' % module
            mod_er.append(module)
    if len(mod_er)!=0:
        print '\nModules missing: %s' % mod_er
        return False
    else:
        return True

def check_ATCA():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.listen(5)
    try:
        sock.connect(('143.107.131.237',22))
        print "Connection to ATCA: ok"
        return True
    except socket.error:
        print "can't establish connection to ATCA crate"
        return False
    except AttributeError:
        print "can't establish connection to ATCA crate"
        return False

def check_REFDB():
    from os.path import isfile
    from os import getcwd
    database='%s/ref.db' % getcwd()
    if isfile(database)==1:
        print 'REF database: ok'
        return True
    else:
        print 'REF database: no'
        return False

def init_tests():
    lib=check_libraries()
    atca=check_ATCA()
    refdb=check_REFDB()
    if lib & refdb & atca:
        print 'oba, pronto pra ir!'
    else:
        print 'ih, se deu mal!!!'

if __name__=='__main__':
    init_tests()
