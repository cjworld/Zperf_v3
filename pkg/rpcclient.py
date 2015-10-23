import xmlrpclib

if __name__ == '__main__':
    s = xmlrpclib.ServerProxy('http://localhost:8000')

    # Print list of available methods
    print s.system.listMethods()
