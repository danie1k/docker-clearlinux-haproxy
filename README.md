# Clear Linux* OS `haproxy` container image

Based on https://github.com/clearlinux/dockerfiles/tree/master/haproxy

Differences:
- Added [`clr-network-troubleshooter`] bundle (for `ping` command)
- Added [`iproute2`] bundle (for `ip` command)
- Added [`mosquitto`] bundle (for `mosquitto_pub` command)
- Added `VOLUME` statement in the [`Dockerfile`]

## What is this image?

`clearlinux/haproxy` is a Docker image with `haproxy`
running on top of the [official clearlinux base image](https://hub.docker.com/_/clearlinux).

> [Haproxy](http://www.haproxy.org/)  is a free, very fast and reliable solution offering
> high availability, load balancing, and proxying for TCP and HTTP-based applications.

For other Clear Linux* OS
based container images, see: https://hub.docker.com/u/clearlinux

## Why use a clearlinux based image?

> [Clear Linux* OS](https://clearlinux.org/) is an open source, rolling release
> Linux distribution optimized for performance and security, from the Cloud to
> the Edge, designed for customization, and manageability.

Clear Linux* OS based container images use:
* Optimized libraries that are compiled with latest compiler versions and
  flags.
* Software packages that follow upstream source closely and update frequently.
* An aggressive security model and best practices for CVE patching.
* A multi-staged build approach to keep a reduced container image size.
* The same container syntax as the official images to make getting started
  easy.

To learn more about Clear Linux* OS, visit: https://clearlinux.org.

## Deploy with Docker
The easiest way to get started with this image is by simply pulling it from
Docker Hub.

*Note: This container uses the same syntax as the [official haproxy image](https://hub.docker.com/_/haproxy).


1. Pull the image from Docker Hub:
    ```shell
    $ docker pull clearlinux/haproxy
    ```

2. Start a container using the examples below:
    ```shell
    $ docker run --name some-haproxy -d -p 8080:80 clearlinux/haproxy
    ```

## Licenses

All licenses for the Clear Linux* Project and distributed software can be found
at https://clearlinux.org/terms-and-policies


[`Dockerfile`]: ./Dockerfile
[`clr-network-troubleshooter`]: https://clearlinux.org/software/bundle/clr-network-troubleshooter
[`iproute2`]: https://clearlinux.org/software/bundle/iproute2
[`mosquitto`]: https://clearlinux.org/software/bundle/mosquitto
