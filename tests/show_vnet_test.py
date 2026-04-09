import os
from click.testing import CliRunner
from utilities_common.db import Db
import show.main as show
import show.vnet as vnet

class TestShowVnetRoutesAll(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_Preety_print(self):
        table =[]
        row = ["Vnet_v6_in_v6-0", "fddd:a156:a251::a6:1/128"]
        mac_addr = ""
        vni = ""
        state = "active"
        epval = "fddd:a100:a251::a10:1,fddd:a101:a251::a10:1"

        vnet.pretty_print(table, row, epval, mac_addr, vni, state)
        expected_output = [['Vnet_v6_in_v6-0', 'fddd:a156:a251::a6:1/128', 'fddd:a100:a251::a10:1,fddd:a101:a251::a10:1', '', '', 'active']]
        assert table == expected_output

        table =[]
        row = ["Vnet_v6_in_v6-0", "fddd:a156:a251::a6:1/128"]
        epval = "fddd:a100:a251::a10:1,fddd:a101:a251::a10:1,fddd:a100:a251::a11:1,fddd:a100:a251::a12:1,fddd:a100:a251::a13:1"
        vnet.pretty_print(table, row, epval, mac_addr, vni, state)
        expected_output = [
            ['Vnet_v6_in_v6-0', 'fddd:a156:a251::a6:1/128', 'fddd:a100:a251::a10:1,fddd:a101:a251::a10:1', '', '', 'active'],
            ['',                '',                         'fddd:a100:a251::a11:1,fddd:a100:a251::a12:1', '', '', ''],
            ['',                '',                         'fddd:a100:a251::a13:1',                       '', '', '']
        ]
        assert table == expected_output

        table =[]
        row = ["Vnet_v6_in_v6-0", "fddd:a156:a251::a6:1/128"]
        epval = "192.168.1.1,192.168.1.2,192.168.1.3,192.168.1.4,192.168.1.5,192.168.1.6,192.168.1.7,192.168.1.8,192.168.1.9,192.168.1.10,192.168.1.11,192.168.1.12,192.168.1.13,192.168.1.14,192.168.1.15"
        vnet.pretty_print(table, row, epval, mac_addr, vni, state)
        expected_output =[
            ['Vnet_v6_in_v6-0', 'fddd:a156:a251::a6:1/128', '192.168.1.1,192.168.1.2,192.168.1.3',    '', '', 'active'],
            ['',                '',                         '192.168.1.4,192.168.1.5,192.168.1.6',    '', '', ''],
            ['',                '',                         '192.168.1.7,192.168.1.8,192.168.1.9',    '', '', ''],
            ['',                '',                         '192.168.1.10,192.168.1.11,192.168.1.12', '', '', ''],
            ['',                '',                         '192.168.1.13,192.168.1.14,192.168.1.15', '', '', '']]
        assert table == expected_output

        table =[]
        row = ["Vnet_v6_in_v6-0", "fddd:a156:a251::a6:1/128"]
        epval = "192.168.1.1"
        vnet.pretty_print(table, row, epval, mac_addr, vni, state)
        expected_output =[
            ['Vnet_v6_in_v6-0', 'fddd:a156:a251::a6:1/128', '192.168.1.1', '', '', 'active']]
        assert table == expected_output

    def test_pretty_print_mac_vni_aligned(self):
        """Each endpoint must appear on its own row with its matching mac and vni."""
        table = []
        row = ["Vnet1", "10.0.0.0/24"]
        epval    = "100.1.1.1,100.1.1.2,100.1.1.3"
        mac_addr = "aa:bb:cc:dd:ee:01,aa:bb:cc:dd:ee:02,aa:bb:cc:dd:ee:03"
        vni      = "1001,1002,1003"
        state    = "active"

        vnet.pretty_print(table, row, epval, mac_addr, vni, state)

        # every row must have exactly 6 columns
        for r in table:
            assert len(r) == 6, f"row has wrong column count: {r}"

        # first row carries vnet/prefix/state, continuation rows blank them
        assert table[0][0] == "Vnet1"
        assert table[0][5] == "active"
        for r in table[1:]:
            assert r[0] == ""
            assert r[5] == ""

        # mac and vni on each row must correspond to the endpoint on that row
        for r in table:
            ep_chunk  = r[2].split(',')
            mac_chunk = r[3].split(',') if r[3] else []
            vni_chunk = r[4].split(',') if r[4] else []
            assert len(ep_chunk) == len(mac_chunk) or r[3] == ""
            assert len(ep_chunk) == len(vni_chunk) or r[4] == ""

    def test_pretty_print_mac_longer_than_endpoint(self):
        """row_width must be determined by the longest field, not just endpoint."""
        table = []
        row = ["Vnet1", "10.0.0.0/24"]
        # short endpoints but long mac addresses — mac drives row_width
        epval    = "1.1.1.1,2.2.2.2,3.3.3.3,4.4.4.4,5.5.5.5"
        mac_addr = "aa:bb:cc:dd:ee:01,aa:bb:cc:dd:ee:02,aa:bb:cc:dd:ee:03,aa:bb:cc:dd:ee:04,aa:bb:cc:dd:ee:05"
        vni      = "100,200,300,400,500"
        state    = "active"

        vnet.pretty_print(table, row, epval, mac_addr, vni, state)

        # all rows must have 6 columns and be non-empty
        assert len(table) >= 1
        for r in table:
            assert len(r) == 6

        # first-row / continuation-row invariants
        assert table[0][0] == "Vnet1"
        assert table[0][5] == "active"
        for r in table[1:]:
            assert r[0] == ""
            assert r[5] == ""

    def test_pretty_print_missing_mac_vni(self):
        """Missing mac/vni must be padded with empty strings, not crash."""
        table = []
        row = ["Vnet1", "10.0.0.0/24"]
        epval    = "100.1.1.1,100.1.1.2,100.1.1.3"
        mac_addr = None
        vni      = None
        state    = "active"

        vnet.pretty_print(table, row, epval, mac_addr, vni, state)

        assert len(table) >= 1
        for r in table:
            assert len(r) == 6

    def test_show_vnet_routes_all_basic(self):
        runner = CliRunner()
        db = Db()
        
        result = runner.invoke(show.cli.commands['vnet'].commands['routes'].commands['all'], [], obj=db)
        assert result.exit_code == 0
        expected_output = """\
vnet name        prefix            nexthop                                interface
---------------  ----------------  -------------------------------------  -------------------------------
test_v4_in_v4-0  160.162.191.1/32  100.100.4.1                            Ethernet1
test_v4_in_v4-0  160.163.191.1/32  100.101.4.1, 100.101.4.2               Ethernet1, Ethernet2
test_v4_in_v4-0  160.164.191.1/32  100.102.4.1, 100.102.4.2, 100.102.4.3  Ethernet1, Ethernet2, Ethernet3
test_v4_in_v4-1  160.165.191.1/32  100.103.4.1, 100.103.4.2, 100.103.4.3  Ethernet1, Ethernet2, Ethernet3

vnet name        prefix                    endpoint                                     mac address    vni    status      metric
---------------  ------------------------  -------------------------------------------  -------------  -----  --------  --------
Vnet_v6_in_v6-0  fddd:a156:a251::a6:1/128  fddd:a100:a251::a10:1,fddd:a101:a251::a10:1                        active
                                           fddd:a102:a251::a10:1,fddd:a103:a251::a10:1
test_v4_in_v4-0  160.162.191.1/32          100.251.7.1                                                        active
test_v4_in_v4-0  160.163.191.1/32          100.251.7.1                                                        active           0
test_v4_in_v4-0  160.164.191.1/32          100.251.7.1
"""
        assert result.output == expected_output

    def test_show_vnet_routes_all_vnetname(self):
        runner = CliRunner()
        db = Db()
        
        result = runner.invoke(show.cli.commands['vnet'].commands['routes'].commands['all'], ['test_v4_in_v4-0'], obj=db)
        assert result.exit_code == 0
        expected_output = """\
vnet name        prefix            nexthop                                interface
---------------  ----------------  -------------------------------------  -------------------------------
test_v4_in_v4-0  160.162.191.1/32  100.100.4.1                            Ethernet1
test_v4_in_v4-0  160.163.191.1/32  100.101.4.1, 100.101.4.2               Ethernet1, Ethernet2
test_v4_in_v4-0  160.164.191.1/32  100.102.4.1, 100.102.4.2, 100.102.4.3  Ethernet1, Ethernet2, Ethernet3

vnet name        prefix            endpoint     mac address    vni    status      metric
---------------  ----------------  -----------  -------------  -----  --------  --------
test_v4_in_v4-0  160.162.191.1/32  100.251.7.1                        active
test_v4_in_v4-0  160.163.191.1/32  100.251.7.1                        active           0
test_v4_in_v4-0  160.164.191.1/32  100.251.7.1
"""
        assert result.output == expected_output

    def test_show_vnet_routes_tunnel_basic(self):
        runner = CliRunner()
        db = Db()
        
        result = runner.invoke(show.cli.commands['vnet'].commands['routes'].commands['tunnel'], [], obj=db)
        assert result.exit_code == 0
        expected_output = """\
vnet name        prefix                    endpoint                                                                                 mac address    vni      metric
---------------  ------------------------  ---------------------------------------------------------------------------------------  -------------  -----  --------
Vnet_v6_in_v6-0  fddd:a156:a251::a6:1/128  fddd:a100:a251::a10:1,fddd:a101:a251::a10:1,fddd:a102:a251::a10:1,fddd:a103:a251::a10:1
test_v4_in_v4-0  160.162.191.1/32          100.251.7.1
test_v4_in_v4-0  160.163.191.1/32          100.251.7.1                                                                                                           0
test_v4_in_v4-0  160.164.191.1/32          100.251.7.1
"""
        assert result.output == expected_output

    def test_show_vnet_routes_local_basic(self):
        runner = CliRunner()
        db = Db()
        
        result = runner.invoke(show.cli.commands['vnet'].commands['routes'].commands['local'], [], obj=db)
        assert result.exit_code == 0
        expected_output = """\
vnet name        prefix            nexthop                                interface
---------------  ----------------  -------------------------------------  -------------------------------
test_v4_in_v4-0  160.162.191.1/32  100.100.4.1                            Ethernet1
test_v4_in_v4-0  160.163.191.1/32  100.101.4.1, 100.101.4.2               Ethernet1, Ethernet2
test_v4_in_v4-0  160.164.191.1/32  100.102.4.1, 100.102.4.2, 100.102.4.3  Ethernet1, Ethernet2, Ethernet3
test_v4_in_v4-1  160.165.191.1/32  100.103.4.1, 100.103.4.2, 100.103.4.3  Ethernet1, Ethernet2, Ethernet3
"""
        assert result.output == expected_output

class TestShowVnetAdvertisedRoutesIPX(object):
    @classmethod
    def setup_class(cls):
        print("SETUP")
        os.environ["UTILITIES_UNIT_TESTING"] = "1"

    def test_show_vnet_adv_routes_ip_basic(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands['vnet'].commands['advertised-routes'], [], obj=db)
        assert result.exit_code == 0
        expected_output = """\
Prefix                    Profile              Community Id
------------------------  -------------------  --------------
160.62.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
160.63.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
160.64.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
fccc:a250:a251::a6:1/128
fddd:a150:a251::a6:1/128  FROM_SDN_SLB_ROUTES  1234:1235
"""
        assert result.output == expected_output

    def test_show_vnet_adv_routes_ip_string(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands['vnet'].commands['advertised-routes'], ['1234:1235'], obj=db)
        assert result.exit_code == 0
        expected_output = """\
Prefix                    Profile              Community Id
------------------------  -------------------  --------------
160.62.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
160.63.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
160.64.191.1/32           FROM_SDN_SLB_ROUTES  1234:1235
fddd:a150:a251::a6:1/128  FROM_SDN_SLB_ROUTES  1234:1235
"""
        assert result.output == expected_output

    def test_show_vnet_adv_routes_ipv6_Error(self):
        runner = CliRunner()
        db = Db()
        result = runner.invoke(show.cli.commands['vnet'].commands['advertised-routes'], ['1230:1235'], obj=db)
        assert result.exit_code == 0
        expected_output = """\
Prefix    Profile    Community Id
--------  ---------  --------------
"""
        assert result.output == expected_output
