#!/usr/bin/env python

import unittest
from gridupdates import functions, config, update, version
import os
import sys
import tempfile
import platform
if sys.version_info[0] == 2:
    import ConfigParser as ConfigParser
    from ConfigParser import SafeConfigParser
else:
    import configparser as ConfigParser
    from configparser import ConfigParser as SafeConfigParser

operating_system = platform.system()
if operating_system == 'Windows':
    default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'],
                                                    ".tahoe")
else:
    default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")



class TestFunctions(unittest.TestCase):
    def test_valid_introducer(self):
        """Tests json introducer list parsing"""
        self.assertTrue(functions.is_valid_introducer('pb://md2tltfmdjvzptg4mznha5zktaxatpmz@5nrsgknvztikjxnpvidlokquojjlsudf7xlnrnyobj7e7trdmuta.b32.i2p/introducer'))
        self.assertFalse(functions.is_valid_introducer('http://killyourtv.i2p'))

    def test_valid_sublist(self):
        goodsubfile = """
{
"pb://vysqjw7x7hfiuozjsggpd5lmyj35pggu@iyawu4w66gd2356vguey2veyn7jbpyzqgpmb74wd2gxzvkuzbxya.b32.i2p/introducer":
        {
                "name": "duck",
                "contact": "<duck@mail.i2p> (http://duck.i2p)",
                "active": false,
                "reasonRemoved":  "This node has been down for a long time now and has therefore been disabled. We're patiently awaiting duck's return though."
        }
}
"""
        badsubfile = """
{
"pb://vysqjw7x7hfiuozjsggpd5lmyj35pggu@iyawu4w66gd2356vguey2veyn7jbpyzqgpmb74wd2gxzvkuzbxya.b32.i2p/introducer":
                "name": "duck",
                "reasonRemoved":  "This node has been down for a long time now and has therefore been disabled. We're patiently awaiting duck's return though."
        }
}
"""
        self.assertFalse(functions.subscription_list_is_valid(badsubfile))
        self.assertTrue(functions.subscription_list_is_valid(goodsubfile))

    def test_http_proxy_configured(self):
        """Test whether our proxy detection works."""
        os.environ['http_proxy'] = 'http://blah:666'
        self.assertTrue(functions.proxy_configured())

        os.unsetenv('http_proxy')
        del os.environ['http_proxy']
        self.assertFalse(functions.proxy_configured())


    def test_default_config(self):
        """Test whether expected config is set"""
        defconfig = {
            'tahoe_node_dir' : default_tahoe_node_dir,
            'list_uri'       : 'URI:DIR2-RO:2vuiokc4wgzkxgqf3qigcvefqa:45gscpimazsm44eoeern54b5t2u4gpf7363odjhut255jxkajpqa/introducers.json.txt',
            'news_uri'       : 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q/NEWS.tgz',
            'script_uri'     : 'URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq',
            'repairlist_uri' : 'URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a/repair-list.json.txt',
            'output_dir'     : os.path.abspath(os.getcwd())
            }
        self.assertEqual(defconfig, config.get_default_config())

    @unittest.skip('Not finished')
    def test_user_config(self):
        """Test if userconfig is parsed properly"""
        tempdir = tempfile.mkdtemp()
        operating_system = platform.system()
        if operating_system == 'Windows':
            default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'],
                                                            ".tahoe")
        else:
            default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")

        #configp = SafeConfigParser()

        config_text = """
[OPTIONS]
tahoe_node_dir = /bleh/
list_uri = URI:DIR2-RO:2vuiokc4wgzkxgqf3qigcvefqa:45gscpimazsm44eoeern54b5t2u4gpf7363odjhut255jxkajpqa/list.txt
news_uri = URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q/gnus.tgz
script_uri = URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq
repairlist_uri = URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a/repair.txt
"""
        configfile = os.path.join(tempdir, 'config.ini')
        with open('configfile','w') as conf:
            conf.write(config_text)
        conf.close()

        #config.parse_config_files(configfile)
        #configp.get('OPTIONS', 'list_uri')

    def test_compatible(self):
        """Test compatible webui code"""
        def compat(ver):
            return functions.compatible_version(ver)
        self.assertTrue(compat('1.9.2'))
        self.assertTrue(compat('1.9'))
        self.assertTrue(compat('1.8.3'))

        self.assertFalse(compat('1.9.10'))
        self.assertFalse(compat('1.7.0'))
        self.assertFalse(compat('1.8.0'))

    def test_update(self):
        """Test update checking"""
        def check(ourversion, testver):
            #p = update.Update(version.__version__, output_dir=None, url=None)
            p = update.Update(ourversion, output_dir=None, url=None)
            p.latest_version = testver
            return p.new_version_available()
        self.assertFalse(check('1.1.0', '1.0'))
        self.assertFalse(check('1.2.0', '1.2.0'))
        self.assertTrue(check('1.2.0', '2.0'))



if __name__ == '__main__':
    unittest.main()

