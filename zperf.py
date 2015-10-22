import os
import json
import device

available_items = [
    {
        'name': 'server',
        'path': './configs/servers/'
    },
    {
        'name': 'client',
        'path': './configs/clients/'
    },
    {
        'name': 'protocol',
        'path': './configs/protocols/'
    },
    {
        'name': 'storage',
        'path': './configs/storages/'
    }
]


def task_factory(task_config):
    server_config = task_config.get('server')
    storage_config = task_config.get('storage')
    client_config = task_config.get('client')
    protocol_config = task_config.get('protocol')

    server = device.FreeBSDServer(server_config)

    client_os = client_config.get('os')
    if client_os == 'windows':
        client = device.WindowsClient(client_config)
    # elif client_os == 'centos':
    #    client = CentOSClient(client_config)
    else:
        client = None

    task_protocol = protocol_config.get('protocol')
    if task_protocol == 'nfs':
        task = task.NfsTask(protocol_config, server=server, client=client, storage_config=storage_config)
    # elif task_protocol == 'iscsi':
    #    task = task.IscsiTask(protocol_config, server=server, client=client, storage=storage_config)
    else:
        task = task.LocalTask(protocol_config, server=server, storage=storage_config)

    return task


def execute_task(task_args):
    task = task_factory(task_args)
    task.setup_task_env()
    task.run_task()
    task.cleanup_task_env()


if __name__ == '__main__':

    options = {}
    for item_config in available_items:
        item_name = item_config.get('name')
        item_path = item_config.get('path')

        print 'Available %ss:' % (item_name)
        file_list = os.listdir(item_path)
        for file_index, filename in enumerate(file_list):
            print '\t%d. %s' % (file_index, filename)
        file_index = int(raw_input('Please select your one %s: ' % item_name))
        while file_index >= len(file_list):
            print 'Invalid value.'
            file_index = int(raw_input('Please select your one %s: ' % item_name))
        file_path = item_path + file_list[file_index]

        with open(file_path, 'r') as fp:
            options[item_name] = json.load(fp)

        print 'Your %s choice: %s' % (item_name, file_list[file_index])
        # print json.dumps(options[item_name], separators=(',',':'), indent=4, sort_keys=True)

    execute_task(options)
    print '[ENDING]'
