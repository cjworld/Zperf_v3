from SimpleXMLRPCServer import SimpleXMLRPCServer
from pkg.devices.windows import WindowsDevice

if __name__ == '__main__':
    server = SimpleXMLRPCServer(('localhost', 8000))
    server.register_introspection_functions()
    a = WindowsDevice()
    server.register_instance(WindowsDevice)
    server.serve_forever()
