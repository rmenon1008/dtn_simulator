import json
import numpy as np
import matplotlib.pyplot as plt

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


    # Model final metrics
    final_entry = metrics[-1]

    # Metric 0 
    # Average payload delivery latency
    num_payloads_recv = agg_metric_for_agents(final_entry["agents"], "total_pay_recv_from_router", "sum")
    total_payload_latency = agg_metric_for_agents(final_entry["agents"], "pay_recv_latencies", "sum_array")
    avg_payload_latency = total_payload_latency / num_payloads_recv
    print("Average payload delivery latency: {} ticks".format(avg_payload_latency))

    # Metric 1
    # Payload delivery success rate
    num_payloads_recv = agg_metric_for_agents(final_entry["agents"], "total_pay_recv_from_router", "sum")
    num_payloads_picked_up = agg_metric_for_agents(final_entry["agents"], "total_drops_picked_up_from_ground", "sum")
    payload_delivery_success_rate = num_payloads_picked_up / num_payloads_recv
    print("Payload delivery success rate: {}%".format(payload_delivery_success_rate * 100))

    # Metric 2
    # Average bundle storage overhead
    bundles_stored_at_each_step = [agg_metric_for_agents(entry["agents"], "routing_protocol.curr_num_stored_bundles", "sum") for entry in metrics]
    avg_bundle_storage_overhead = sum(bundles_stored_at_each_step) / len(bundles_stored_at_each_step)
    print("Average bundle storage overhead: {}".format(avg_bundle_storage_overhead))


if __name__ == "__main__":
    metrics = json.load(open("metrics.json", "r"))
    metrics_to_plot = [
        ("routing_protocol.total_bundle_sends", "sum"),
        ("routing_protocol.curr_num_stored_bundles", "sum"),
        ("curr_num_stored_payloads", "mean"),
        ("total_pay_recv_from_router", "sum")
    ]

    parse_and_plot(metrics, metrics_to_plot)