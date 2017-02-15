dhtcrawler cluster
==================

Cluster project to crawl the BitTorrent DHT network and download torrent file metadata from remote BitTorrent clients.

Run a number of [p2pspider](https://github.com/dontcontactme/p2pspider) instance hosts (crawlers) to gather DHT infohashes, download their metadata and send them on a [Redis](https://redis.io/)-based [Celery](http://www.celeryproject.org/) instance (collector) which verifies the torrent files and stores them to disk.

Requirements
------------

### Development ###

* Python 3.5 (and pip)
* Node.js >=0.12.0 (and npm)
* Redis Server
* aws cli (for docker image pushing)
* aria2 (for torrent indexing script)

### Docker deployment ###

* [Docker](https://docs.docker.com/userguide/)
* [Docker Compose](https://docs.docker.com/compose/)

1. DEVELOPMENT
--------------

### 1.1 Setup Celery collector

First, install the Redis daemon and start it. Then start the Celery worker which will connect to the Redis instance on localhost:

```
$ cd collector
$ pyvenv venv
$ source venv/bin/activate
(venv) $ pip3 install -r requirements.txt
(venv) $ ./tasks.py
```

Collected torrent files will be saved as `torrents/[INFOHASH].torrent`

### 1.2 Setup p2pspider crawler

```
$ cd crawler
$ npm install
$ npm start
```

This will start the worker with the default broker of `redis://localhost/0`. To use another one, e.g. a remote host, set the `BROKER` environment variable:

```
$ BROKER=redis://[HOSTNAME]/0 npm start
```

2. DEPLOYMENT WITH DOCKER
-------------------------

### 2.1 Output directory

Because the programs within the containers run with different uids, you may need to make the `torrents` target directory writeable before:

```
$ chmod a+w torrents
```

If you intend to crawl for a while, you may run out of inodes because of the many small torrent files. It's a good idea to (loop) mount a filesystem with a higher inode count than the default. The usage type `news` creates one inode for every 4k block, which should be plenty.

```
$ dd if=/dev/zero of=torrents.img bs=1M count=1024
$ mkfs.ext4 -T news torrents.img
# mount torrents.img torrents
# chmod -R a+w torrents
```

### 2.2 Creating docker images

Building the images and starting the cluster locally (one crawler, one collector instance):

```
$ docker-compose build
$ docker-compose up
```

To start the optional Celery Flower web monitor, issue `docker ps` to find the ID of the running collector container and then issue:

```
$ docker exec [CONTAINER-ID] supervisorctl start celery-flower
```

Afterwards it should be reachable via [localhost:5555](http://localhost:5555).

### 2.3 Deployment to AWS ECS

#### 1. Setup ECS (EC2 Container Service)

For the developer guide on ECS, [see here](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html). These are the basic steps for setting it up:

In the [IAM console](https://console.aws.amazon.com/iam):
* Create an [ECS instance role](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/instance_IAM_role.html) with the `AmazonEC2ContainerServiceforEC2Role` policy attached

In the [ECS console](https://console.aws.amazon.com/ecs):
* Create two container registry repositories: `collector` and `crawler`
* Build, tag and push the two Docker images

Configure the aws cli by running `aws configure`. Then run either the `aws/push-containers.sh` script or follow the push instructions manually (given on the EC2 container registry site).

* Define tasks definitions

Create a `collector` and a `crawler` task using the supplied JSON task definitions. Be sure to replace the `[REGISTRY-URI]` field with your own ECS repository URI, and replace the `[COLLECTOR]` field with the private IP/hostname of the EC2 instance where the Collector container runs.

* Define cluster

Create a service for each task definition. Set the `Number of tasks` to 0 for now.

#### 2. Create EC2 instances

* Select an [Amazon ECS-optimized AMI](http://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_container_instance.html) from the Community AMIs
* Set the created ECS instance role as IAM role for the instance
* Insert the setup script `aws/setup-ec2-instance.sh` as user data
* Use a security group that allows port 6881 UDP/TCP inbound from the internet (and the Redis Port 6379 TCP between the instances)
* You will need to create and run [CrawlerCount]+1 EC2 instances

#### 3. Running it

* Collector service: Set `Number of tasks` to 1. 
* ECS should find a suitable EC2 instance and start a collector container. Check that a collector container has started, note the private IP of collector EC2 instance and update the `crawler` task definition so that `BROKER` env variable points to the correct collector hostname/IP  
  (This manual step could be eliminated by using a proper ECS service discovery solution).
* Crawler service: Set `Number of tasks` to some number in [1,*].

3. LOGS
-------

To see the collector status, connect to the collector host,  issue `docker ps` to find the ID of the running collector container and then issue:

```
$ docker logs -f [CONTAINER-ID]
```

To see only the stats, use the following. They are printed every minute and show the cumulative values of the last 10 minutes.

```
$ docker logs -f [CONTAINER-ID] 2>&1 | grep print_stats
```

For a typical session, the stats may look like this:

```
Received task: tasks.print_stats[17e03d9a-23b9-4be5-86c4-ebc020f672f4]  
tasks.print_stats: last 10.0 mins: 1800 torrents / 51.2 MB saved
tasks.print_stats: Rate: 180.0/m, 10799.5/h, 259.2k/d
tasks.print_stats: Storage consumption rate: 5.1 MB/m, 0.3 GB/h, 7.2 GB/d
Task tasks.print_stats[17e03d9a-23b9-4be5-86c4-ebc020f672f4] succeeded in 0.04759194100006425s: {'saved': 1800, 'size': 53672251, 'save_rate': 2.999862196330241, 'size_rate': 89449.64264824889, 'running': 600.027562, 'start': 1482410075.418662}

```
