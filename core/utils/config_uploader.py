'''
Module containing the functions necessary to interact with the wma.
Credit and less than optimal code has to be spreaded among lots of people.
'''
import os
import imp
import argparse

from PSetTweaks.WMTweak import makeTweak
from WMCore.Cache.WMConfigCache import ConfigCache


def __load_config_file(file_path):
    """
    Load a config module
    """
    print('Importing the config, this may take a while...')
    cfgBaseName = os.path.basename(file_path).replace(".py", "")
    cfgDirName = os.path.dirname(file_path)
    modPath = imp.find_module(cfgBaseName, [cfgDirName])
    loadedConfig = imp.load_module(cfgBaseName, modPath[0], modPath[1], modPath[2])
    print('Imported %s' % (file_path))
    return loadedConfig


def upload_to_couch(cfg_file_name, label, user_name, group_name, database_url):
    if not os.path.exists(cfg_file_name):
        raise Exception('Can\'t locate config file %s.' % cfg_file_name)

    loaded_config = __load_config_file(cfg_file_name)
    database_name = 'reqmgr_config_cache'
    configCache = ConfigCache(database_url, database_name)
    configCache.createUserGroup(group_name, user_name)
    configCache.addConfig(cfg_file_name)
    configCache.setPSetTweaks(makeTweak(loaded_config.process).jsondictionary())
    configCache.setLabel(label)
    configCache.setDescription(label)
    configCache.save()

    print('DocID    %s: %s' % (label, configCache.document["_id"]))
    print('Revision %s: %s' % (label, configCache.document["_rev"]))

    return configCache.document["_id"]


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--file',
                    dest='filename',
                    type=str,
                    help='File to be uploaded')
parser.add_argument('--label',
                    type=str,
                    help='Label, e.g. prepid')
parser.add_argument('--user',
                    type=str,
                    help='Username')
parser.add_argument('--group',
                    type=str,
                    help='Group')
parser.add_argument('--db',
                    type=str,
                    help='Database url')


args = parser.parse_args()
upload_to_couch(args.filename, args.label, args.user, args.group, args.db)
