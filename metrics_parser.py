import json
import numpy as np
import matplotlib.pyplot as plt
import time

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

def summary_statistics(title, final_client_metrics, metrics, verify):
    file_name = "summary_" + time.ctime().replace(" ", "_").replace(":", "_")
    open(file_name, "x") # create file, error if already exists
    def log_and_print(str):
        with open(file_name, "a") as outfile:
            if "\n" in str:
                outfile.write(str)
            else:
                outfile.write(str + "\n")
        print(str, flush=True)

    log_and_print("============ Summary Statistics ============")
    log_and_print(title)
    # Sanity checking:
    if verify:
        for agent in final_client_metrics["agents"]:
            seen_payloads = set()
            for payload_dict in agent["received_payloads"]:
                unique_tuple = (payload_dict["drop_id"], payload_dict["creation_timestamp"])
                if unique_tuple in seen_payloads:
                    log_and_print("INVARIANT VIOLATION dupe payload:", unique_tuple[0], unique_tuple[1])
                else:
                    seen_payloads.add(unique_tuple)

    # Metric 0 
    # Average payload delivery latency
    num_payloads_recv = agg_metric_for_agents(final_client_metrics["agents"], "total_pay_recv_from_router", "sum")
    total_payload_latency = agg_metric_for_agents(final_client_metrics["agents"], "pay_recv_latencies", "sum_array")
    if num_payloads_recv > 0:
        avg_payload_latency = total_payload_latency / num_payloads_recv
        log_and_print("Average payload delivery latency: {} ticks".format(avg_payload_latency))
    else:
        log_and_print("Average payload delivery latency: N/A (no payloads were delivered)")

    # Metric 1
    # Payload delivery success rate
    num_payloads_recv = agg_metric_for_agents(final_client_metrics["agents"], "total_pay_recv_from_router", "sum")
    num_payloads_picked_up = agg_metric_for_agents(final_client_metrics["agents"], "total_drops_picked_up_from_ground", "sum")
    if num_payloads_picked_up > 0:
        payload_delivery_success_rate = num_payloads_recv / num_payloads_picked_up
        log_and_print("Payload delivery success rate: {}%".format(payload_delivery_success_rate * 100))
    else:
        log_and_print("Payload delivery success rate: N/A (no payloads were picked up)")

    # Metric 2
    # Average bundle storage overhead
    total_bundles_stored = metrics["total_bundles_stored_so_far"]
    avg_bundle_storage_overhead = total_bundles_stored / metrics["num_steps"]
    log_and_print("Average bundle storage overhead: {}".format(avg_bundle_storage_overhead))


if __name__ == "__main__":
    metrics = json.load(open("metrics.json", "r"))
    metrics_to_plot = [
        ("routing_protocol.total_bundle_sends", "sum"),
        ("routing_protocol.curr_num_stored_bundles", "sum"),
        ("curr_num_stored_payloads", "mean"),
        ("total_pay_recv_from_router", "sum")
    ]

    parse_and_plot(metrics, metrics_to_plot)