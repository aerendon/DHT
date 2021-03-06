#!/env/bin/python

import hashlib
import json
import random
import string
import sys
import time

import zmq
from termcolor import colored

import fnode


# def check_files_node(node, my_id):
#     files_my_id = {}
#     delete = {}
#     for i in node['file']:
#         print i[0:7] + '-->>' + node['lower_bound']
#         print 'i --> ' + i
#         if my_id > node['lower_bound']:
#             if (i <= my_id and i >= 0) or (i > node['lower_bound'] and i <= 0):
#                 # print i
#                 files_my_id[i] = node['file'][i]
#                 delete[i] = i
#         else:
#             if i <= my_id and i > node['lower_bound']:
#                 # print i
#                 files_my_id[i] = node['file'][i]
#                 delete[i] = i
#
#     for i in delete:
#         print ' DEL --> ' + i
#         del node['file'][i]
#
#     files_my_id = json.dumps(files_my_id)
#
#     return files_my_id


def add(node, req, socket_send):
    fnode.printJSON(req)
    check = fnode.check_rank(node['id'], node['lower_bound'], req['msg']['id'])
    print 'CHECK --> ' + str(check)

    if check == 0:
        # files_my_id = check_files_node(node, req['msg']['id'])
        # # print files_my_id
        #
        # req_update_files = fnode.create_req('update_file',
        #                                     node['ip'] + ':' + node['port'],
        #                                     req['msg']['origin'],
        #                                     json.loads(files_my_id))
        # req_update_files_json = json.loads(req_update_files)
        # print 'Update to ' + 'tcp://' + req_update_files_json['to']
        # time.sleep(2)
        # socket_send.connect('tcp://' + req_update_files_json['to'])
        # # fnode.printJSON(req_update_json)
        # socket_send.send(req_update_files)
        # message = socket_send.recv()
        # print message

        req_update = fnode.create_req(
            'update', node['ip'] + ':' + node['port'], req['msg']['origin'], {
                'lower_bound': node['lower_bound'],
                'lower_bound_ip': node['lower_bound_ip']
            })
        req_update_json = json.loads(req_update)
        print 'Update to ' + 'tcp://' + req_update_json['to']
        time.sleep(2)
        socket_send.connect('tcp://' + req_update_json['to'])
        socket_send.send(req_update)
        message = socket_send.recv()
        print message

        node['lower_bound'] = req['msg']['id']
        node['lower_bound_ip'] = req['msg']['origin']

        fnode.node_info(node)
    elif check == -1:
        req_add = fnode.create_req(
            'add', node['ip'] + ':' + node['port'], node['lower_bound_ip'],
            {'origin': req['msg']['origin'],
             'id': req['msg']['id']})
        req_add_json = json.loads(req_add)
        socket_send.connect('tcp://' + req_add_json['to'])
        # fnode.printJSON(req_add_json)
        socket_send.send(req_add)
        message = socket_send.recv()
        print message


def update(node, req):
    fnode.printJSON(req)
    node['lower_bound'] = req['msg']['lower_bound']
    node['lower_bound_ip'] = req['msg']['lower_bound_ip']

    print '############ UPDATE OK'
    fnode.node_info(node)


def save(node, req, socket_send):
    fnode.printJSON(req)
    check = fnode.check_rank(node['id'], node['lower_bound'], req['id'])
    print 'CHECK --> ' + str(check)

    if check == 0:
        fnode.file_to_ring(node, req['name'], req['data'], req['id'])

        fnode.node_info(node)
    elif check == -1:
        req_save = json.dumps({
            'req': 'save',
            'from': node['ip'] + ':' + node['port'],
            'to': node['lower_bound_ip'],
            'data': req['data'],
            'name': req['name'],
            'id': req['id']
        })
        req_save_json = json.loads(req_save)
        socket_send.connect('tcp://' + req_save_json['to'])
        # fnode.printJSON(req_add_json)
        socket_send.send(req_save)
        message = socket_send.recv()
        print message


def remove_file(node, req, socket_send):
    fnode.printJSON(req)
    check = fnode.check_rank(node['id'], node['lower_bound'], req['id'])
    print 'CHECK --> ' + str(check)

    if check == 0:
        fnode.remove_file_ring(node, req['id'])

        fnode.node_info(node)
    elif check == -1:
        req_remove = json.dumps({
            'req': 'remove',
            'from': node['ip'] + ':' + node['port'],
            'to': node['lower_bound_ip'],
            'id': req['id']
        })
        req_remove_json = json.loads(req_remove)
        socket_send.connect('tcp://' + req_remove_json['to'])
        # fnode.printJSON(req_add_json)
        socket_send.send(req_remove)
        message = socket_send.recv()
        print message


def check_file(node, file_id):
    for i in node:
        print i
        if i == file_id:
            return node[i]
            break
    return 'No file'


def get_file(node, req, socket_send):
    fnode.printJSON(req)
    check = check_file(node['file'], req['id'])

    if check != 'No file':
        print colored(check, 'cyan')
        # fnode.node_info(node)
        req_send = json.dumps({
            'from': node['ip'] + ':' + node['port'],
            'to': req['client_origin'],
            'info': check
        })

        req_send_json = json.loads(req_send)
        socket_send.connect('tcp://' + req_send_json['to'])
        socket_send.send(req_send)
        message = socket_send.recv()
        print message

    else:
        print colored('File does not exist in this node :(', 'red')

        if req['node_origin'] == node['lower_bound_ip']:
            req_send = json.dumps({
                'from': node['ip'] + ':' + node['port'],
                'to': req['client_origin'],
                'info': 'No'
            })

            req_send_json = json.loads(req_send)
            socket_send.connect('tcp://' + req_send_json['to'])
            socket_send.send(req_send)
            message = socket_send.recv()
            print message

        else:
            get_req = json.dumps({
                'req': 'get',
                'from': req['from'],
                'to': node['lower_bound_ip'],
                'id': req['id'],
                'node_origin': req['node_origin'],
                'client_origin': req['client_origin']
            })
            get_req_json = json.loads(get_req)

            socket_send.connect('tcp://' + get_req_json['to'])
            socket_send.send(get_req)
            message = socket_send.recv()
            print colored(message, 'green')


def pass_data(node, req_json):
    for i in req_json['msg']:
        node['file'][i] = req_json['msg'][i]

    fnode.node_info(node)


def search_new_connection(node, info, socket_send):
    if node['lower_bound'] == info['node_id']:
        node['lower_bound'] = info['lower_bound']
        node['lower_bound_ip'] = info['lower_bound_ip']

        fnode.node_info(node)
    else:
        new_req = fnode.create_req('new_connection',
                                   node['ip'] + ':' + node['port'],
                                   node['lower_bound_ip'], info)
        new_req_json = json.loads(new_req)

        socket_send.connect('tcp://' + new_req_json['to'])
        socket_send.send(new_req)
        message = socket_send.recv()
        print colored(message, 'green')


# def update_file_list(node, req):
#     for i in req['msg']:
#         # print i
#         node['file'][i] = req['msg'][i]
#
#     fnode.node_info(node)
