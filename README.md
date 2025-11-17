# AwsRds

Open source project for performing various AWS RDS (Relational Database Service) tasks.

## Table of Contents
- [AwsRds](#awsrds)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Initialization Class](#initialization-class)
    - [AwsRDS](#awsrds-1)
  - [Instances](#instances)
    - [AddEnvTag](#addenvtag)
    - [CheckDBEnvVar](#checkdbenvvar)
    - [DelEnvTag](#delenvtag)
    - [DownloadLogs](#downloadlogs)
    - [DownloadSlowQueries](#downloadslowqueries)
    - [Exists](#exists)
    - [GetInstance](#getinstance)
    - [GetInstanceByTag](#getinstancebytag)
    - [GetInstanceCluster](#getinstancecluster)
    - [GetModifiedLogs](#getmodifiedlogs)
    - [GetSnapshotByInstance](#getsnapshotbyinstance)
    - [GetTopSnapshot](#gettopsnapshot)
    - [InstanceAction](#instanceaction)
    - [SnapshotExists](#snapshotexists)
    - [Status](#status)
    - [TailLogs](#taillogs)
    - [UploadToS3](#uploadtos3)

## Overview
`AwsRds` is a Python project to interact with AWS RDS instances. It provides tools to list, manage, and monitor RDS instances programmatically.

- Prerequisites
  - Must have an AWS CLI Profile configured

## Initialization Class

### AwsRDS

**Parameters**
- Profile (str)
  - AWS CLI Profile Name
    - **Default**: default
- Region (str)
  - AWS CLI Profile Region
    - **Default**: us-east-1

## Instances

### AddEnvTag

Add a Tag to RDS Instance.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance name
- Key (str) [REQUIRED]
  - Tag key
- Value (str) [REQUIRED]
  - Tag value

**Returns**

bool

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.AddEnvTag("postgres-aws","env","PROD")

print(data)
```

### CheckDBEnvVar

Check for the DB environment variable. If it's missing, you'll be prompted to enter its values.

**Prerequisites**:
- PostgreSQL Only

**Parameters**
- Type (str)
    - **Default**: postgres

**Returns**

Nothing

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
rds.CheckDBEnvVar()
```

### DelEnvTag

Delete a Tag from a RDS Instance.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance
- Key (str) [REQUIRED]
  - Tag Key

**Returns**

bool

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.AddEnvTag("postgres-aws","env")

print(data)
```

### DownloadLogs

Will download a rds log file locally.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance name.
- LogFile (str) [REQUIRED] 
  - RDS log file.
- DLoc (str) [REQUIRED]
  - The local file location.

**Returns**

Nothing

**Example**
```python
from AwsRds import AwsRds 

rds = AwsRds()
rds.DownloadLogs("postgres-aws","my_server_log","/tmp/logs"):
```

### DownloadSlowQueries

Download slow queries. 

**Prerequisites**:
- Aurora PostgreSQL engine
- `log_min_duration_statement` must be configured in the parameter group
- Instance timezone must be set to UTC
- Requires execution from within a Linux EC2 instance

**Parameters**
- instance (str) [REQUIRED]
  - The RDS instance name.
- logfile (str) [REQUIRED]
  - The RDS log file name.  
- dloc (str) [REQUIRED]
  - The destination location and file name.

**Returns**

Nothing

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.DownloadSlowQueries("postgres-aws","my_server_slow_log","/tmp/slowlogs/new_log)
```

### Exists

Check RDS to see if name exists.

**Parameters**
- Name (str) [REQUIRED]
  - RDS instance or cluster name
- IsCluster (bool)
  - Is this name a cluster 
  - **Default**: True

**Returns**

bool

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.Exists("postgres-aws")

print(data)
```

### GetInstance

Get all RDS Instances by engine.

**Parameters**
- Engine (str)
  - The RDS engine type to filter instances by.
  - **Default**: aurora-postgresql
- Active (bool)	
  - Filter only active instances
  - **Default**: False
- RetOut (bool)	
  - Print output to standard output
  - **Default**: False

**Returns**

Instance Names

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
instances = rds.GetInstance(engine="aurora-postgresql", active=True)
print(instances)
```

### GetInstanceByTag

Get RDS Instance by a Tag Value.

**Parameters**
- Key (str) [REQUIRED]
  - Tag Key
- Value (str) [REQUIRED]
  - Tag Value

**Returns**

list
[{InstanceName: Value, DBName: Value}]

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.GetInstanceByTag("env","PROD")

print(data)
```

### GetInstanceCluster

Get the RDS instance cluster name.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance name

**Returns**

RDS Cluster Name

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.CheckDBEnvVar("postgres-aws")

print(data)
```

### GetModifiedLogs

Will get the RDS log file names that have been modified within a period.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance name.
- Mins (int)
  - Number of minutes prior to check.
  - **Default**: 5
- ShowBlankFile (bool)
  - Show a file if it is empty
  - **Default**: False

**Returns**

RDS Log File Name

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
logs = rds.GetModifiedLogs(instance="postgres-aws")
print(logs)
```

### GetSnapshotByInstance

Get a RDS Snapshot for an RDS Instance.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS instance
- RetOut (bool)
  - Return Standard Output
  - **Default** = False

**Returns**

list
[{Snapshot: Value, Snapshot Date: Value}]

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.GetSnapshotByInstance("postgres-aws")

print(data)
```

### GetTopSnapshot

Get top RDS snapshot for an instance or all instances.
The function will get the lastest or earliest snapshot for an instance.

**Parameters**
- InstanceName (str)
  - RDS instance name
  - **Default** = ALL
- SortOrder (str)
  - The sort order
  - Options
    - ASC (ascending order) 
    - DESC (descending order)
  - **Default** = ASC (ascending order)

**Returns**

str
Snapshot Name

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.GetTopSnapshot("postgres-aws")

print(data)
```

### InstanceAction

Perform an action on an RDS Instance.

**Parameters**
- Instance (str) [REQUIRED]
  - RDS Instance Name
- Action (str) [REQUIRED]
  - Action to perform
  - **Options**
    - Start = Start an Instance
    - Stop = Stop an Instance

**Returns**

Nothing

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
rds.InstanceAction("postgres-aws","Start")
```

### SnapshotExists

Check to see if a RDS snapshot exists.

**Parameters**
- SnapshotName (str) [REQUIRED]
  - RDS Snapshot name 

**Returns**

bool

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.SnapshotExists("postgres-ss")

print(data)
```

### Status

Check to see if RDS is running.

**Parameters**
- Name (str) [REQUIRED]
  - RDS instance or cluster name.
- IsCluster (bool) 
  - Is this name a cluster
  - **Default**: True
- RtnText (bool)
  - Return text only
  - **Default**: False

**Returns**

bool or str

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.Status("postgres-aws")

print(data)
```

### TailLogs

Tail a specific RDS log.

**Parameters**
- Instance (str) [REQUIRED]
  - The RDS instance name.
- LogFile (str) [REQUIRED]
  - The RDS log file name.  

**Returns**

RDS Log File Data

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
data = rds.TailLogs("postgres-aws","my_server_log")

print(data)
```

### UploadToS3

Will upload a local file to an S3 bucket.

**Parameters**
- FileLoc (str) [REQUIRED]
  - File location of the file you want to upload.
- BucketName (str) [REQUIRED]
  - The s3 bucket name. *Please note this is only the top level bucket.*
- DestFileLoc (str) [REQUIRED]
  - The s3 location and file name.
  - Examples
    - File Only Copy
      - Windows
        - `uploadtos3("c:\\temp\\log.txt","testbucket","log.txt")`
      - Linux
        - `uploadtos3("/temp/log.txt","testbucket","log.txt")`

**Returns**

Nothing

**Example**

```python
from AwsRds import AwsRds 

rds = AwsRds()
rds.UploadToS3("/temp/log.txt","testbucket","log.txt")
```
