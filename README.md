[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
![CI](https://github.com/egede/spotmanager/workflows/CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/egede/spotmanager/badge.svg?branch=main)](https://coveralls.io/github/egede/spotmanager?branch=main)

# Spotmanager
Manage spot (preemptible) instances in a cloud environment. The code will query for the existence of running instances,
retire from the condor queue servers that have been alive for a while (to prevent jobs running when 
machines are pulled down), will pull down idle machines and finally create new ones.

## Install
The best is to install inside a virtualenv

    python3 -m venv spotmanager
    cd spotmanager
    source bin/activate
    pip install --upgrade pip
    pip install wheel
    pip install git+https://github.com/egede/spotmanager.git
    
The code can run from the _controller_ script. Do

    controller --help
    
to see the options. Almost for sure code will need to be modified to suit an individual use.
