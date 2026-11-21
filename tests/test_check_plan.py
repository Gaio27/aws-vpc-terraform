import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import check_plan as cp  # noqa: E402


def res(address, type_, values):
    return {"address": address, "type": type_, "values": values}


def subnet(name, cidr, az, public):
    return res(
        f"aws_subnet.{name}",
        "aws_subnet",
        {
            "cidr_block": cidr,
            "availability_zone": az,
            "map_public_ip_on_launch": public,
            "tags": {"Name": name},
        },
    )


def valid_plan():
    resources = [
        res("aws_vpc.main", "aws_vpc", {"cidr_block": "10.20.0.0/16", "tags": {"Name": "vpc-prod"}}),
        subnet("publik-a", "10.20.0.0/24", "ap-southeast-1a", True),
        subnet("publik-b", "10.20.1.0/24", "ap-southeast-1b", True),
        subnet("privat-app-a", "10.20.10.0/24", "ap-southeast-1a", False),
        subnet("privat-app-b", "10.20.11.0/24", "ap-southeast-1b", False),
        subnet("privat-data-a", "10.20.20.0/24", "ap-southeast-1a", False),
        subnet("privat-data-b", "10.20.21.0/24", "ap-southeast-1b", False),
        res("aws_internet_gateway.main", "aws_internet_gateway", {}),
        res("aws_nat_gateway.nat[\"publik-a\"]", "aws_nat_gateway", {}),
        res("aws_nat_gateway.nat[\"publik-b\"]", "aws_nat_gateway", {}),
        res(
            "aws_security_group.lb",
            "aws_security_group",
            {
                "name": "sg-lb",
                "ingress": [{"from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]}],
            },
        ),
        res(
            "aws_security_group.app",
            "aws_security_group",
            {
                "name": "sg-app",
                "ingress": [{"from_port": 8080, "to_port": 8080, "cidr_blocks": []}],
            },
        ),
    ]
    return {"planned_values": {"root_module": {"resources": resources, "child_modules": []}}}


def resources_of(plan):
    return plan["planned_values"]["root_module"]["resources"]


def by_name(plan, name):
    return next(r for r in resources_of(plan) if r["values"].get("tags", {}).get("Name") == name)


def test_valid_plan_has_no_problems():
    assert cp.check_plan(valid_plan()) == []


def test_detects_overlapping_subnets():
    plan = valid_plan()
    by_name(plan, "privat-app-b")["values"]["cidr_block"] = "10.20.10.128/25"
    problems = cp.check_plan(plan)
    assert any("tumpang tindih" in p for p in problems)


def test_detects_subnet_outside_vpc():
    plan = valid_plan()
    by_name(plan, "privat-data-b")["values"]["cidr_block"] = "192.168.50.0/24"
    problems = cp.check_plan(plan)
    assert any("di luar VPC" in p for p in problems)


def test_detects_public_subnet_without_public_ip():
    plan = valid_plan()
    by_name(plan, "publik-a")["values"]["map_public_ip_on_launch"] = False
    problems = cp.check_plan(plan)
    assert any("publik harus memberi IP publik" in p for p in problems)


def test_detects_private_subnet_with_public_ip():
    plan = valid_plan()
    by_name(plan, "privat-app-a")["values"]["map_public_ip_on_launch"] = True
    problems = cp.check_plan(plan)
    assert any("privat tidak boleh" in p for p in problems)


def test_detects_single_az():
    plan = valid_plan()
    for name in ("publik-b", "privat-app-b", "privat-data-b"):
        by_name(plan, name)["values"]["availability_zone"] = "ap-southeast-1a"
    problems = cp.check_plan(plan)
    assert any("2 AZ" in p for p in problems)


def test_detects_missing_nat_gateway():
    plan = valid_plan()
    plan["planned_values"]["root_module"]["resources"] = [
        r for r in resources_of(plan) if r["type"] != "aws_nat_gateway"
    ][:]
    problems = cp.check_plan(plan)
    assert any("NAT gateway" in p for p in problems)


def test_detects_ssh_open_to_internet():
    plan = valid_plan()
    sg = next(r for r in resources_of(plan) if r["address"] == "aws_security_group.app")
    sg["values"]["ingress"].append({"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]})
    problems = cp.check_plan(plan)
    assert any("22-22" in p and "terbuka ke internet" in p for p in problems)


def test_detects_missing_vpc():
    plan = copy.deepcopy(valid_plan())
    plan["planned_values"]["root_module"]["resources"] = [
        r for r in resources_of(plan) if r["type"] != "aws_vpc"
    ]
    problems = cp.check_plan(plan)
    assert problems and "aws_vpc" in problems[0]


def test_walks_child_modules():
    plan = valid_plan()
    root = plan["planned_values"]["root_module"]
    child_resources = [r for r in root["resources"] if r["type"] == "aws_subnet"]
    root["resources"] = [r for r in root["resources"] if r["type"] != "aws_subnet"]
    root["child_modules"] = [{"resources": child_resources, "child_modules": []}]
    assert cp.check_plan(plan) == []
