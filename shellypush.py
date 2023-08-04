#!/usr/bin/env python3

import click
import requests
import json
from pprint import pprint

@click.command()
@click.option('--shelly-url', default='http://192.168.33.1', help='HTTP or HTTPS url to Shelly Plug endpoint')
@click.option('--shelly-gen', default='1', help='API/Device generation.')
@click.option('--shelly-user', default=None, help='Username for authentication.')
@click.option('--shelly-password', default=None, help='Password for authentication.')
@click.option('--push-url', default='http://localhost:9091',  help='Push Gateway URL.')
@click.option('--push-job', default='shelly', help='Push Gateway job to attach metrics to.')
@click.option('--push-suffix', default='metrics', help='Push Gateway job to attach metrics to.')
def main(shelly_url, shelly_gen, shelly_user, shelly_password, push_url, push_job, push_suffix):
    r = requests.get("{}/{}".format(shelly_url, "status"))
    if r.status_code != 200:
        print("Couldn't get Shelly Plug status")
        exit(1)
    data = json.loads(r.text)
    body = ""
    labels = "mac=\"{}\",overtemperature=\"{}\"".format(
        data["mac"], 1 if data["overtemperature"] else 0,
        data["temperature"]
    )
    body = add_metric(
        body, "shelly_temperature",
        "Temperature of the shelly plug.", "GAUGE", labels,
        data["temperature"]
    )
    for i, m in enumerate(data["meters"]):
        labels = "mac=\"{}\",is_valid=\"{}\"".format(
            data["mac"],
            1 if m["is_valid"] else 0
        )
        body = add_metric(
            body, "shelly_meter_{}_power".format(i),
            "Power measurement for meter {}, in Watts".format(i), "GAUGE",
            labels, m["power"]
        )
        body = add_metric(
            body, "shelly_meter_{}_overpower".format(i),
            "Overpower for meter {}".format(i), "GAUGE",
            labels, m["overpower"]
        )
        body = add_metric(
            body, "shelly_meter_{}_total".format(i),
            "Total energy consumed seen by meter {}, in Watt-minute".format(i), "GAUGE",
            labels, m["total"]
        )
    print(body)
    p = requests.post("{}/{}/job/{}/mac/{}".format(push_url, push_suffix, push_job, data["mac"]), data=body, verify=False)
    print("Response : {} {}".format(p, p.text))

def add_metric(body, name, description, metric_type, labels, value):
    body += "# HELP {} {}\n \
# TYPE {} {}\n \
{}[{}] {}\n".format(name, description, name, metric_type, name, labels, value).replace('[', '{').replace(']', '}')
    return body

if __name__ == '__main__':
    main()