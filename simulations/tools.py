import json

def read_contact_plan_from_json(filename):
    with open(filename, "r") as read_file:
        data = json.load(read_file)
        contacts = data["contacts"]
        return contacts
    
def get_total_contact_time(cp):
    total_time = 0
    for contact in cp:
        total_time += contact["endTime"] - contact["startTime"]
    return total_time

def get_total_num_contacts(cp):
    return len(cp)

def get_avg_contact_time(cp):
    return get_total_contact_time(cp) / get_total_num_contacts(cp)

def get_num_unique_contact_partners(cp):
    partners = set()
    for contact in cp:
        node1 = contact["source"]
        node2 = contact["dest"]
        pair = frozenset((node1, node2))
        partners.add(pair)
    return len(partners)

def get_cp_name(exp_num):
    return "simulations/scenario{0}/5000steps_cp_s{0}.json".format(exp_num)

experiment_nums = [1, 2, 3]
for i in experiment_nums:
    cp = read_contact_plan_from_json(get_cp_name(i))
    total_contact_time = get_total_contact_time(cp)
    total_num_contacts = get_total_num_contacts(cp)
    avg_contact_time = get_avg_contact_time(cp)
    num_unique_partners = get_num_unique_contact_partners(cp)

    print("Scenario", i)
    print("\tTotal Contact Time:", total_contact_time)
    print("\tTotal Num Contacts:", total_num_contacts)
    print("\tAverage Contact Time:", avg_contact_time)
    print("\tNum Unique Partners:", num_unique_partners)