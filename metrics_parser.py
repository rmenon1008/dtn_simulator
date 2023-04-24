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

    if agg == "sum":
        return sum(metric_vals)
    elif agg == "ave":
        return sum(metric_vals) / agent_num
    elif agg == "min":
        return min(metric_vals)
    elif agg == "max":
        return max(metric_vals)
    

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

def __main__():
    metrics = json.load(open("metrics.json", "r"))
    metrics_to_plot = [
        ("agent.client_agent.ClientAgent.num_data_drops", "sum"),
        ("agent.client_agent.ClientAgent.num_data_drops", "mean"),
        ("agent.client_agent.ClientAgent.num_data_drops", "min"),
        ("agent.client_agent.ClientAgent.num_data_drops", "max"),
    ]

    parse_and_plot(metrics, metrics_to_plot)