# Jenkins Automation Project

This project aims to streamline interactions with Jenkins via its API, allowing users to perform batch operations such as building, backing up, restoring, and editing Jenkins jobs. 

## Features

- **Build Jenkins Jobs**: Build Jenkins jobs using the Jenkins API.
- **Backup and Restore**: Backup and restore Jenkins jobs configurations in batches.
- **Edit Configurations**: Modify Jenkins job configurations using a dictionary-based approach.
- **Centralized Inputs**: All user inputs are centralized in `inputs.py`.
- **Environment Variables**: Use environment variables (`JENKINS_USERNAME` and `JENKINS_APIKEY`) to securely authenticate with Jenkins.

## Setup

1. **Environment Variables**: Ensure your `.env` file contains the following variables:
   - `JENKINS_USERNAME`: Your Jenkins username.
   - `JENKINS_APIKEY`: Your Jenkins API key.

   - To obtain a Jenkins API key, follow the instructions provided at:
https://stackoverflow.com/questions/45466090/how-to-get-the-api-token-for-jenkins


2. **Virtual Environment (Optional)**: It's recommended to use a virtual environment to manage project dependencies. You can create a virtual environment named `.venv` and activate it, and install project dependencies using the following commands:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate    # On Windows
   source .venv/bin/activate # On Unix or MacOS
   ```
   
3. **Dependencies**: Install project dependencies using `pip`:

   ```bash
   pip install -r requirements.txt
   ```

4. **Usage**: Modify the `change_dictionary` in `main.py` to define the changes you want to make to Jenkins job configurations. Then, run `main.py` to execute the changes.

## Change Dictionary

The `change_dictionary` maps function names to new values for modifying Jenkins job configurations. Available functions include:

- `build_parameters`
- `script_parameters`
- `git_repo`
- `post_build_projects`
- `post_build_properties`
- `email_to`
- `email_subject`
- `build_node`
- `description`
- `build_branch`

Example of a change dictionary:

```python
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
```

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/your-feature-name`).
5. Create a new pull request.

## License

This project is licensed under the [BSD 3-Clause License](LICENSE).
