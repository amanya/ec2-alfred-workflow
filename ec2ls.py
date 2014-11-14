#!/bin/env python

import argparse
import sys

import boto.ec2
from workflow import Workflow, ICON_NETWORK, ICON_WARNING

def get_recent_instances(aws_access_key_id, aws_secret_access_key, region):
    conn = boto.ec2.connect_to_region(region,
                                      aws_access_key_id=aws_access_key_id,
                                      aws_secret_access_key=aws_secret_access_key)
    reservations = conn.get_all_reservations()

    instances = []

    for res in reservations:
        for i in res.instances:
            if i.state != 'running':
                continue
            name = 'Name' in i.tags and i.tags['Name'] or i.dns_name
            desc = i.ip_address + u' [' + i.instance_type + ']'
            instances.append({'desc': desc,
                              'ip': i.ip_address,
                              'name': name})

    return instances


def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-access-key-id', dest='aws_access_key_id', nargs='?', default=None)
    parser.add_argument('--set-secret-access-key', dest='aws_secret_access_key', nargs='?', default=None)
    parser.add_argument('--set-region', dest='region', nargs='?', default=None)
    parser.add_argument('--set-active-account', dest='active_account', nargs='?', default=None)
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(wf.args)

    if args.active_account:
        wf.settings['active_account'] = args.active_account
        return 0

    account = wf.settings.get('active_account', 'default')

    if not account in wf.settings:
        wf.settings['account'] = {}

    if args.aws_access_key_id:
        wf.settings.setdefault(account, {})['aws_access_key_id'] = args.aws_access_key_id
        wf.settings.save()
        return 0

    if args.aws_secret_access_key:
        wf.settings.setdefault(account, {})['aws_secret_access_key'] = args.aws_secret_access_key
        wf.settings.save()
        return 0

    if args.region:
        wf.settings.setdefault(account, {})['region'] = args.region
        wf.settings.save()
        return 0

    aws_access_key_id = wf.settings[account].get('aws_access_key_id', None)

    if not aws_access_key_id:
        wf.add_item('No aws_access_key_id set.',
                    'Please use awssetaccesskey to set your access key.',
                    valid = False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    aws_secret_access_key = wf.settings[account].get('aws_secret_access_key', None)

    if not aws_secret_access_key:
        wf.add_item('No aws_secret_access_key set.',
                    'Please use awssetsecretkey to set your secret key.',
                    valid = False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    region = wf.settings[account].get('region', None)

    if not region:
        wf.add_item('No region set.',
                    'Please use awssetregion to set your region.',
                    valid = False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    query = args.query

    def wrapper():
        return get_recent_instances(aws_access_key_id, aws_secret_access_key, region)

    instances = wf.cached_data('instances-%s' % account, wrapper, max_age=10)

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


