from jenkins_class import *
from jenkins_gui import JenkinsGUI
from tkinter import *

change_dictionary = {
    "build_parameters": {
        "ENV01": None,
        "ACCOUNT_ENV01": None,
        "ENV02": None,
        "ACCOUNT_ENV02": None,
        "BRANCH": None,
    },
    "script_parameters": [
        "--variable ENV01:${ENV01}",
        "--variable ACCOUNT_ENV01:${ACCOUNT_ENV01}",
        "--variable ENV02:${ENV02}",
        "--variable ACCOUNT_ENV02:${ACCOUNT_ENV02}",
        "-e DefectORDraftORPerformance",
    ],
    "git_repo": GIT_URL,
    "post_build_projects": "Zephyr_Upload,copy_results_to_cloud",
    "post_build_properties": "WRKSPACE=${WORKSPACE}\nINIT_JOB_BASE_NAME=${JOB_BASE_NAME}",
    "email_to": "JenkinsReport@company.com",
    "email_subject": "v1.0",
    "build_node": None,
    "description": "v1.0",
    "build_branch": "${BRANCH}",
}
# Necessary to init the Jenkins variables and jobs
# jenkins_project = JenkinsProject()

# Backup Existing Jobs
# jenkins_project.backup_jobs()

# Create _updates Folder
# jenkins_project.change(change_dict=change_dictionary)

# Upload changes from _updates Folder
# jenkins_project.upload_jobs()

# Used to Create New from _updates Folder
# create_jobs()

# Builds Jenkins Report
# build_report()

# assemble_build_list()
# jenkins_project.restore_backups()
