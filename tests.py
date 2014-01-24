#!/usr/bin/env python

import unittest
from gridupdates import functions, config, update, version, news, introducers, repairs
#from gridupdates.news import News
from gridupdates.functions import gen_full_tahoe_uri
import os
import re
import sys
import tempfile
import platform
if sys.version_info[0] == 2:
    import ConfigParser as ConfigParser
    from ConfigParser import SafeConfigParser
    from StringIO import StringIO
else:
    import configparser as ConfigParser
    from configparser import ConfigParser as SafeConfigParser
    from io import StringIO

operating_system = platform.system()
if operating_system == 'Windows':
    default_tahoe_node_dir = os.path.join(os.environ['USERPROFILE'],
                                                    ".tahoe")
else:
    default_tahoe_node_dir = os.path.join(os.environ['HOME'], ".tahoe")



class TestWithoutNetwork(unittest.TestCase):
    def setUp(self):
        self.tahoe_node_uri = 'http://127.0.0.1:3456'
        self.config = config.get_default_config()
        self.capture = StringIO()
        #sys.stdout = self.capture
        self.tempdir = tempfile.mkdtemp()
        self.tahoe_node_dir = os.path.join(self.tempdir, '.tahoe')
        os.makedirs(self.tahoe_node_dir)

    def tearDown(self):
        functions.remove_temporary_dir(self.tempdir)

    def test_valid_introducer(self):
        """is_valid_introducer should be able to weed out bad introducers"""
        self.assertTrue(functions.is_valid_introducer('pb://md2tltfmdjvzptg4mznha5zktaxatpmz@5nrsgknvztikjxnpvidlokquojjlsudf7xlnrnyobj7e7trdmuta.b32.i2p/introducer'))
        self.assertTrue(functions.is_valid_introducer('pb://md2tltfmdjvzptg4mznha5zktaxatpmz@5nrsgknvztikjxnpvidlokquojjlsudf7xlnrnyobj7e7trdmuta.b32.i2p:666/introducer'))
        self.assertFalse(functions.is_valid_introducer('http://killyourtv.i2p'))

    def test_valid_sublist(self):
        """subscription_list_is_valid parse proper json and abort when it sees
        invalid json data"""

        sys.stdout = self.capture
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
        """proxy_configured should be able to determine when a proxy is set."""
        os.environ['http_proxy'] = 'http://blah:666'
        self.assertTrue(functions.proxy_configured())

        os.unsetenv('http_proxy')
        del os.environ['http_proxy']
        self.assertFalse(functions.proxy_configured())


    def test_default_config(self):
        """get_default_config should provide sane defaults"""
        defconfig = {
            'tahoe_node_dir' : default_tahoe_node_dir,
            'list_uri'       : 'URI:DIR2-RO:2vuiokc4wgzkxgqf3qigcvefqa:45gscpimazsm44eoeern54b5t2u4gpf7363odjhut255jxkajpqa/introducers.json.txt',
            'news_uri'       : 'URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q/NEWS.tgz',
            'script_uri'     : 'URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq',
            'repairlist_uri' : 'URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a/repair-list.json.txt',
            'output_dir'     : os.path.abspath(os.getcwd())
            }
        self.assertEqual(defconfig, self.config)

    @unittest.skip('Not finished')
    def test_user_config(self):
        """this will try parsing the user config"""
        #configp = SafeConfigParser()

        config_text = """
[OPTIONS]
tahoe_node_dir = /bleh/
list_uri = URI:DIR2-RO:2vuiokc4wgzkxgqf3qigcvefqa:45gscpimazsm44eoeern54b5t2u4gpf7363odjhut255jxkajpqa/list.txt
news_uri = URI:DIR2-RO:hx6754mru4kjn5xhda2fdxhaiu:hbk4u6s7cqfiurqgqcnkv2ckwwxk4lybuq3brsaj2bq5hzajd65q/gnus.tgz
script_uri = URI:DIR2-RO:hgh5ylzzj6ey4a654ir2yxxblu:hzk3e5rbsefobeqhliytxpycop7ep6qlscmw4wzj5plicg3ilotq
repairlist_uri = URI:DIR2-RO:ysxswonidme22ireuqrsrkcv4y:nqxg7ihxnx7eqoqeqoy7xxjmsqq6vzfjuicjtploh4k7mx6viz3a/repair.txt
"""
        configfile = os.path.join(self.tempdir, 'config.ini')
        with open('configfile','w') as conf:
            conf.write(config_text)
        conf.close()

        #config.parse_config_files(configfile)
        #configp.get('OPTIONS', 'list_uri')

    def test_compatible(self):
        """should be able to correctly determine if tahoe is compatible"""
        def compat(ver):
            return functions.compatible_version(ver)
        self.assertTrue(compat('1.9.2'))
        self.assertTrue(compat('1.9'))
        self.assertTrue(compat('1.8.3'))

        self.assertFalse(compat('1.9.10'))
        self.assertFalse(compat('1.7.0'))
        self.assertFalse(compat('1.8.0'))

    def test_version_comparison(self):
        """are versions are compared properly?"""
        def check(ourversion, testver):
            #p = update.Update(version.__version__, output_dir=None, url=None)
            p = update.Update(ourversion, output_dir=None, url=None)
            p.latest_version = testver
            return p.new_version_available()
        self.assertFalse(check('1.1.0', '1.0'))
        self.assertFalse(check('1.2.0', '1.2.0'))
        self.assertTrue(check('1.2.0', '2.0'))

class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.tahoe_node_uri = 'http://127.0.0.1:3456'
        self.config = config.get_default_config()
        self.oldstdout = sys.stdout
        self.capture = StringIO()
        sys.stdout = self.capture
        self.tempdir = tempfile.mkdtemp()
        self.tahoe_node_dir = os.path.join(self.tempdir, '.tahoe')
        os.makedirs(self.tahoe_node_dir)

    def tearDown(self):
        functions.remove_temporary_dir(self.tempdir)
        sys.stdout = self.oldstdout


    def test_fetch_news(self):
        """ Test news fetching."""
        web_static_dir =  os.path.join(self.tahoe_node_dir, 'static')

        n = news.News(self.tahoe_node_dir,
                    web_static_dir,
                    self.tahoe_node_uri,
                    functions.gen_full_tahoe_uri(self.tahoe_node_uri,
                    self.config['news_uri']), 0)

        self.assertTrue(n.run_action())

    def test_download_update(self):
        """should download update files"""
        updater = update.Update('1.1.0', self.tempdir,
                functions.gen_full_tahoe_uri(self.tahoe_node_uri,
                    self.config['script_uri']))
        self.assertTrue(updater.run_action('download', 'zip'))
        self.assertTrue(updater.run_action('download', 'deb'))
        self.assertTrue(updater.run_action('download', 'tar'))
        self.assertTrue(updater.run_action('download', 'exe'))
        self.assertTrue(updater.run_action('download', 'py2exe'))
        with self.assertRaises(ValueError):
            (updater.run_action('download', ''))


    def test_update_available(self):
        """Update.newversion available should find update"""
        updater = update.Update('1.3.0', self.tempdir,
                functions.gen_full_tahoe_uri(self.tahoe_node_uri,
                    self.config['script_uri']))
        self.assertFalse(updater.new_version_available())

        del updater
        updater = update.Update('1.1.0', self.tempdir,
                functions.gen_full_tahoe_uri(self.tahoe_node_uri,
                    self.config['script_uri']))
        self.assertTrue(updater.new_version_available())

    def test_introducer_list(self):
        """should sync or merge introducer lists"""
        dead_intros  = """
pb://vj2ezdq6bu5uxbciqcoo65tay2nkfqdg@uzrf37svuqf37vd57jtwywddeufm4hkrsbtwkjde7kbtfqxx4t6q.b32.i2p/introducer
pb://j3omzqrjgcsr7mwzrkekjxxyvt7jeah5@yk3f75mhhllmhwksfecunudu4bxlowlb5tt4ajrqiieo4xfybnia.b32.i2p/introducer
pb://vysqjw7x7hfiuozjsggpd5lmyj35pggu@iyawu4w66gd2356vguey2veyn7jbpyzqgpmb74wd2gxzvkuzbxya.b32.i2p/introducer
pb://yb6j4bb5r5r2gco5vrhbtv6pjwzkgzdi@fuynpbna7k4usuvlibzah2jn3fs2dxgovqeucyszghkqnaf6atwq.b32.i2p:0/introducer
pb://6y2vv5gnnd4lrw2mv4rehxfzapgdmebq@abaihqkysj6celuk6k6rmfnqjscf4uvl5nxrs4v7ykqjiarb4ydq.b32.i2p/introducer"""

        with open(os.path.join(self.tahoe_node_dir, 'introducers'), 'w') as intro:
            intro.writelines(dead_intros.strip())

        p = introducers.Introducers(self.tahoe_node_dir,
                functions.gen_full_tahoe_uri(self.tahoe_node_uri,
                self.config['list_uri']),2)

        p.run_action('sync')
        with open(os.path.join(self.tahoe_node_dir, 'introducers'), 'w+') as intro:
            introfile = intro.read()
        self.assertIsNotNone(introfile)
        r = re.search(r'Removed introducer:', str(self.capture.getvalue()))
        self.assertTrue(r) # assertNotRegex not in python2.6
        with open(os.path.join(self.tahoe_node_dir, 'introducers'), 'w') as intro:
            intro.writelines(dead_intros)
        p.run_action('merge')

        # write the dead introducers above to a file, then merge. To pass the
        # resultant introducer list should be larger than what we started with.
        with open(os.path.join(self.tahoe_node_dir, 'introducers'), 'r') as intro:
            count = len(intro.readlines())
        self.assertGreater(count, 5)

    def test_repairs(self):
        repairlist = repairs.RepairList(self.tahoe_node_uri,
                functions.gen_full_tahoe_uri(self.tahoe_node_uri, self.config['repairlist_uri']), 2)
        repairlist.run_action()

if __name__ == '__main__':
    unittest.main()

