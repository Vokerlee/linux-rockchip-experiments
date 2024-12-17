# How to install Armbian distributive to Orange Pi 5 Pro

## Preliminar actions

List of actions:
  * Install [official distributive](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-5-Pro.html) to your SD-card like Orange Pi OS(Arch) with any kernel, it doesn't matter right now.
  * After booting from SD-card download [Armbian distributive](https://www.armbian.com/orange-pi-5-pro/) **using your board**.
  * Use the following command to install distributive to eMMC module on your board
    * ```shell
        sudo dd bs=1M if=name.img of=/dev/[device-name]
        sudo dd bs=1M if=name.img of=/dev/mmcblk1 # example
        ```
  * Before reboot **make sure** that patch cord (Ethernet cable) is plugged in, otherwise
  you will encounter some troubles creating linux account and installing updates.
  * Remove SD-card.
  * ```
    reboot
    ```

## Armbian installed

### Basic

  * Register linux account, update the system:
  ```shell
  sudo apt update && sudo apt upgrade
  sudo apt install net-tools
  sudo apt install aptitude
  sudo aptitude install libssl-dev
  ```
  * After the previous stage turn on Wi-Fi and you can plug out Ethernet cable.
  * If you use NVME device, let's turn on its default mounting:
    ```shell
    blkid
    sudo echo "UUID=[from blkid] [path] ext4 defaults 0 1" >> /etc/fstab
    sudo mount -a # try to mount using updated fstab
    ```
  * ```shell
    reboot # for no problems
    ```
### Enable SSH

  * Generate keys:
  ```shell
  mkdir -p $HOME/.ssh
  sudo ssh-keygen -t rsa -b 4096 -C "[EMAIL]" -f $HOME/.ssh/id_rsa # sshd will start automatically
  ```

### Disable auto-suspend

```shell
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
sudo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target
```