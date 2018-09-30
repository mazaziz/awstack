"""AWS CloudFormation for humans

Usage:
  awstack -h|--help
  awstack init [-d PATH] [-p PROFILE] [-n NAME] [--desc TEXT]
  awstack local [-d PATH]
  awstack create [-t] [-d PATH] [-p PROFILE]
  awstack (status|s) [-w] [-d PATH] [-p PROFILE]
  awstack (validate|remote|diff|resources|exports|changesets|css) [-d PATH] [-p PROFILE]
  awstack (changeset|cs) NAME (create|c|preview|p|execute|e) [-d PATH] [-p PROFILE]
  awstack account (stacks|exports) [-p PROFILE]

Options:
  -h,--help             display this help
  -d,--path PATH        path to stack directory, defaults to current working directory
  -p,--profile PROFILE  named profile to use in aws session, defaults to the value in manifest
                        (you may configure named profiles using ~/.aws/config)
  -n,--name NAME        name of the stack, defaults to basename of stack path
  --desc TEXT           description about the stack
  -t                    disable stack termination protection
  -w,--watch            keep probing until stack progress completes

Commands:
  init             create an empty stack skeleton in specified path
  local            display local template
  remote           display currently active template on aws
  diff             display template's unified diff between remote and local
  create           create new stack on aws using local template
  status|s         display stack status
  validate         validate local template
  resources        display provisioned resources
  exports          display exported values
  changesets|css   display created change sets
  changeset|cs
    create|c       create change set
    preview|p      review changes before execution
    execute|e      apply the changes in corresponding change set
  account
    stacks         display all stacks in related account
    exports        display all exported values in related account
"""
import os
import docopt
import awstack.handler as handler

def main():
    opts = docopt.docopt(__doc__, help=True)
    if opts["changesets"] or opts["css"]:
        handler.handle_changesets(opts)
    elif (opts["changeset"] or opts["cs"]) and (opts["create"] or opts["c"]):
        handler.handle_changeset_create(opts)
    elif (opts["changeset"] or opts["cs"]) and (opts["preview"] or opts["p"]):
        handler.handle_changeset_preview(opts)
    elif (opts["changeset"] or opts["cs"]) and (opts["execute"] or opts["e"]):
        handler.handle_changeset_execute(opts)
    elif opts["init"]:
        handler.handle_init(opts)
    elif opts["status"] or opts["s"]:
        handler.handle_status(opts)
    elif opts["local"]:
        handler.handle_local(opts)
    elif opts["validate"]:
        handler.handle_validate(opts)
    elif opts["diff"]:
        handler.handle_diff(opts)
    elif opts["remote"]:
        handler.handle_remote(opts)
    elif opts["create"]:
        handler.handle_create(opts)
    elif opts["account"] and opts["stacks"]:
        handler.handle_account_stacks(opts)
    elif opts["account"] and opts["exports"]:
        handler.handle_account_exports(opts)
    elif opts["resources"]:
        handler.handle_resources(opts)
    elif opts["exports"]:
        handler.handle_exports(opts)
    else:
        raise Exception("unhandled command")
