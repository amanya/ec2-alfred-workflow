#!/bin/env python

import argparse
import sys
import os

import ConfigParser
import boto.ec2
from workflow import Workflow, ICON_NETWORK, ICON_WARNING

AWS_CONFIG_FILE = "{}/.aws/config".format(os.environ.get('HOME'))
LOGGER = None


def get_profiles():
    config = ConfigParser.ConfigParser()
    config.readfp(open(AWS_CONFIG_FILE))
    sections = []
    for section in config.sections():
        if section.find('profile') == 0:
            section = section[8:]  # remove 'profile' from profile name
        profile = {'name': section}
        sections.append(profile)
    return sections


def get_recent_instances(region, profile_name):
    conn = boto.ec2.connect_to_region(region,
                                      profile_name=profile_name)
    reservations = conn.get_all_reservations()

    instances = []

    for res in reservations:
        for i in res.instances:
            if i.state != 'running':
                continue
            name = 'Name' in i.tags and i.tags['Name'] or i.dns_name
            if i.ip_address:
                desc = i.ip_address + u' [' + i.instance_type + ']'
            else:
                desc = u' [' + i.instance_type + ']'
            instances.append({'desc': desc,
                              'ip': i.ip_address,
                              'name': name})

    return instances


def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('--set-region', dest='region', nargs='?', default=None)
    parser.add_argument(
        '--list-profiles',
        dest='list_profiles',
        action="store_true")
    parser.add_argument(
        '--set-profile',
        dest='profile_name',
        nargs='?',
        default=None)
    parser.add_argument('query', nargs='?', default=None)
    args = parser.parse_args(wf.args)

    account = wf.settings.get('active_account', 'default')

    if account not in wf.settings:
        wf.settings['account'] = {}

    if args.profile_name:
        wf.settings.setdefault(account, {})['profile_name'] = args.profile_name
        wf.settings.save()
        return 0

    if args.region:
        wf.settings.setdefault(account, {})['region'] = args.region
        wf.settings.save()
        return 0

    if args.list_profiles:
        list_profiles(wf, args.query)
        return 0

    query_instances(wf, args.query)


def query_instances(wf, query):
    account = wf.settings.get('active_account', 'default')
    aws_access_key_id = wf.settings[account].get('aws_access_key_id', None)
    profile_name = wf.settings[account].get('profile_name', 'default')

    region = wf.settings[account].get('region', 'eu-west-1')

    def wrapper():
        return get_recent_instances(region, profile_name)

    instances = wf.cached_data('instances-%s' % account, wrapper, max_age=10)

    if query:
        instances = wf.filter(query, instances, key=search_key_for_instance)

    if not instances:
        wf.add_item('No instances found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for instance in instances:
        wf.add_item(arg="{}|{}".format(profile_name, instance['ip']),
                    uid=instance['ip'],
                    icon=ICON_NETWORK,
                    subtitle=instance['desc'],
                    title=instance['name'],
                    copytext=instance['ip'],
                    valid=True)

    wf.send_feedback()


def list_profiles(wf, query):
    profiles = get_profiles()

    if query:
        profiles = wf.filter(query, profiles, key=search_key_for_profile)

    if not profiles:
        wf.add_item('No profile found', icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    for profile in profiles:
        wf.add_item(arg=profile['name'],
                    icon=ICON_NETWORK,
                    title=profile['name'],
                    valid=True)

    wf.send_feedback()


def search_key_for_instance(instance):
    elements = []
    elements.append(instance['name'])

    return u' '.join(elements)


def search_key_for_profile(profile):
    elements = []
    elements.append(profile['name'])

    return u' '.join(elements)


if __name__ == '__main__':
    wf = Workflow()
    LOGGER = wf.logger
    sys.exit(wf.run(main))
