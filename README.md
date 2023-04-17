# ImpfPass Apotheken Portal

Welcome to the **ImpfPass Apotheken Portal** GitHub repository! This project aims to automate the process of filling out the form on mein-apothekenportal.de for generating COVID-19 EU vaccination certificates. The script utilizes web drivers to achieve this, and has already been used to create and send out over 9000 certificates.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
  - [Creating a .env file](#creating-a-env-file)
  - [Dealing with requirements.txt](#dealing-with-requirements.txt)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- Automatically fills out the mein-apothekenportal.de form for generating COVID-19 EU vaccination certificates
- Utilizes web drivers for automation
- Proven track record of creating and sending over 9000 certificates

## Requirements

- Python 3.7+
- Google Chrome (latest version recommended)
- ChromeDriver (compatible with your Chrome version)

## Setup

### Creating a .env file

1. Locate the `.env.template` file in the project's root directory.
2. Make a copy of the file and rename it to `.env`.
3. Open the `.env` file with a text editor.
4. Fill in the required fields with your personal information and credentials, making sure to replace the placeholder values. Save the file when you're done.

### Dealing with requirements.txt

1. Open your terminal or command prompt.
2. Navigate to the project's root directory.
3. Run the following command to install the required dependencies: `pip install -r requirements.txt`

This will install all the necessary packages for the project to run.

## Usage

1. Navigate to the project's root directory using your terminal or command prompt.
2. Run the following command to start the script: `python main.py`
3. Follow the on-screen instructions to complete the process and start the automation.