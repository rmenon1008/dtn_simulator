import json
import numpy as np
import matplotlib.pyplot as plt
import time
import os
from random import randint

def agg_metric_for_agents(agents, key, agg):
    """
    Aggregates a metric for a list of agents.

    agents: list of agent dicts
    key: string of nested keys separated by periods
    agg: string of aggregation function to use (sum, ave, max, min)
    """
    agent_num = len(agents)
    metric_vals = []
    
    key = key.split(".")
    for agent in agents:
        val = agent
        for k in key:
            if k not in val:
                break
            val = val[k]
        else:
            metric_vals.append(val)

    if len(metric_vals) == 0:
        return None

    if agg == "sum":
        return sum(metric_vals)
    elif agg == "ave":
        return sum(metric_vals) / agent_num
    elif agg == "min":
        return min(metric_vals)
    elif agg == "max":
        return max(metric_vals)
    elif agg == "sum_array":
        return sum(sum(x) for x in metric_vals)
    

def parse_and_plot(metrics, metrics_to_plot):
    """
    Parses metrics and plots them.

    metrics: list of metrics dicts
    metrics_to_plot: list of tuples of (metric_key, agg_func)
    """

    plt.figure(figsize=(12,5))

    for key, agg in metrics_to_plot:
        metric_vals = [agg_metric_for_agents(entry["agents"], key, agg) for entry in metrics]
        plt.plot(metric_vals, label="{} ({})".format(key, agg))

    plt.xlabel("Step")
    plt.legend()
    plt.savefig("plotted_metrics.png")

def summary_statistics(final_client_metrics, metrics, verify):
    # Sanity checking:
    if verify:
        for agent in final_client_metrics["agents"]:
            seen_payloads = set()
            for payload_dict in agent["received_payloads"]:
                unique_tuple = (payload_dict["drop_id"], payload_dict["creation_timestamp"])
                if unique_tuple in seen_payloads:
                    print("INVARIANT VIOLATION dupe payload:", unique_tuple[0], unique_tuple[1])
                else:
                    seen_payloads.add(unique_tuple)

    # Metric 0 
    # Average payload delivery latency
    num_payloads_recv = agg_metric_for_agents(final_client_metrics["agents"], "total_pay_recv_from_router", "sum")
    total_payload_latency = agg_metric_for_agents(final_client_metrics["agents"], "pay_recv_latencies", "sum_array")
    avg_payload_latency = None
    if num_payloads_recv > 0:
        avg_payload_latency = total_payload_latency / num_payloads_recv
    # Metric 1
    # Payload delivery success rate
    num_payloads_recv = agg_metric_for_agents(final_client_metrics["agents"], "total_pay_recv_from_router", "sum")
    num_payloads_picked_up = agg_metric_for_agents(final_client_metrics["agents"], "total_drops_picked_up_from_ground", "sum")
    payload_delivery_success_rate = None
    if num_payloads_picked_up > 0:
        payload_delivery_success_rate = (num_payloads_recv / num_payloads_picked_up) * 100

    # Metric 2
    # Average bundle storage overhead
    total_bundles_stored = metrics["total_bundles_stored_so_far"]
    avg_bundle_storage_overhead = total_bundles_stored / metrics["num_steps"]
    return (avg_payload_latency, payload_delivery_success_rate, avg_bundle_storage_overhead)


if __name__ == "__main__":
    metrics = json.load(open("metrics.json", "r"))
    metrics_to_plot = [
        ("routing_protocol.total_bundle_sends", "sum"),
        ("routing_protocol.curr_num_stored_bundles", "sum"),
        ("curr_num_stored_payloads", "mean"),
        ("total_pay_recv_from_router", "sum")
    ]

    parse_and_plot(metrics, metrics_to_plot)