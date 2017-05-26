Ultron
---
Compare production and dev aws environment
versions for dev teams then post to slack

Purpose
---
There are multiple agile development teams using AWS on various 
projects. The versions of Elastic Beanstalk environments, EC2
services do not always match up to the corresponding versions in production. To find out
what versions the teams are running and what versions are on production required the 
utilization of various tools. 

This tool will report the environment/service versions right beside each other. The comparisons
 are broken into categories of matching, not matching and dev branches. The tool currently takes data
 for Elastic Beanstalk and EC2 resources, other cloud service plugins
 can be incorporated .


Sample Report
---

The report that gets posted on each teams slack looks something like this...

![Sample Report](https://raw.githubusercontent.com/Signiant/ultron/master/images/sample_ultron_report.png)


Prerequisites
---

* A config file determining master team and regular team connection information.

Usage
---
To run the tool you require a set config file and aws credentials

`docker pull signiant/ultron`

`docker run -v /absolute path/source_code/sample_config.json:/source-code/sample_config.json  -v /absolute path/aws_credentials:/root/aws_credentials ultron:latest`



Project Organization
---
  
The project is structured as follows:

* Ultron.py - this invokes each plugin, calls the comparator functions and output formatter
* plugins - one plugin per AWS service. Each plugin requires a compare.py implementation.
* output.py - reads the formatted data from comparator, creates slack json payload then posts to slack
* sample_config.json -  configure what qualities to compare on whether you want the environments to be compared if they have green health, if the environment is live and if the team is the master 











