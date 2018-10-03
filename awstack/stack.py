import os
import json
import glob
import re
import boto3.session

class LocalStack:
    def __init__(self, path, manifest: dict):
        self.path = path
        self.manifest = manifest

    def __getattr__(self, name):
        try:
            builder = self.__getattribute__("_attr_{}".format(name))
        except AttributeError:
            raise Exception("no builder found for the attribute: {}".format(name))
        return builder()

    def _attr_name(self):
        return self.manifest["name"]

    def _attr_template_version(self):
        return self.manifest.get("version", "2010-09-09")

    def _attr_description(self):
        return self.manifest["description"]
    
    def _attr_profile(self):
        return self.manifest.get("profile", "default")
    
    def get_template(self) -> dict:
        return {
            "AWSTemplateFormatVersion": self.template_version,
            "Description": self.description,
            "Parameters": LocalStack.assemble("{}/parameters".format(self.path)),
            "Resources": LocalStack.assemble("{}/resources".format(self.path)),
            "Outputs": LocalStack.assemble("{}/outputs".format(self.path))
        }
    
    @staticmethod
    def create_skeleton(path, profile, name, desc) -> "LocalStack":
        if os.path.exists(path):
            assert os.path.isdir(path), "stack path must be a directory"
            assert 0 == len(os.listdir(path)), "{} is not empty".format(path)
        else:
            os.mkdir(path)
        os.mkdir("{}/outputs".format(path))
        os.mkdir("{}/resources".format(path))
        os.mkdir("{}/parameters".format(path))
        with open("{}/manifest.json".format(path), mode="w") as fh:
            fh.write("{}\n".format(json.dumps({
                "name": name,
                "description": desc,
                "profile": profile or "default"
            }, indent=4)))
        return LocalStack.load(path)

    @staticmethod
    def assemble(path) -> dict:
        if not os.path.exists(path):
            return {}
        assert os.path.isdir(path), "{} is not directory".format(path)
        template = {}
        for fpath in glob.iglob("{}/**/*.json".format(path), recursive=True):
            rpath = fpath.replace(path, "", 1)
            if re.search("{}-".format(os.path.sep), rpath):
                continue
            logical = rpath.replace(os.path.sep, "")[:-5]
            assert logical not in template, "duplicate logical name: {}".format(logical)
            with open(fpath, "r") as fh:
                template[logical] = json.load(fh)
        return template

    @staticmethod
    def load(path) -> "LocalStack":
        assert os.path.isdir(path)
        manifest_file = "{}/manifest.json".format(path)
        assert os.path.exists(manifest_file), "manifest file not found: {}".format(manifest_file)
        with open(manifest_file, "r") as fh:
            manifest = json.load(fh)
        assert "name" in manifest
        assert "description" in manifest
        return LocalStack(path, manifest)

class Stack:
    def __init__(self, lstack: LocalStack, cf):
        self.lstack = lstack
        self.cf = cf

    def create_stack(self, termination_protection):
        self.cf.create_stack(
            StackName=self.lstack.name,
            TemplateBody=json.dumps(self.lstack.get_template()),
            Capabilities=["CAPABILITY_NAMED_IAM"],
            OnFailure="ROLLBACK",
            EnableTerminationProtection=termination_protection
        )

    def get_info(self) -> dict:
        resp = self.cf.describe_stacks(
            StackName=self.lstack.name
        )
        for info in resp["Stacks"]:
            if info["StackName"] == self.lstack.name:
                return info
        raise Exception("stack [{}] not found".format(self.lstack.name))

    def get_status(self) -> (str, bool):
        status = self.get_info()["StackStatus"]
        return status, status.endswith("_IN_PROGRESS")

    def create_changeset(self, name):
        self.cf.create_change_set(
            StackName=self.lstack.name,
            TemplateBody=json.dumps(self.lstack.get_template()),
            ChangeSetName=name,
            Capabilities=["CAPABILITY_NAMED_IAM"]
        )

    def get_changeset(self, name) -> dict:
        return self.cf.describe_change_set(
            StackName=self.lstack.name,
            ChangeSetName=name
        )
    
    def get_changeset_status(self, name) -> (str, bool):
        changeset = self.get_changeset(name)
        return changeset["Status"], changeset["Status"] in ["CREATE_PENDING", "CREATE_IN_PROGRESS"]

    def execute_changeset(self, name) -> str:
        self.cf.execute_change_set(
            StackName=self.lstack.name,
            ChangeSetName=name
        )

    def get_changesets(self) -> list:
        resp = self.cf.list_change_sets(
            StackName=self.lstack.name
        )
        return resp["Summaries"]
    
    def get_resources(self) -> list:
        resp = self.cf.list_stack_resources(
            StackName=self.lstack.name
        )
        return resp["StackResourceSummaries"]
    
    def get_exports(self) -> list:
        return self.get_info().get("Outputs", [])

    def get_template(self, indent=None) -> dict:
        resp = self.cf.get_template(
            StackName=self.lstack.name,
            TemplateStage="Original"
        )
        return resp["TemplateBody"]

    def validate(self):
        return self.cf.validate_template(
            TemplateBody=json.dumps(self.lstack.get_template())
        )

    @staticmethod
    def load(lstack: LocalStack, profile: str) -> "Stack":
        aws_session = boto3.session.Session(profile_name=(profile or lstack.profile))
        return Stack(lstack, aws_session.client("cloudformation"))
