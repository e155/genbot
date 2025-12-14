#!/bin/bash
timedatectl set-timezone  Europe/Kyiv
echo 'export LANG=C.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=C.UTF-8' >> ~/.bashrc
source ~/.bashrc

