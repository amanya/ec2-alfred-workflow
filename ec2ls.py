#!/bin/env python

import sys
import boto.ec2
from workflow import Workflow, ICON_NETWORK, ICON_WARNING

REGION = 'eu-west-1'

def get_recent_instances():
    conn = boto.ec2.connect_to_region(REGION)
    reservations = conn.get_all_reservations()

    instances = []

    for res in reservations:
        for i in res.instances:
            name = 'Name' in i.tags and i.tags['Name'] or i.dns_name
            desc = i.ip_address
            desc += u' [' + i.instance_type + ']'
            instances.append({'desc': desc,
                              'ip': i.ip_address,
                              'name': name})

    return instances


def main(wf):

    if len(wf.args):
        query = wf.args[0]
    else:
        query = None

    instances = wf.cached_data('instances', get_recent_instances, max_age=10)

    if query:
        instances = wf.filter(query, instances, key=search_key_for_instance)

    if not instances:
        wf.add_item('No instances found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for instance in instances:
        wf.add_item(arg=instance['ip'],
                    icon=ICON_NETWORK,
                    subtitle=instance['desc'],
                    title=instance['name'],
                    valid=True)

    wf.send_feedback()

def search_key_for_instance(instance):
    elements = []
    elements.append(instance['name'])

    return u' '.join(elements)

if __name__ == u'__main__':
    wf = Workflow()
    sys.exit(wf.run(main))


