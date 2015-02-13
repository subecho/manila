# Copyright (c) 2014 Clinton Knight.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
Mock unit tests for the NetApp driver protocols CIFS class module.
"""

import mock

from manila import exception
from manila.share.drivers.netapp.dataontap.client import api as netapp_api
from manila.share.drivers.netapp.dataontap.protocols import cifs_cmode
from manila import test
from manila.tests.share.drivers.netapp.dataontap.protocols \
    import fakes as fake


class NetAppClusteredCIFSHelperTestCase(test.TestCase):

    def setUp(self):
        super(NetAppClusteredCIFSHelperTestCase, self).setUp()
        self.mock_object(cifs_cmode, 'LOG')

        self.mock_context = mock.Mock()

        self.mock_client = mock.Mock()
        self.helper = cifs_cmode.NetAppCmodeCIFSHelper()
        self.helper.set_client(self.mock_client)

    def test_create_share(self):

        result = self.helper.create_share(fake.SHARE_NAME, fake.SHARE_ADDRESS)

        self.mock_client.create_cifs_share.assert_called_once_with(
            fake.SHARE_NAME)
        self.mock_client.remove_cifs_share_access.assert_called_once_with(
            fake.SHARE_NAME, 'Everyone')
        self.assertEqual('//%s/%s' % (fake.SHARE_ADDRESS, fake.SHARE_NAME),
                         result)

    def test_delete_share(self):

        self.helper.delete_share(fake.CIFS_SHARE)

        self.mock_client.remove_cifs_share.assert_called_once_with(
            fake.SHARE_NAME)

    def test_allow_access(self):

        self.helper.allow_access(self.mock_context, fake.CIFS_SHARE,
                                 fake.ACCESS)

        self.mock_client.add_cifs_share_access.assert_called_once_with(
            fake.SHARE_NAME, fake.ACCESS['access_to'])

    def test_allow_access_preexisting(self):

        self.mock_client.add_cifs_share_access.side_effect = \
            netapp_api.NaApiError(code=netapp_api.EDUPLICATEENTRY)

        self.assertRaises(exception.ShareAccessExists,
                          self.helper.allow_access,
                          self.mock_context,
                          fake.CIFS_SHARE,
                          fake.ACCESS)

    def test_allow_access_api_error(self):

        self.mock_client.add_cifs_share_access.side_effect = \
            netapp_api.NaApiError()

        self.assertRaises(netapp_api.NaApiError,
                          self.helper.allow_access,
                          self.mock_context,
                          fake.CIFS_SHARE,
                          fake.ACCESS)

    def test_allow_access_invalid_type(self):

        fake_access = fake.ACCESS.copy()
        fake_access['access_type'] = 'group'
        self.assertRaises(exception.NetAppException,
                          self.helper.allow_access,
                          self.mock_context,
                          fake.CIFS_SHARE,
                          fake_access)

    def test_deny_access(self):

        self.helper.deny_access(self.mock_context, fake.CIFS_SHARE,
                                fake.ACCESS)

        self.mock_client.remove_cifs_share_access.assert_called_once_with(
            fake.SHARE_NAME, fake.ACCESS['access_to'])

    def test_deny_access_nonexistent_user(self):

        self.mock_client.remove_cifs_share_access.side_effect = \
            netapp_api.NaApiError(code=netapp_api.EONTAPI_EINVAL)

        self.helper.deny_access(self.mock_context, fake.CIFS_SHARE,
                                fake.ACCESS)

        self.mock_client.remove_cifs_share_access.assert_called_once_with(
            fake.SHARE_NAME, fake.ACCESS['access_to'])
        self.assertEqual(1, cifs_cmode.LOG.error.call_count)

    def test_deny_access_nonexistent_rule(self):

        self.mock_client.remove_cifs_share_access.side_effect = \
            netapp_api.NaApiError(code=netapp_api.EOBJECTNOTFOUND)

        self.helper.deny_access(self.mock_context, fake.CIFS_SHARE,
                                fake.ACCESS)

        self.mock_client.remove_cifs_share_access.assert_called_once_with(
            fake.SHARE_NAME, fake.ACCESS['access_to'])
        self.assertEqual(1, cifs_cmode.LOG.error.call_count)

    def test_deny_access_api_error(self):

        self.mock_client.remove_cifs_share_access.side_effect = \
            netapp_api.NaApiError()

        self.assertRaises(netapp_api.NaApiError,
                          self.helper.deny_access,
                          self.mock_context,
                          fake.CIFS_SHARE,
                          fake.ACCESS)

    def test_get_target(self):

        target = self.helper.get_target(fake.CIFS_SHARE)
        self.assertEqual(fake.SHARE_ADDRESS, target)

    def test_get_target_missing_location(self):

        target = self.helper.get_target({'export_location': ''})
        self.assertEqual('', target)

    def test_get_export_location(self):

        host_ip, share_name = self.helper._get_export_location(fake.CIFS_SHARE)
        self.assertEqual(fake.SHARE_ADDRESS, host_ip)
        self.assertEqual(fake.SHARE_NAME, share_name)

    def test_get_export_location_missing_location(self):

        fake_share = fake.CIFS_SHARE.copy()
        fake_share['export_location'] = ''

        host_ip, share_name = self.helper._get_export_location(fake_share)

        self.assertEqual('', host_ip)
        self.assertEqual('', share_name)