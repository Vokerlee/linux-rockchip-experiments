#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
#
# Copyright (C) 2024 by Roman Glaz
#
# This script is used to update current initramfs & kernel images, dtb files
# Works for: Orange Pi 5 Pro, Armbian customized kernel

set -eou pipefail

script_dir="$(dirname "$0")"
linux_src_root=$(realpath "./${script_dir}/..")
cd $linux_src_root
version=$(make kernelversion)

# Kernel image

image_symlink=Image
image="vmlinuz-${version}"

install_kernel_image() {
    cd $linux_src_root
    make install
    cd /boot
    rm -rf $image_symlink
    ln -fs $image $image_symlink
}

# Kernel modules

install_kernel_modules() {
    cd $linux_src_root
    make modules_install
}

# Device tree

dtb_symlink=dtb
dtb="dtb-$version"

install_dtb() {
    cd $linux_src_root
    make dtbs_install INSTALL_DTBS_PATH=/boot/$dtb
    cd /boot
    rm -rf $dtb_symlink
    ln -fs $dtb $dtb_symlink
}

# Initrd

initrd="initrd.img-${version}"
initrd_symlink=initrd.img

install_initrd() {
    # uInitrd and initrd.img are supposed to be installed here after kernel installation
    rm -rf $initrd_symlink
    ln -fs $initrd $initrd_symlink
}

# Start

install_kernel_image
install_kernel_modules
install_dtb
install_initrd

echo "Successfully updated boot & kernel images to version ${version}"
