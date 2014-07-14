### Android development environment for ubuntu precise (12.04 LTS)

* Oracle Java JDK 6
* Android SDK r22.3
* Android NDK r9c
* Apache Ant 1.8.4

It also updates the SDK to android 19 (4.4.2) with platform tools and system images for that revision.

#### Install

You can either pull from `ahazem/android`:

```
docker pull ahazem/android
```

```
docker run -i -t ahazem/android /bin/bash
```

or add it to your Dockerfile:

```
FROM ahazem/android
```
