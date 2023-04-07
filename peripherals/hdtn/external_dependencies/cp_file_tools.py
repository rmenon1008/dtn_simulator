import csv
import json
import os
import argparse

DEFAULT_OUT_DIR = "./out/"

def read_contact_plan_from_json(filename):
    with open(filename, "r") as read_file:
        data = json.load(read_file)
        contacts = data["contacts"]
        return contacts
    
def read_contact_plan_from_csv(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        contacts = []
        for row in reader:
            contacts.append({
                "contact": int(row["contact_id"]),
                "source": row["source"],
                "dest": row["dest"],
                "startTime": int(row["startTime"]),
                "endTime": int(row["endTime"]),
                "rate": row["rate"],
                # "owlt": row["owlt"],
                # "confidence": row["confidence"],
                })
        return contacts

def csv_to_json(filename, out_dir):
    contact_plan_name = os.path.splitext(os.path.split(filename)[1])[0]
    data = {"contacts": read_contact_plan_from_csv(filename)}
    if verify_contact_plan(data["contacts"]) is not None:
        print("There are issues with this contact plan! Run with --verify to see issues")
    json_data = json.dumps(data, indent=4)
    json_file_path = os.path.join(out_dir, contact_plan_name + ".json")
    with open(json_file_path, "w") as outfile:
        outfile.write(json_data)
    print("Finished generating json file, located at %s" % json_file_path)

# Outputs
def json_to_csv(filename, out_dir):
    contact_plan_name = os.path.splitext(os.path.split(filename)[1])[0]
    csv_file_path = os.path.join(out_dir, contact_plan_name + ".csv")
    csvf = csv.writer(open(csv_file_path, "w", newline=''))
    csvf.writerow([
        "contact_id",
        "source",
        "dest",
        "startTime",
        "endTime",
        "rate",
        # "owlt",
        # "confidence"
        ])

    contacts = read_contact_plan_from_json(filename)
    if verify_contact_plan(contacts) is not None:
        print("There are issues with this contact plan! Run with --verify to see issues")
    for contact in contacts:
        csvf.writerow([
            contact["contact"],
            contact["source"],
            contact["dest"],
            contact["startTime"],
            contact["endTime"],
            contact["rate"],
            # 1, #contact["owlt"],
            # 1.0, # confidence is 1.0f
            ])
    print("Finished generating csv file, located at %s" % csv_file_path)

def verify_contact_plan(contact_plan_object, verbose=False):
    if verbose: print("Verifying contact plan...")
    counter = {"num_errors": 0, "num_warnings": 0}
    def error(counter, msg):
        counter["num_errors"] += 1
        if verbose: print("\tError: %s" % msg)
    def warning(counter, msg):
        counter["num_warnings"] += 1
        if verbose: print("\tWarning: %s" % msg)
    contact_ids = set()
    duplicate_found = False
    for contact in contact_plan_object:
        # Check for duplicate contacts
        curr_contact_id = contact["contact"]
        if curr_contact_id in contact_ids:
            error(counter, "Duplicate contact id exists! (id=%s)" % curr_contact_id)
            duplicate_found = True
        else:
            contact_ids.add(curr_contact_id)
        # Check start/end times
        start_time = contact["startTime"]
        end_time = contact["endTime"]
        if not isinstance(start_time, int):
            error(counter, "(Contact id=%s) startTime is not an int type: %s" % (curr_contact_id, start_time))
        if not isinstance(end_time, int):
            error(counter, "(Contact id=%s) endTime is not an int type: %s" % (curr_contact_id, end_time))
        if start_time > end_time:
            error(counter, "(Contact id=%s) startTime is greater than endTime: (%s > %s)" % (curr_contact_id, start_time, end_time))
        if start_time == end_time:
            warning(counter, "(Contact id=%s) startTime is equal to endTime: (%s == %s)" % (curr_contact_id, start_time, end_time))
        # If there are confidence values in the contact plan: check if within range of 0 and 1
        # TODO
    if not duplicate_found:
        if (0 in contact_ids) and (len(contact_ids) != max(contact_ids) + 1):
            warning(counter, "The # of unique contact ids (%s) does not match with the maximum contact ID found plus 1 (%s + 1) (assuming 0-indexing is used). This may indicate a missing contact." % (len(contact_ids), len(contact_plan_object)))
        if (0 not in contact_ids) and (len(contact_ids) != max(contact_ids)):
            warning(counter, "The # of unique contact ids (%s) does not match with the maximum contact ID found (%s) (assuming 1-indexing is used). This may indicate a missing contact." % (len(contact_ids), len(contact_plan_object)))
    # Done checking
    num_errors = counter["num_errors"]
    num_warnings = counter["num_warnings"]
    if num_errors + num_warnings > 0:
        if verbose: print("Issues found with contact plan:")
        if verbose: print("\t num errors=%s" % num_errors)
        if verbose: print("\t num warnings=%s" % num_warnings)
        return (counter["num_errors"], counter["num_warnings"])
    else:
        if verbose: print("Found no issues with contact plan")
        return None


def main():
    argParser = argparse.ArgumentParser(description="Helper tool to perform various actions on contact plans.")
    argParser.add_argument("file", help="File path of the contact plan")
    argParser.add_argument("--c2j", help="Convert csv contact plan file to json contact plan file", action='store_true')
    argParser.add_argument("--j2c", help="Convert csv contact plan file to json contact plan file", action='store_true')
    argParser.add_argument("--verify", help="Verify semantics of a given contact plan file (csv or json)", action='store_true')
    argParser.add_argument("--outdir", help="Directory that any new files should be sent to (ignored for --verify)")
    args = argParser.parse_args()

    arg_counter = 0
    if (args.c2j):
        arg_counter += 1
    if (args.j2c):
        arg_counter += 1
    if (args.verify):
        arg_counter += 1
    if (arg_counter != 1):
        print("Must provide only one argument out of {--c2j, --j2c, --verify}")

    if not os.access(args.file, os.R_OK):
        print("Couldn't open file: %s" % args.file)
        quit()
    
    if (args.c2j):
        outdir = args.outdir if (args.outdir is not None) else DEFAULT_OUT_DIR
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        csv_to_json(args.file, outdir)

    if (args.j2c):
        outdir = args.outdir if (args.outdir is not None) else DEFAULT_OUT_DIR
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        json_to_csv(args.file, outdir)

    if (args.verify):
        file_ext = os.path.splitext(args.file)[1]
        cp = None
        if file_ext == ".csv":
            cp = read_contact_plan_from_csv(args.file)
        elif file_ext == ".json":
            cp = read_contact_plan_from_json(args.file)
        else:
            print("unrecognized file extension: %s", args.file)
            quit()
        verify_contact_plan(cp, verbose=True)

if __name__ == "__main__":
    main()