import os
from typing import Any, Dict, List
import json
import boto3
from logging import Logger


class Parser:

    def get_cfn_list_exports(self, cfn_client: Any) -> str:
        """Return a cloudformation export full list."""
        self.logger.info(f"get_cfn_list_exportsexport")
        full_export_list = []
        exports = cfn_client.list_exports()
        while True:
            full_export_list.extend(exports.get("Exports", []))
            # check if there are more exports
            next_token = exports.get('NextToken')
            self.logger.info(next_token)
            if next_token is None:
                break
            self.logger.info(
                f"Output exceeds 100 exported output values, reading next page with NextToken: {next_token}")
            exports = cfn_client.list_exports(NextToken=next_token)
        self.logger.info(f'full export list: {full_export_list}')
        return full_export_list

    def get_cfn_export(self, exports: list, exportname: str = "example") -> str:
        self.logger.info(f"looking for the import variable of: {exportname}")
        for export in exports:
            if exportname == export.get("Name"):
                return export["Value"]

    def get_ssm_parameter(self, ssm_client: Any, path: str = "example") -> str:
        """Return a SSM parameter."""
        self.logger.info(f"get_ssm_parameter: {path}")
        # WithDecrypion is ignored if we are pulling a non Secure value
        result = ssm_client.get_parameter(Name=path, WithDecryption=True)
        if result.get("Parameter", {}).get("Type") == "StringList":
            return result.get("Parameter", {}).get("Value").split(",")
        else:
            return result.get("Parameter", {}).get("Value")

    def resolve(self, obj: [list, dict], export_list: Dict[str, Any], boto3_ssm_client: Any, boto3_cf_client: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = self.resolve(v, export_list, boto3_ssm_client, boto3_cf_client)
            return obj
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                if isinstance(item, dict):
                    self.resolve(item, export_list, boto3_ssm_client, boto3_cf_client)
                elif isinstance(item, list) or isinstance(item, str):
                    obj[index] = self.resolve(
                        item, export_list, boto3_ssm_client, boto3_cf_client)
            return obj
        elif isinstance(obj, str):
            if obj.startswith("!Import"):
                obj = self.get_cfn_export(
                    export_list, obj.split(" ")[1])
            if obj.startswith("resolve:ssm"):
                self.logger.info("SSM parameter store")
                split_obj = obj.split(":")
                path = split_obj[2]
                if len(split_obj) > 3:
                    path = f"{path}:{split_obj[3]}"
                obj = self.get_ssm_parameter(boto3_ssm_client, path)
            return obj

    def references(self, event: Dict[str, Any], logger: Logger, boto3_ssm_client, boto3_cf_client) -> Dict[str, Any]:
        """Handle the lambda invocation for returning parameters."""

        self.logger = logger

        self.logger.debug(event)
        # get full list of exports for speed
        export_list = self.get_cfn_list_exports(boto3_cf_client)
        self.logger.debug(export_list)
        self.resolve(event, export_list, boto3_ssm_client, boto3_cf_client)

        self.logger.info(event)
        return event
