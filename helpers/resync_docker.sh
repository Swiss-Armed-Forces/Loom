#!/usr/bin/env bash
# This script can be used in a qubes template/appvm
# setup where loom is installed in the template and
# run in the appvm. Run this in the appvm to "pull"
# a new version of loom which was updated in the template.
#
# This requires in the appvm the file:
#
# /rw/config/qubes-bind-dirs.d/50_user.conf
#
# to contain:
#
# binds+=( '/var/lib/docker' )
set -euo pipefail

# stop docker & bind-mounts
sudo systemctl stop docker
sudo umount /var/lib/docker || true
sudo /usr/lib/qubes/init/bind-dirs.sh umount
# backup volumes
sudo mv /rw/bind-dirs/var/lib/docker/volumes /rw/volumes-backup
# re-sync docker
while ! sudo rm -rf /rw/bind-dirs/var/lib/docker/; do
    # sometimes docker is started by something else on the system
    # (mostly by just accessing the docker socket). Hence some other
    # processes might have files open/locked in that directory
    # and the rm will fail: just stop docker again and try remove again
    sudo systemctl stop docker
done
sudo /usr/lib/qubes/init/bind-dirs.sh
# restore volumes
sudo rm -rf /rw/bind-dirs/var/lib/docker/volumes
sudo mv /rw/volumes-backup /rw/bind-dirs/var/lib/docker/volumes
# restart docker
sudo systemctl start docker
