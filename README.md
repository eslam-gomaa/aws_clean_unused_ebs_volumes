
# AWS - Clean unused disks [ Python Script ]

<br>

A Python script that deletes AWS EBS Volumes in the `available` state (unused)

> At least Python 3.6 is needed

<br>

Currently the script filters the Volumes to be deleted based on:

1. The state ('available')

2. The last detach event history

<br>

---

<br>

## Usage


Currently, we need to put the credentials in the script (Temporarly, will be modified later)

```python
self.region = 'us-east-1'
self.access_key = '*****'
self.secret_key = '*****'
```

<br>


### 2. Run the script


```bash
python3.6 aws_disks.py
```


---

### Example 1

> Deleting the Volumes that match the 'last_detach_event_age' filter
>
> For testing we set the filter to 0 (means include the Volumes that were detached today)

```

eslam@kvm-development-eslam-gomaa:~/work_dir/aws_clean_available_disks$ 🍉 python3.6 aws_disks.py 

> Number of found volumes in the 'available' state: 5
> Volumes total size: 500gb
> Deleting EBS Volumes in the 'available' state with detach history older than or equal to '0' days

+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+
| ID                    | AZ         | State     | Size   | Type   | Encrypted   | Creation Time                    | Detach Events   | Last Detach Info                       |
+=======================+============+===========+========+========+=============+==================================+=================+========================================+
| vol-0b3c7847bc162230b | us-east-1a | available | 100gb  | io2    | False       | 2022-05-15 12:58:53.195000+00:00 | True            | Detach_time: 2022-05-15 13:06:01+00:00 |
|                       |            |           |        |        |             |                                  |                 | Username: cloud_user                   |
|                       |            |           |        |        |             |                                  |                 | AccessKey: ASIAWKVW3GBOMPILDJAF        |
|                       |            |           |        |        |             |                                  |                 | Instance_ID: i-07aa98be82db530da       |
|                       |            |           |        |        |             |                                  |                 | Device: /dev/sdd                       |
|                       |            |           |        |        |             |                                  |                 | Datachment age in days: 0              |
+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+
| vol-0a0f81b9a534ed8d5 | us-east-1a | available | 100gb  | gp2    | False       | 2022-05-15 13:03:04.093000+00:00 | True            | Detach_time: 2022-05-15 13:05:48+00:00 |
|                       |            |           |        |        |             |                                  |                 | Username: cloud_user                   |
|                       |            |           |        |        |             |                                  |                 | AccessKey: ASIAWKVW3GBOMPILDJAF        |
|                       |            |           |        |        |             |                                  |                 | Instance_ID: i-07aa98be82db530da       |
|                       |            |           |        |        |             |                                  |                 | Device: /dev/sdf                       |
|                       |            |           |        |        |             |                                  |                 | Datachment age in days: 0              |
+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+
| vol-0b550c52a319b288f | us-east-1a | available | 100gb  | gp2    | False       | 2022-05-15 13:03:53.962000+00:00 | True            | Detach_time: 2022-05-15 13:05:48+00:00 |
|                       |            |           |        |        |             |                                  |                 | Username: cloud_user                   |
|                       |            |           |        |        |             |                                  |                 | AccessKey: ASIAWKVW3GBOMPILDJAF        |
|                       |            |           |        |        |             |                                  |                 | Instance_ID: i-07aa98be82db530da       |
|                       |            |           |        |        |             |                                  |                 | Device: /dev/sdg                       |
|                       |            |           |        |        |             |                                  |                 | Datachment age in days: 0              |
+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+
| vol-040c1f0a0117bdd86 | us-east-1a | available | 100gb  | io1    | False       | 2022-05-15 13:04:02.110000+00:00 | True            | Detach_time: 2022-05-15 13:05:48+00:00 |
|                       |            |           |        |        |             |                                  |                 | Username: cloud_user                   |
|                       |            |           |        |        |             |                                  |                 | AccessKey: ASIAWKVW3GBOMPILDJAF        |
|                       |            |           |        |        |             |                                  |                 | Instance_ID: i-07aa98be82db530da       |
|                       |            |           |        |        |             |                                  |                 | Device: /dev/sdh                       |
|                       |            |           |        |        |             |                                  |                 | Datachment age in days: 0              |
+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+
| vol-02a2c00125e429fe4 | us-east-1a | available | 100gb  | io2    | False       | 2022-05-15 13:04:10.098000+00:00 | True            | Detach_time: 2022-05-15 13:05:48+00:00 |
|                       |            |           |        |        |             |                                  |                 | Username: cloud_user                   |
|                       |            |           |        |        |             |                                  |                 | AccessKey: ASIAWKVW3GBOMPILDJAF        |
|                       |            |           |        |        |             |                                  |                 | Instance_ID: i-07aa98be82db530da       |
|                       |            |           |        |        |             |                                  |                 | Device: /dev/sdi                       |
|                       |            |           |        |        |             |                                  |                 | Datachment age in days: 0              |
+-----------------------+------------+-----------+--------+--------+-------------+----------------------------------+-----------------+----------------------------------------+

WARNING -- Confirm before deleting the listed volumes: 

yes || no 

yes: Run & continue
no:  Abort
YOUR Decision: yes
> Ok .. Let's continue ...

INFO -- Deleting Volumes:
> Volume vol-0b3c7847bc162230b deleted successfully
> Volume vol-0a0f81b9a534ed8d5 deleted successfully
> Volume vol-0b550c52a319b288f deleted successfully
> Volume vol-040c1f0a0117bdd86 deleted successfully
> Volume vol-02a2c00125e429fe4 deleted successfully

* A double Check; Current Volumes in the 'available' state is: 0
> Volumes cleaned successfully
```

<br>

---

<br>

## Examples

<a id="Examples"></a>


### Example 2

> In this example, we set the 'last_detach_event_age' to 30 days
>
> Hence, the disks that were detached today are skipped

```
eslam@kvm-development-eslam-gomaa:~/work_dir/aws_clean_available_disks$ 🍉 python3.6 aws_disks.py 
DEBUG -- Skiping Volume: 'vol-0b3c7847bc162230b' => Last detach event age is: '0' days which is less than what we need: '30' days
DEBUG -- Skiping Volume: 'vol-0a0f81b9a534ed8d5' => Last detach event age is: '0' days which is less than what we need: '30' days
DEBUG -- Skiping Volume: 'vol-0b550c52a319b288f' => Last detach event age is: '0' days which is less than what we need: '30' days
DEBUG -- Skiping Volume: 'vol-040c1f0a0117bdd86' => Last detach event age is: '0' days which is less than what we need: '30' days
DEBUG -- Skiping Volume: 'vol-02a2c00125e429fe4' => Last detach event age is: '0' days which is less than what we need: '30' days
INFO -- Number of disks in the 'available' state is 0
> No need to continue
```

