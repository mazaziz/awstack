import os
import json
import time
from awstack.stack import LocalStack, Stack
from awstack.stacks import Stacks

def load_stack(opts) -> Stack:
    path = opts["--path"] or os.path.realpath(os.path.curdir)
    lstack = LocalStack.load(path)
    return Stack.load(lstack, opts["--profile"])

def watch_stack_status(stack: Stack):
    def echo(v):
        print(v, end="", flush=True)
    status, inprogress = stack.get_status()
    echo(status)
    if not inprogress:
        echo("\n")
        return status
    while inprogress:
        time.sleep(1)
        status_before = status
        status, inprogress = stack.get_status()
        if status == status_before:
            echo(".")
        else:
            echo("\n{}".format(status))
    echo("\n")
    return status

def watch_changeset_status(stack: Stack, name):
    def echo(v):
        print(v, end="", flush=True)
    status, inprogress = stack.get_changeset_status(name)
    echo(status)
    if not inprogress:
        echo("\n")
        return status
    while inprogress:
        time.sleep(1)
        status_before = status
        status, inprogress = stack.get_changeset_status(name)
        if status == status_before:
            echo(".")
        else:
            echo("\n{}".format(status))
    echo("\n")
    return status

def handle_init(opts):
    path = opts["--path"] or os.path.realpath(os.path.curdir)
    name = opts["--name"] or os.path.basename(path)
    desc = opts["--desc"] or "created by using awstack"
    lstack = LocalStack.create_skeleton(path, opts["--profile"], name, desc)
    print("OK: stack skeleton initialized in {} with name={}, profile={}".format(lstack.path, lstack.name, lstack.profile))

def handle_status(opts):
    stack = load_stack(opts)
    if opts["--watch"]:
        watch_stack_status(stack)
    else:
        print(stack.get_status()[0])

def handle_local(opts):
    path = opts["--path"] or os.path.realpath(os.path.curdir)
    template = LocalStack.load(path).get_template()
    print(json.dumps(template, indent=4))

def handle_remote(opts):
    template = load_stack(opts).get_template()
    print(json.dumps(template, indent=4))

def handle_validate(opts):
    load_stack(opts).validate()
    print("OK")

def handle_diff(opts):
    import difflib
    stack = load_stack(opts)
    diff = "\n".join(difflib.unified_diff(
        json.dumps(stack.get_template(), indent=4, sort_keys=True).splitlines(),
        json.dumps(stack.lstack.get_template(), indent=4, sort_keys=True).splitlines()
    ))
    if diff:
        print(diff)

def handle_changesets(opts):
    for item in load_stack(opts).get_changesets():
        print("{} {} [execution status: {}]".format(item["ChangeSetName"], item["Status"], item["ExecutionStatus"]))

def handle_changeset_create(opts):
    stack = load_stack(opts)
    stack.create_changeset(opts["NAME"])
    watch_changeset_status(stack, opts["NAME"])

def handle_changeset_preview(opts):
    changeset = load_stack(opts).get_changeset(opts["NAME"])
    print(json.dumps(changeset["Changes"], indent=4))

def handle_changeset_execute(opts):
    stack = load_stack(opts)
    stack.execute_changeset(opts["NAME"])
    watch_stack_status(stack)

def handle_create(opts):
    termination_protection = not opts["-t"]
    stack = load_stack(opts)
    stack.create_stack(termination_protection)
    watch_stack_status(stack)

def handle_resources(opts):
    for item in load_stack(opts).get_resources():
        print("{} {} [{}]".format(
            item["LogicalResourceId"],
            item["ResourceStatus"],
            item["ResourceType"]
        ))

def handle_outputs(opts):
    for item in load_stack(opts).get_outputs():
        print("{} = {}{}".format(
            item["OutputKey"], 
            item["OutputValue"],
            "" if "ExportName" not in item else " [{}]".format(item["ExportName"])
        ))

def handle_account_stacks(opts):
    for item in Stacks.load(opts["--profile"]).get_stacks():
        print("{} {}".format(item["StackName"], item["StackStatus"]))

def handle_account_exports(opts):
    for item in Stacks.load(opts["--profile"]).get_exports():
        print("{} = {}".format(item["Name"], item["Value"]))
