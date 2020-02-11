# File: scouter_client.py
# Written By: Aaron Couch
# Contributions By:
# Date: 2020-02-06
# Updated On: 2020-02-10
# Python Version: 3.7.3
# pylint: disable=locally-disabled, missing-docstring

import sys
import json
import time
import argparse
import multiprocessing
import requests

SP_API_BASE_URL = "https://gateway.stackpath.com"


class Scouter:
    def __init__(self, client_credentials, account_data, scouter_data):
        self._workload_instances = self._get_workload_instances(client_credentials, account_data)
        self._scouter_secret = scouter_data[0]
        self._scouter_port = scouter_data[1]
        self._dst = None
        self._utility = None

    @property
    def workload_instances(self):
        return self._workload_instances

    @staticmethod
    def _api_error_handler(message, response_json):
        if response_json:
            print(f"{message} Response: {json.dumps(response_json)}")
        else:
            print(message)
        sys.exit(1)

    @staticmethod
    def _get_api_token(client_credentials):
        url = f"{SP_API_BASE_URL}/identity/v1/oauth2/token"
        payload = {"grant_type": "client_credentials"}
        try:
            response = requests.post(url, data=payload, auth=client_credentials)
            response.raise_for_status()
            data = response.json()
            api_token = data["access_token"]
        except requests.exceptions.RequestException as error:
            Scouter._api_error_handler(
                f"Failed to generate an StackPath API token. Error: {str(error)}", response.json()
            )
        return api_token

    @staticmethod
    def _get_workload_instances(client_credentials, account_data):
        instances = {}
        api_token = Scouter._get_api_token(client_credentials)
        headers = {"Accept": "application/json", "Authorization": f"Bearer {api_token}"}
        endpoint = f"/workload/v1/stacks/{account_data[0]}/workloads/{account_data[1]}/instances"
        base_url = f"{SP_API_BASE_URL}{endpoint}"
        has_next_page = True
        data = None
        while has_next_page:
            url = base_url
            if data is not None:
                end_cursor = data["pageInfo"]["endCursor"]  # pylint: disable=unsubscriptable-object
                url = f"{base_url}?page_request.after={end_cursor}"
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                for instance in data["results"]:
                    if instance["phase"].lower() == "running":
                        instances[instance["name"]] = {
                            "ip_addr": instance["externalIpAddress"],
                            "pop": instance["location"]["cityCode"].lower(),
                        }
                has_next_page = data["pageInfo"]["hasNextPage"]
            except requests.exceptions.RequestException as error:
                Scouter._api_error_handler(
                    f"Failed to get workload instances. Error: {str(error)}", response.json()
                )
        return instances

    def _scouter_api_handler(self, url, payload):
        headers = {"Authorization": self._scouter_secret, "Content-Type": "application/json"}
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as error:
            if response.json():
                return response.json()
            return str(error)
        receipt = data["receipt"]
        url = f"{url}?receipt={receipt}"
        is_running = True
        while is_running:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                is_running = data["is_running"]
            except requests.exceptions.RequestException as error:
                if response.json():
                    return response.json()
                return str(error)
            time.sleep(1)
        return data["results"]

    def _mp_worker(self, instance):
        src_ip = self._workload_instances[instance]["ip_addr"]
        url = f"http://{src_ip}:{self._scouter_port}/api/v1.0/tests"
        if self._utility == "ping":
            payload = {"ping": []}
            for dst in self._dst:
                payload["ping"].append({"dst": dst, "count": 5})
        elif self._utility == "traceroute":
            payload = {"traceroute": []}
            for dst in self._dst:
                payload["traceroute"].append({"dst": dst})
        results = self._scouter_api_handler(url, payload)
        return (instance, results)

    def run(self, dst, dst_pops, utility="ping"):
        self._utility = utility
        if dst is None:
            self._dst = []
            for value in self._workload_instances.values():
                if "all" in dst_pops or value["pop"] in dst_pops:
                    self._dst.append(value["ip_addr"])
        else:
            self._dst = dst
        mp_pool = multiprocessing.Pool(len(self._workload_instances.keys()))
        results = mp_pool.map(self._mp_worker, self._workload_instances)
        mp_pool.close()
        mp_pool.join()
        return results


def get_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack-slug", type=str, required=True)
    parser.add_argument("--workload-id", type=str, required=True)
    parser.add_argument("--client-id", type=str, required=True)
    parser.add_argument("--client-secret", type=str, required=True)
    parser.add_argument("--scouter-secret", type=str, required=True)
    parser.add_argument("--scouter-port", type=int, default=8000)
    parser.add_argument("--utility", type=str, default="ping", choices=["ping", "traceroute"])
    dst_group = parser.add_mutually_exclusive_group()
    dst_group.add_argument("--dst", nargs="+")
    dst_group.add_argument("--dst-pops", nargs="+", default=["all"])
    return vars(parser.parse_args())


def calc_jitter(latency_values):
    jitter_values = []
    for (index, latency) in enumerate(latency_values[:-1]):
        jitter_values.append(abs(latency - latency_values[index + 1]))
    return sum(jitter_values) / (len(latency_values) - 1)


def get_public_ip():
    try:
        response = requests.get("http://icanhazip.com")
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.RequestException:
        return "Unknown"


def serialize_ping_result(result):
    successful_probe_rtt_ms = {}
    data = {
        "tags": {"dst": result["dst"]},
        "fields": {
            "failed": int(result["failed"]),
            "loss_pct": result["loss"],
            "avg_rtt_ms": 0.0,
            "jitter_ms": 0.0,
            "jitter_pct": 100.0,
        },
    }
    if not result["failed"]:
        successful_probe_rtt_ms = {reply["seq"]: reply["rtt_ms"] for reply in result["replies"]}
        # ICMP will sometimes return negative RTT values. This is due to the bug reported in
        # https://github.com/secdev/scapy/issues/2277. This will be fixed in Scapy v2.4.4.
        positive_rtt_ms = [rtt_ms for rtt_ms in successful_probe_rtt_ms.values() if rtt_ms >= 0]
        data["fields"]["avg_rtt_ms"] = sum(positive_rtt_ms) / len(positive_rtt_ms)
        data["fields"]["jitter_ms"] = calc_jitter(positive_rtt_ms)
        data["fields"]["jitter_pct"] = (
            float(data["fields"]["jitter_ms"]) / float(data["fields"]["avg_rtt_ms"])
        ) * 100
    for seq in range(5):
        rtt_ms = 0.0
        if seq in successful_probe_rtt_ms:
            rtt_ms = successful_probe_rtt_ms[seq]
        data["fields"][f"probe_{seq}_rtt_ms"] = rtt_ms
    return data


def serialize_traceroute_result(result):
    hops = []
    data = {
        "tags": {"dst": result["dst"], "proto": result["proto"], "dport": result["dport"]},
        "fields": {
            "failed": int(result["failed"]),
            "final_hop_rtt_ms": 0.0,
            "final_hop_ttl": 32,
            "as_path": None,
        },
    }
    for hop in result["trace"]:
        if not hop["no_response"]:
            data["fields"]["final_hop_rtt_ms"] = hop["rtt_ms"]
            data["fields"]["final_hop_ttl"] = hop["ttl"]
            if hop["asn"]:
                hops.append(str(hop["asn"]))
            else:
                hops.append("*")
        else:
            hops.append("*")
    data["fields"]["as_path"] = " ".join(hops)
    return data


def main():
    cmd_args = get_cmd_args()
    public_ip = get_public_ip()
    client = Scouter(
        client_credentials=(cmd_args["client_id"], cmd_args["client_secret"]),
        account_data=(cmd_args["stack_slug"], cmd_args["workload_id"]),
        scouter_data=(cmd_args["scouter_secret"], cmd_args["scouter_port"]),
    )
    nanoseconds = f"{time.time()*1000000000:.0f}"
    data = client.run(
        dst=cmd_args["dst"], dst_pops=cmd_args["dst_pops"], utility=cmd_args["utility"]
    )
    for entry in data:
        src_slug = entry[0]
        src_pop = client.workload_instances[src_slug]["pop"]
        dst_pop = "Unknown"
        for (utility, results) in entry[1].items():
            for result in results:
                if utility == "ping":
                    serialized_data = serialize_ping_result(result["result"])
                elif utility == "traceroute":
                    serialized_data = serialize_traceroute_result(result["result"])
                if cmd_args["dst"] is None:
                    for value in client.workload_instances.values():
                        if value["ip_addr"] == serialized_data["tags"]["dst"]:
                            dst_pop = value["pop"]
                serialized_data["tags"]["src_slug"] = src_slug
                serialized_data["tags"]["src_pop"] = src_pop
                serialized_data["tags"]["dst_pop"] = dst_pop
                serialized_data["tags"]["public_ip"] = public_ip
                tag_str = ",".join(f"{key}={val}" for (key, val) in serialized_data["tags"].items())
                field_str = ",".join(
                    f'{key}="{val}"' for (key, val) in serialized_data["fields"].items()
                )
                print(f"{utility},{tag_str} {field_str} {nanoseconds}")


if __name__ == "__main__":
    main()
