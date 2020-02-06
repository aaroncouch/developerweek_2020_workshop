# File: scouter_ping.py
# Written By: Aaron Couch
# Contributions By:
# Date: 2020-01-29
# Updated On: 2020-02-06
# Python Version: 3.7.3
# pylint: disable=locally-disabled, missing-docstring

import sys
import json
import time
import argparse
import multiprocessing
import requests

SP_API_BASE_URL = "https://gateway.stackpath.com"


class PingClient:
    def __init__(self, client_credentials, account_data, scouter_data):
        self._workload_instances = self._get_workload_instances(client_credentials, account_data)
        self._scouter_secret = scouter_data[0]
        self._scouter_port = scouter_data[1]
        self._dst = None

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
            PingClient._api_error_handler(
                f"Failed to generate an SP2.0 API token. Error: {str(error)}", response.json()
            )
        return api_token

    @staticmethod
    def _get_workload_instances(client_credentials, account_data):
        instances = {}
        api_token = PingClient._get_api_token(client_credentials)
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
                PingClient._api_error_handler(
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
        return data["results"]

    def _mp_ping_worker(self, instance):
        src_ip = self._workload_instances[instance]["ip_addr"]
        url = f"http://{src_ip}:{self._scouter_port}/api/v1.0/tests"
        payload = {"ping": []}
        for dst in self._dst:
            payload["ping"].append({"dst": dst, "count": 5})
        results = self._scouter_api_handler(url, payload)
        return (instance, results)

    def ping(self, dst, dst_pops):
        if dst is None:
            self._dst = []
            for value in self._workload_instances.values():
                if "all" in dst_pops or value["pop"] in dst_pops:
                    self._dst.append(value["ip_addr"])
        else:
            self._dst = dst
        mp_pool = multiprocessing.Pool(len(self._workload_instances.keys()))
        results = mp_pool.map(self._mp_ping_worker, self._workload_instances)
        mp_pool.close()
        mp_pool.join()
        return results


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


def get_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack-id", type=str, required=True)
    parser.add_argument("--workload-id", type=str, required=True)
    parser.add_argument("--client-id", type=str, required=True)
    parser.add_argument("--client-secret", type=str, required=True)
    parser.add_argument("--scouter-secret", type=str, required=True)
    parser.add_argument("--scouter-port", type=int, default=8000)
    dst_group = parser.add_mutually_exclusive_group()
    dst_group.add_argument("--dst", nargs="+")
    dst_group.add_argument("--dst-pops", nargs="+", default=["all"])
    return vars(parser.parse_args())


def main():
    cmd_args = get_cmd_args()
    public_ip = get_public_ip()
    client = PingClient(
        client_credentials=(cmd_args["client_id"], cmd_args["client_secret"]),
        account_data=(cmd_args["stack_id"], cmd_args["workload_id"]),
        scouter_data=(cmd_args["scouter_secret"], cmd_args["scouter_port"]),
    )
    nanoseconds = f"{time.time()*1000000000:.0f}"
    data = client.ping(dst=cmd_args["dst"], dst_pops=cmd_args["dst_pops"])
    for entry in data:
        src_slug = entry[0]
        src_pop = client.workload_instances[src_slug]["pop"]
        for result in entry[1]["ping"]:
            result = result["result"]
            # Set defaults.
            rtt = {}
            reply_fields = []
            failed = int(result["failed"])
            loss_pct = result["loss"]
            dst = result["dst"]
            dst_pop = "Unknown"
            avg_rtt_ms = "9999.9"
            jitter_ms = "0.0"
            jitter_pct = "100.0"
            # Check if the ping resulted in a failure; if not, update defaults.
            if not failed:
                # Average Ping RTT across all received packets in milliseconds.
                avg_rtt_ms = result["rtt"]["avg"]
                rtt = {reply["seq"]: reply["rtt_ms"] for reply in result["replies"]}
                # Calculate jitter_ms based on all rtt_ms values from the replies.
                jitter_ms = calc_jitter(list(rtt.values()))
                # Calculate jitter_pct.
                jitter_pct = (float(jitter_ms) / float(avg_rtt_ms)) * 100
            for seq in range(5):
                rtt_ms = "9999.9"
                if seq in rtt:
                    rtt_ms = rtt[seq]
                reply_fields.append(f'reply_{seq}_ms="{rtt_ms}"')
            if cmd_args["dst"] is None:
                for value in client.workload_instances.values():
                    if value["ip_addr"] == dst:
                        dst_pop = value["pop"]
            print(
                f"ping,src_slug={src_slug},src_pop={src_pop},dst={dst},dst_pop={dst_pop},"
                f'public_ip={public_ip} failed="{failed}",loss_pct="{loss_pct}",'
                f'avg_rtt="{avg_rtt_ms}",jitter_ms="{jitter_ms}",jitter_pct="{jitter_pct}",'
                f"{','.join(reply_fields)} {nanoseconds}"
            )


if __name__ == "__main__":
    main()
