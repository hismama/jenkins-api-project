from datetime import datetime
from dotenv import load_dotenv
from inputs import *
import os
import requests
import csv
from typing import Union
from pathlib import Path
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as et
import json
import pandas as pd
import jenkins
import pyperclip

load_dotenv(ENV_PATH)
USERNAME = os.getenv("JENKINS_USERNAME")
KEY = os.getenv("JENKINS_APIKEY")
if USERNAME is None or KEY is None:
    print(
        f"JENKINS_USERNAME: {USERNAME}\nJENKINS_APIKEY: {KEY}\n"
        f"Check your path: {ENV_PATH}\nSet JENKINS_USERNAME and JENKINS_APIKEY in .env file."
    )
    quit()


def build_report(
    jenkins_root: str = JENKINS_ROOT, jenkins_path: str = JENKINS_PATH
) -> str:
    all_total = 0
    total_success = 0
    report_columns = ["Name", "Status", "Success", "Total"]
    report_rows = []
    server = jenkins.Jenkins(
        url=jenkins_root + jenkins_path,
        username=USERNAME,
        password=KEY,
    )
    jobs = server.get_all_jobs()
    print("Building report...")
    for job in jobs:
        try:
            status = server.get_job_info(job["name"])["disabled"]
        except Exception as e:
            print(job["name"], e)
            status = True
        if job["name"] not in EXCLUDED and status is False:
            # print(server.get_job_info(job["name"]))
            try:
                build_number = server.get_job_info(job["name"])["builds"][0]["number"]
            except IndexError:
                continue
            else:
                # print(build_number)
                build_info = server.get_build_info(job["name"], build_number)
                # print(build_info)
                pass_fail = build_info["result"]
                comment = ""
                if pass_fail is None:
                    try:
                        build_info = server.get_build_info(
                            job["name"], build_number - 1
                        )
                        pass_fail = build_info["result"]
                    except jenkins.JenkinsException:
                        comment = "no builds"
                    else:
                        comment = "previous"
                try:
                    total_count = build_info["actions"][6]["totalCount"]
                except KeyError:
                    try:
                        total_count = build_info["actions"][7]["totalCount"]
                    except KeyError:
                        total_count = 0
                try:
                    failures = build_info["actions"][6]["failCount"]
                except KeyError:
                    try:
                        failures = build_info["actions"][7]["failCount"]
                    except KeyError:
                        failures = 0
                success = total_count - failures
                report = [job["name"], pass_fail, success, total_count, comment]
                report_rows.append(report)
                all_total += total_count
                total_success += success
    percent_success = str(int(total_success / all_total * 100)) + "%"
    report_rows.append(
        [
            "Overall",
            percent_success,
            total_success,
            all_total,
        ]
    )
    now = datetime.now()
    report_rows.append(["Date_Ran", now.strftime("%Y-%m-%d %H:%M")])
    filepath = Path(__file__).parent / "Jenkins_Summary.csv"
    with open(filepath, "w", newline="") as f:
        write = csv.writer(f)
        write.writerow(report_columns)
        write.writerows(report_rows)
    print(
        f"\nReport exported to:\n{filepath}\n{percent_success} Success\n{all_total} Total Jobs"
    )
    return f"\nReport exported to:\n{filepath}\n{percent_success} Success\n{all_total} Total Jobs"


def assemble_build_list(
    project_directory: str = LOCAL_BACKUP_ROOT + LOCAL_BACKUP_FOLDER + "_updates",
):
    """
    Builds comma separated list for placing into _Manual_Kickoff Downstream Projects
    """
    build_list = ""
    for file in os.listdir(project_directory):
        if file.endswith(".xml"):
            job = os.path.splitext(file)[0]
            build_list += job + ","
    pyperclip.copy(build_list)
    print("\n\nBuild List copied to clipboard!")


def create_jobs(
    upload_root: str = LOCAL_BACKUP_ROOT,
    upload_folder: str = LOCAL_BACKUP_FOLDER,
    jenkins_base_url: str = JENKINS_ROOT,
    create_path: str = CREATE_JENKINS_PATH,
    username: str = USERNAME,
    api_key: str = KEY,
) -> None:
    """
    Create Jenkins jobs from XML files stored in a specified folder that function "change" creates.

    Args:
    - upload_root (str): Root directory for uploaded files. Defaults to LOCAL_BACKUP_ROOT.
    - upload_folder (str): Folder containing uploaded XML files. Defaults to LOCAL_BACKUP_FOLDER.
    - jenkins_base_url (str): Base URL of Jenkins server. Defaults to JENKINS_ROOT.
    - create_path (str): Path to Jenkins job creation endpoint. Defaults to CREATE_JENKINS_PATH.
    - username (str): Username for Jenkins authentication. Defaults to USERNAME.
    - api_key (str): API key for Jenkins authentication. Defaults to KEY.

    Returns:
    None

    Raises:
    - FileNotFoundError: If no files are found in the specified upload folder.

    Notes:
    This function reads XML files from the upload folder, creates Jenkins jobs
    using the Jenkins REST API, and prints the status of each job creation attempt.
    """
    upload_folder = upload_root + upload_folder + "_updates"
    try:
        os.listdir(upload_folder)
    except FileNotFoundError:
        print(f"\nNo files found under: {upload_folder}")
        quit()
    for file in os.listdir(upload_folder):
        if file.endswith(".xml"):
            config_xml_path = os.path.join(upload_folder, file)
            with open(config_xml_path, "r") as config_file:
                config_xml = config_file.read()
            job = os.path.splitext(file)[0]
            post_url = jenkins_base_url + create_path + "createItem?name=" + job
            response = requests.post(
                url=post_url,
                data=config_xml,
                auth=HTTPBasicAuth(username, api_key),
                headers={"Content-Type": "application/xml"},
            )
            if response.status_code == 200:
                print(f"POST request for {job} successful")
            elif response.status_code == 404:
                print(
                    f"Project path needs to exist prior to create_jobs.\nVerify path: {post_url}"
                )
            else:
                print(
                    f"POST request for {job} failed with status code:",
                    response.status_code,
                )


def xml_adjust_element(xml: et.Element, node_name: str, new_value: str) -> None:
    """
    Adjusts the value of an XML element or creates a new element if it doesn't exist.

    Args:
    - xml (xml.etree.ElementTree.Element): The root XML element.
    - node_name (str): The name of the XML node to adjust or create.
    - new_value (str): The new value to assign to the XML node.

    Returns:
    None

    Notes:
    This function searches for an XML element with the given node_name.
    If found, it updates the element's text content with the new_value.
    If the element does not exist, it creates a new element with the given node_name
    and assigns it the new_value.

    Example:
    xml = et.Element('root')
    xml_adjust_element(xml, 'name', 'John')
    # <root><name>John</name></root>
    """
    new_node = xml.find(".//" + node_name)
    if new_node is None:
        new_node = et.Element(node_name)
        xml.append(new_node)
    new_node.text = new_value


def xml_adjust_nodevalue(
    xml: et.Element, xml_path: str, node_name: str, new_value: str
) -> None:
    """
    Adjusts the value of an XML node or creates a new node if it doesn't exist.

    Args:
    - xml (xml.etree.ElementTree.Element): The root XML element.
    - xml_path (str): The XPath to the parent element where the node will be adjusted or created.
    - node_name (str): The name of the XML node to adjust or create.
    - new_value (str): The new value to assign to the XML node.

    Returns:
    None

    Notes:
    This function adjusts the value of an XML node specified by the given XPath.
    If the node does not exist, it creates a new node with the specified name and value
    under the parent element specified by xml_path.

    If the parent element specified by xml_path does not exist, a TypeError is raised,
    indicating that the main XML path does not exist. In such cases, manual intervention
    is required to create the necessary XML structure in Jenkins before re-running the function.

    Example:
    xml = et.Element('root')
    xml_adjust_nodevalue(xml, '.', 'name', 'John')
    # <root><name>John</name></root>
    """
    new_value_xpath = xml_path + "/" + node_name
    new_value_node = xml.find(new_value_xpath)
    if new_value_node is None:
        try:
            new_value_node = et.SubElement(xml.find(xml_path), node_name)
        except TypeError:
            print(
                f"Main {xml_path} does not exist.\n"
                f"Create section manually in Jenkins, take backup of job XML, and run again.\n"
            )
            return
    new_value_node.text = new_value


class JenkinsProject:
    def __init__(
        self,
        jenkins_base_url: str = JENKINS_ROOT,
        project_path: str = JENKINS_PATH,
    ):
        """
        Represents a Jenkins project and provides methods to interact with Jenkins.

        Args:
        - jenkins_base_url (str): The base URL of the Jenkins server.
        - project_path (str): The path to the Jenkins project.

        Attributes:
        - jenkins_root (str): The base URL of the Jenkins server.
        - jenkins_path (str): The path to the Jenkins project.
        - username (str): The username for authentication.
        - api_key (str): The API key for authentication.
        - backup_folder (str): The folder name for local backups.
        - backup_path (str): The full path to the local backup folder.
        - jenkins_csv (str): The path to the Jenkins CSV file containing job, node, URL1, URL2, and branch data
        - csv_job (str): Placeholder for job name from CSV.
        - csv_node (str): Placeholder for node name from CSV.
        - csv_url1 (str): Placeholder for URL1 from CSV.
        - csv_url2 (str): Placeholder for URL2 from CSV.
        - csv_branch (str): Placeholder for branch name from CSV.
        - node_tenant (dict): Dictionary containing job, node, URL1, URL2, and branch data from CSV.
        - raw_data (dict): Raw data retrieved from Jenkins server.
        - jobs (list): List of dictionaries containing job names and URLs.
        - job_names (list): List of job names.
        - job_urls (list): List of job URLs.
        - json_data (dict): JSON data containing jobs.

        Methods:
        - __init__: Initializes a JenkinsProject instance.
        - backup_jobs: Backs up Jenkins jobs by retrieving their config.xml files.
        - directory_upload: Uploads XML files from a directory to Jenkins jobs.
        - change: Iterates through Jenkins CSV to find matching config.xml Job files and adjusts them.
        - email_to: Modifies the email recipient list in a Jenkins job configuration XML.
        - email_subject: Modifies the email subject template in a Jenkins job configuration XML.
        - build_node: Modifies the assigned build node in a Jenkins job configuration XML.
        - description: Modifies the job description in a Jenkins job configuration XML.
        - build_branch: Modifies the build branch in a Jenkins job configuration XML.
        - git_repo: Modifies the Git repository URL in a Jenkins job configuration XML.
        - post_build_projects: Modifies the post-build projects in a Jenkins job configuration XML.
        - post_build_properties: Modifies the post-build properties in a Jenkins job configuration XML.
        - build_parameters: Modifies build parameters in a Jenkins job configuration XML.
        - script_parameters: Modifies script parameters in a Jenkins job configuration XML.

        Raises:
        - FileNotFoundError: If the CSV file or any config.xml file is not found.
        - KeyError: If an invalid function is provided in the change dictionary.

        Notes:
        - This class provides a comprehensive interface to manage Jenkins projects and configurations.
        """
        self.jenkins_root = jenkins_base_url
        self.jenkins_path = project_path
        self.username = USERNAME
        self.api_key = KEY
        self.backup_folder = LOCAL_BACKUP_FOLDER
        self.backup_path = LOCAL_BACKUP_ROOT + LOCAL_BACKUP_FOLDER
        self.jenkins_csv = JENKINS_CSV
        # All assigned individually in a change call
        self.csv_job = None
        self.csv_node = None
        self.csv_url1 = None
        self.csv_url2 = None
        self.csv_branch = None
        self.test = 0
        try:
            df = pd.read_csv(self.jenkins_csv)
        except FileNotFoundError:
            print(f"Check your Jenkins.csv location:\n{self.jenkins_csv}")
            quit()
        self.node_tenant = df.to_dict(orient="dict")
        # Jenkins GET to pull all job names from jenkins_path
        full_project_url = self.jenkins_root + self.jenkins_path + "api/json"
        response = requests.get(
            url=full_project_url,
            auth=HTTPBasicAuth(self.username, self.api_key),
        )
        response.raise_for_status()
        self.raw_data = response.json()
        self.jobs = []
        self.job_names = []
        self.job_urls = []
        # Loop over each Job and extract Name and URL
        for job in self.raw_data["jobs"]:
            job_name = job["name"]
            job_url = job["url"]

            job = {"name": job_name, "url": job_url}
            self.jobs.append(job)
            self.job_names.append(job_name)
            self.job_urls.append(job_url)
        self.json_data = {"jobs": self.jobs}

    def backup_jobs(self):
        """
        Backs up Jenkins jobs by fetching their configuration files.

        The method iterates over each job, retrieves its configuration XML,
        and saves it to a local backup folder named after the job.

        Raises:
        - IOError: If there is an error writing the job's configuration XML to a file.

        Notes:
        - The configuration XML is fetched using the Jenkins REST API.
        - The backup folder structure is created if it doesn't exist.
        - Each job's configuration is saved in a separate XML file named after the job.
        """
        print("Backup initiated...")
        for job in self.jobs:
            response = requests.get(
                url=job["url"] + "config.xml",
                auth=HTTPBasicAuth(self.username, self.api_key),
            )
            filename = self.backup_path + "/" + job["name"] + ".xml"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as file:
                file.write(response.text)
        print("\nBackup completed\n")

    def save_names_urls_as_json(
        self,
        backup_root: str = LOCAL_BACKUP_ROOT,
        backup_folder: str = LOCAL_BACKUP_FOLDER,
    ):
        """
        Saves job names and URLs as JSON to a specified file.

        Args:
        - backup_root (str): The root directory for saving the JSON file.
        - backup_folder (str): The folder where the JSON file will be saved.

        Returns:
        None

        Notes:
        - The JSON file contains job names and URLs stored in the `json_data` attribute.
        - The JSON file is saved with indentation for readability.
        """
        filename = backup_root + backup_folder + "/_API-List.json"
        with open(filename, "w") as file:
            json.dump(self.json_data, file, indent=4)
        print(f"\nJSON placed in: {filename}\n")

    def upload_jobs(self):
        """
        Uploads jobs from the local backup folder to Jenkins.

        Returns:
        None

        Notes:
        - Jobs are uploaded from the `_updates` folder in the local backup path.
        - This method internally calls the `directory_upload` method to upload jobs.
        """
        upload_folder = self.backup_path + "_updates"
        self.directory_upload(upload_folder)

    def restore_backups(self):
        """
        Restores backed-up jobs to their original locations in Jenkins.

        Returns:
        None

        Notes:
        - Jobs are restored from the main backup folder.
        - This method internally calls the `directory_upload` method to restore backups.
        """
        restore_folder = self.backup_path
        self.directory_upload(restore_folder)

    def directory_upload(self, directory):
        """
        Uploads XML files from a directory to Jenkins as job configurations.

        Args:
        - directory (str): The directory containing XML files to upload.

        Returns:
        None

        Notes:
        - This method iterates through XML files in the specified directory.
        - Each XML file is uploaded to Jenkins as a job configuration using the Jenkins REST API.
        - The job name is derived from the XML file name (without the extension).
        - Status messages are printed for each upload attempt.
        """
        for file in os.listdir(directory):
            if file.endswith(".xml"):
                config_xml_path = os.path.join(directory, file)
                with open(config_xml_path, "r") as config_file:
                    config_xml = config_file.read()
                job = os.path.splitext(file)[0]
                post_url = (
                    self.jenkins_root + self.jenkins_path + "job/" + job + "/config.xml"
                )
                response = requests.post(
                    url=post_url,
                    data=config_xml,
                    auth=HTTPBasicAuth(self.username, self.api_key),
                    headers={"Content-Type": "application/xml"},
                )
                if response.status_code == 200:
                    print(f"POST request for {job} successful")
                else:
                    print(
                        f"POST request for {job} failed with status code:",
                        response.status_code,
                    )

    def build_parameters(self, new_value: dict, config_xml: et.Element) -> None:
        """
        Builds and adds parameters to a Jenkins job configuration XML.

        Args:
        - new_value (dict): A dictionary containing parameter names and their corresponding values.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Raises:
        - AttributeError: If the new_value argument is not a dictionary.

        Notes:
        - This method constructs and inserts parameter definitions into the Jenkins job configuration XML.
        - It replaces existing parameter definitions if present to start fresh.
        - The parameter definitions are added under the 'properties/hudson.model.ParametersDefinitionProperty' section.
        - The method handles specific parameter values based on keys such as 'SERVER_TRACE_ENV01', 'SERVER_TRACE_ENV02',
          'ACCOUNT_TRACE_ENV01', 'ACCOUNT_TRACE_ENV02', and 'BRANCH'.
        - It utilizes the xml_adjust_nodevalue function to adjust XML node values accordingly.
        - If the new_value argument is not a dictionary, the method raises an AttributeError.
        """

        parameters = 0
        main_parent = ".//properties/hudson.model.ParametersDefinitionProperty"
        hudson_present = config_xml.find(main_parent)
        # Removing present elements to start fresh
        if hudson_present is not None:
            for child in config_xml.findall(main_parent):
                if child == hudson_present:
                    config_xml.find(".//properties").remove(child)
                    break
        et.SubElement(
            config_xml.find(".//properties"),
            "hudson.model.ParametersDefinitionProperty",
        )
        et.SubElement(config_xml.find(main_parent), "parameterDefinitions")
        try:
            for key, value in new_value.items():
                parameters += 1
                if "SERVER_TRACE_ENV01" == key:
                    value = self.csv_url1
                if "SERVER_TRACE_ENV02" == key:
                    value = self.csv_url2
                if "ACCOUNT_TRACE_ENV01" == key:
                    value = self.csv_url1.split(".")[0].replace("-", "_")
                if "ACCOUNT_TRACE_ENV02" == key:
                    value = self.csv_url2.split(".")[0].replace("-", "_")
                if "BRANCH" == key:
                    value = self.csv_branch

                et.SubElement(
                    config_xml.find(main_parent + "/parameterDefinitions"),
                    "hudson.model.StringParameterDefinition",
                )
                node = (
                    f".//hudson.model.ParametersDefinitionProperty"
                    f"//hudson.model.StringParameterDefinition[{parameters}]"
                )
                xml_adjust_nodevalue(
                    xml=config_xml,
                    xml_path=node,
                    node_name="name",
                    new_value=key,
                )
                xml_adjust_nodevalue(
                    xml=config_xml,
                    xml_path=node,
                    node_name="defaultValue",
                    new_value=value,
                )
        except AttributeError:
            print(
                f"build_parameter value must be of style dictionary, not {type(new_value)}"
            )
            quit()

    def script_parameters(
        self, new_value: Union[list, str], config_xml: et.Element
    ) -> None:
        """
        Modifies script parameters in a Jenkins job configuration XML.

        Args:
        - new_value (Union[list, str]): A list of script parameters or a single script parameter to add.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Raises:
        - TypeError: If the new_value argument is not a list or a string.

        Notes:
        - This method modifies the script parameters in the Jenkins job configuration XML.
        - It appends the provided script parameters to the existing script command in the 'builders/hudson.tasks.Shell' section.
        - If new_value is a list, it adds each parameter to the script command if it's not already present.
        - If new_value is a string, it adds the single parameter to the script command if it's not already present.
        - If new_value is not a list or a string, the method raises a TypeError.
        """
        parameter_command = ""
        command_xpath = ".//builders/hudson.tasks.Shell/command"
        command_string = config_xml.find(command_xpath).text
        if type(new_value) is list:
            for command in new_value:
                if command not in command_string:
                    parameter_command += " " + command
            # Adds necessary command string to robot cmd line call
            insert_position = command_string.find("${JOB_BASE_NAME}.xml") + len(
                "${JOB_BASE_NAME}.xml"
            )
            final_command_string = (
                command_string[:insert_position]
                + parameter_command
                + command_string[insert_position:]
            )
            xml_adjust_nodevalue(
                xml=config_xml,
                xml_path=".//builders/hudson.tasks.Shell",
                node_name="command",
                new_value=final_command_string,
            )
        else:
            print(
                f"script_parameters value must be of style list, not {type(new_value)}"
            )
            quit()

    def git_repo(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the Git repository URL in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new Git repository URL.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the Git repository URL in the Jenkins job configuration XML.
        - It updates the URL attribute of the 'hudson.plugins.git.UserRemoteConfig' element.
        """
        xml_adjust_nodevalue(
            config_xml, ".//hudson.plugins.git.UserRemoteConfig", "url", new_value
        )

    def post_build_projects(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the post-build projects in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new post-build projects configuration.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the post-build projects configuration in the Jenkins job configuration XML.
        - It updates the 'projects' attribute of the 'hudson.plugins.parameterizedtrigger.BuildTriggerConfig' element.
        """
        xml_adjust_nodevalue(
            config_xml,
            ".//configs/hudson.plugins.parameterizedtrigger.BuildTriggerConfig",
            "projects",
            new_value,
        )

    def post_build_properties(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the post-build properties in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new post-build properties configuration.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the post-build properties configuration in the Jenkins job configuration XML.
        - It updates the 'properties' attribute of the 'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters' element.
        """
        xml_adjust_nodevalue(
            config_xml,
            ".//configs//hudson.plugins.parameterizedtrigger.PredefinedBuildParameters",
            "properties",
            new_value,
        )

    def email_to(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the email recipient list in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new recipient list for email notifications.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the email recipient list in the Jenkins job configuration XML.
        - It updates the 'recipientList' element with the new recipient list.
        """
        xml_adjust_element(config_xml, "recipientList", new_value)

    def email_subject(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the email subject template in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new value to append to the email subject template.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the email subject template in the Jenkins job configuration XML.
        - It updates the 'defaultSubject' element with the new subject template.
        - The template includes placeholders for job name and build status.
        """
        template = self.csv_job + "_" + new_value + "_" + "$BUILD_STATUS"
        xml_adjust_element(config_xml, "defaultSubject", template)

    def build_node(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the assigned build node in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new build node for job execution.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the assigned build node in the Jenkins job configuration XML.
        - It updates the 'assignedNode' element with the new build node.
        """
        template = self.csv_node
        xml_adjust_element(config_xml, "assignedNode", template)

    def description(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the job description in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new description for the job.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the job description in the Jenkins job configuration XML.
        - It updates the 'description' element with the new description.
        """
        template = self.csv_job + "_" + new_value
        xml_adjust_element(config_xml, "description", template)

    def build_branch(self, new_value: str, config_xml: et.Element) -> None:
        """
        Modifies the build branch in a Jenkins job configuration XML.

        Args:
        - new_value (str): The new branch name for the build.
        - config_xml (xml.etree.ElementTree.Element): The XML element representing the job configuration.

        Returns:
        None

        Notes:
        - This method modifies the build branch in the Jenkins job configuration XML.
        - It updates the 'name' attribute of the 'hudson.plugins.git.BranchSpec' element with the new branch name.
        """
        xml_adjust_nodevalue(
            config_xml,
            ".//branches/hudson.plugins.git.BranchSpec",
            "name",
            new_value,
        )

    def change(self, change_dict: dict) -> None:
        """
        Iterates through the jenkins_csv to find matching config.xml Job files in Jenkins backup folder.
        If match found, the config.xml file is adjusted according to change dictionary input.

        Args:
        - change_dict (dict): A dictionary containing the changes to be made to the Jenkins job configurations.

        Returns:
        None

        Notes:
        - This method iterates through the jenkins_csv to find matching config.xml Job files in the Jenkins backup folder.
        - For each job found, it adjusts the config.xml file according to the changes specified in the change dictionary.
        - The change dictionary maps function names to their corresponding methods for modifying Jenkins job configurations.
        - If a function specified in the change dictionary is not found, the method prints an error message and terminates.
        - After applying the changes, the updated config.xml files are saved in the '_updates' folder within the backup path.
        """
        function_mapping = {
            "build_parameters": self.build_parameters,
            "script_parameters": self.script_parameters,
            "git_repo": self.git_repo,
            "post_build_projects": self.post_build_projects,
            "post_build_properties": self.post_build_properties,
            "email_to": self.email_to,
            "email_subject": self.email_subject,
            "build_node": self.build_node,
            "description": self.description,
            "build_branch": self.build_branch,
        }
        for key in self.node_tenant["Job"]:
            self.csv_job = self.node_tenant["Job"][key]
            self.csv_node = self.node_tenant["Node"][key]
            self.csv_url1 = self.node_tenant["URL1"][key]
            self.csv_url2 = self.node_tenant["URL2"][key]
            self.csv_branch = self.node_tenant["BRANCH"][key]
            print(f"\nProcessing:\n{self.csv_job}")
            try:
                xml_structure = et.parse(self.backup_path + "/" + self.csv_job + ".xml")
                config_xml = xml_structure.getroot()
            except FileNotFoundError:
                print(
                    f"Jenkins.csv: {self.csv_job}.xml not found in {self.backup_path}\n"
                    f"Changes for {self.csv_job} cannot be performed.\n"
                    f"Add projects to csv or adjust project name in Jenkins or the CSV file."
                )
                continue

            for func_string, value in change_dict.items():
                try:
                    node_func = function_mapping[func_string]
                except KeyError:
                    print(
                        f"Invalid function '{func_string}' in change dictionary, try again."
                    )
                    quit()
                else:
                    node_func(value, config_xml)
            os.makedirs(
                os.path.dirname(self.backup_path + "_updates/"),
                exist_ok=True,
            )
            xml_structure.write(
                self.backup_path + "_updates/" + self.csv_job + ".xml",
                encoding="UTF-8",
                xml_declaration=True,
            )
            print("Done")
