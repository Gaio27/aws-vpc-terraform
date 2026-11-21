"""Memeriksa aturan desain VPC pada output `terraform show -json`.

Tidak memanggil AWS dan tidak membutuhkan kredensial. Cukup berikan file JSON hasil plan:

    cd terraform
    terraform plan -out rencana.tfplan
    terraform show -json rencana.tfplan > ../plan.json
    cd ..
    python3 scripts/check_plan.py plan.json
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from pathlib import Path

EXPECTED_SUBNETS = 6
EXPECTED_AZS = 2


def _resources(plan: dict, type_name: str) -> list[dict]:
    found: list[dict] = []

    def walk(module: dict) -> None:
        for r in module.get("resources", []):
            if r.get("type") == type_name:
                found.append(r)
        for child in module.get("child_modules", []):
            walk(child)

    walk(plan.get("planned_values", {}).get("root_module", {}))
    return found


def _name(resource: dict) -> str:
    values = resource.get("values", {})
    return (values.get("tags") or {}).get("Name") or resource.get("address", "?")


def check_plan(plan: dict) -> list[str]:
    """Mengembalikan daftar masalah. Daftar kosong berarti desain sesuai aturan."""
    problems: list[str] = []

    vpcs = _resources(plan, "aws_vpc")
    if len(vpcs) != 1:
        return [f"harus ada tepat 1 aws_vpc, ditemukan {len(vpcs)}"]
    vpc_net = ipaddress.IPv4Network(vpcs[0]["values"]["cidr_block"])

    subnets = _resources(plan, "aws_subnet")
    if len(subnets) != EXPECTED_SUBNETS:
        problems.append(f"harus ada {EXPECTED_SUBNETS} subnet, ditemukan {len(subnets)}")

    parsed: list[tuple[str, ipaddress.IPv4Network]] = []
    for s in subnets:
        v = s["values"]
        name = _name(s)
        net = ipaddress.IPv4Network(v["cidr_block"])
        parsed.append((name, net))

        if not net.subnet_of(vpc_net):
            problems.append(f"{name}: {net} berada di luar VPC {vpc_net}")

        if name.startswith("publik") and v.get("map_public_ip_on_launch") is not True:
            problems.append(f"{name}: subnet publik harus memberi IP publik otomatis")
        if name.startswith("privat") and v.get("map_public_ip_on_launch"):
            problems.append(f"{name}: subnet privat tidak boleh memberi IP publik otomatis")

    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            (na, a), (nb, b) = parsed[i], parsed[j]
            if a.overlaps(b):
                problems.append(f"{na} ({a}) tumpang tindih dengan {nb} ({b})")

    azs = {s["values"].get("availability_zone") for s in subnets}
    if len(azs) < EXPECTED_AZS:
        problems.append(f"subnet harus tersebar di {EXPECTED_AZS} AZ, ditemukan {len(azs)}")

    igws = _resources(plan, "aws_internet_gateway")
    if len(igws) != 1:
        problems.append(f"harus ada tepat 1 internet gateway, ditemukan {len(igws)}")

    nats = _resources(plan, "aws_nat_gateway")
    if len(nats) != EXPECTED_AZS:
        problems.append(f"harus ada {EXPECTED_AZS} NAT gateway (satu per AZ), ditemukan {len(nats)}")

    for sg in _resources(plan, "aws_security_group"):
        sg_name = sg["values"].get("name") or _name(sg)
        for rule in sg["values"].get("ingress") or []:
            cidrs = rule.get("cidr_blocks") or []
            if "0.0.0.0/0" in cidrs and not (
                rule.get("from_port") == 443 and rule.get("to_port") == 443
            ):
                problems.append(
                    f"{sg_name}: ingress {rule.get('from_port')}-{rule.get('to_port')} "
                    f"terbuka ke internet (hanya port 443 yang diizinkan)"
                )

    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Periksa desain VPC dari output terraform show -json")
    p.add_argument("plan_json", help="file JSON hasil terraform show -json")
    args = p.parse_args(argv)

    plan = json.loads(Path(args.plan_json).read_text(encoding="utf-8"))
    problems = check_plan(plan)
    if problems:
        print("GAGAL:")
        for item in problems:
            print(f"  - {item}")
        return 1
    print("OK: desain VPC sesuai aturan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
