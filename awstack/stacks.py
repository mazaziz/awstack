import boto3.session

class Stacks:
    def __init__(self, cf):
        self.cf = cf

    def get_stacks(self):
        status_filter = [
            "CREATE_IN_PROGRESS",
            "CREATE_FAILED",
            "CREATE_COMPLETE",
            "ROLLBACK_IN_PROGRESS",
            "ROLLBACK_FAILED",
            "ROLLBACK_COMPLETE",
            "DELETE_IN_PROGRESS",
            "DELETE_FAILED",
            "UPDATE_IN_PROGRESS",
            "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
            "UPDATE_COMPLETE",
            "UPDATE_ROLLBACK_IN_PROGRESS",
            "UPDATE_ROLLBACK_FAILED",
            "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS",
            "UPDATE_ROLLBACK_COMPLETE",
            "REVIEW_IN_PROGRESS"
        ]
        stacks = []
        resp = self.cf.list_stacks(
            StackStatusFilter=status_filter
        )
        for info in resp["StackSummaries"]:
            stacks.append(info)
        while resp.get("NextToken"):
            resp = self.cf.list_stacks(
                StackStatusFilter=status_filter,
                NextToken=resp.get("NextToken")
            )
            for info in resp["StackSummaries"]:
                stacks.append(info)
        return stacks
    
    def get_exports(self):
        return self.cf.list_exports()["Exports"]

    @staticmethod
    def load(profile) -> "Stacks":
        aws_session = boto3.session.Session(profile_name=(profile or "default"))
        return Stacks(aws_session.client("cloudformation"))
