
import boto3
import botocore
import time
from datetime import datetime, timezone
from tabulate import tabulate
import json

# pip3 install boto3
# pip3 install tabulate
class clean_AWS_unused_volumes:
    """
    class to clean AWS volumes in the 'available' state
    """
    def __init__(self):
        self.region = 'us-east-1'
        self.access_key = 'AKIA3DU6IGM577NR6G4I'
        self.secret_key = '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'
        self.ask_before_delete = True
        self.ec2_client = None
        self.cloudTrail_client = None
        self.pricing_client = None
        self.available_volumes_dct = None
        self.volume_state_to_filter = 'available'
        # The number of the days that the last "volume detach event" must be older than or equal to them.
        self.last_detach_age_days_filter = 30
        self.dry_run = False
        self.debug = True


    def authenticate_ec2(self):
        """
        Authenticate with AWS (EC2 service)
        """
        self.ec2_client = boto3.client(
        service_name='ec2',
        aws_access_key_id = self.access_key,
        aws_secret_access_key = self.secret_key,
        region_name = self.region
        )

    def authenticate_cloudTrail(self):
        """
        Authenticate with AWS (CloudTrail service)
        """
        self.cloudTrail_client = boto3.client(
        service_name='cloudtrail',
        aws_access_key_id = self.access_key,
        aws_secret_access_key = self.secret_key,
        region_name = self.region
        )

    def list_available_volumes(self):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_volumes
        
        Lists all volumes of all VMs
        - Return: a dict of 2 items
            1. count: (int)    ->  number of disks
            2. total_volumes_size: (int)  -> The total size of Volumes in GB
            3. volumes: (dct)  ->  contains the volumes as a dictionary of dictionaries [where the volume_id is the key & the info are the value]
        """
        if self.ec2_client is None:
            self.authenticate_ec2()
        try:
            # Get the list of Volumes filtered with the state 'available'
            volumes = self.ec2_client.describe_volumes(Filters=[{'Name': 'status','Values': [self.volume_state_to_filter]}]).get('Volumes')

            # Counter to count the number of disks
            cnt = 0
            # Counter to count the total size number of the disks
            total_size = 0

            volumes_dct = {}

            # Loop over the Volumes (original result) & get the information that we need
            for v in volumes:
                # Get the ID of the Volume
                id = v.get('VolumeId')
                
                there_are_detach_events = False
                # Lookup the "detach event"s for each Volume with "CloudTrail"
                detach_event = self.cloud_trail_lookup_events(volume_id=id)
                
                ### The maximum number of days for CloudTrail event history  ### 
                # By default, CloudTrail stores the events history for 90 days.
                # https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events-console.html
                last_detach_age_days = 90

                # If the number of "CloudTrail detach events" is > 0; then do the following
                if len(detach_event) > 0:
                    there_are_detach_events = True
                    # Get the current time
                    current_time = datetime.now((timezone.utc))
                    # Subtruct the current time for the last detach event time to get the detach event age.
                    detach_age = current_time - detach_event[0].get('event_time') # Last detach event time
                    # Get the detach events times in minutes, hours, days
                    last_detach_age_minutes = int(detach_age.total_seconds() / 60)
                    last_detach_age_hours = int(last_detach_age_minutes / 60)
                    # Update "last_detach_age_days" var with the correct "last detach event age in days"
                    last_detach_age_days = int(last_detach_age_minutes / 1440)


                ### Filter the Volumes by the "last detachment event age in days" ###
                # If the "actual last detach event of the Volume" is greater than or equal to "last detach filter in days" (User input)' ↩
                # Then consider the Volume (add the Volume to the dictionary)
                ### For example => If the last detach event age of the Volume is 40 days and we filter by 30 days (means last event old must be >= 30):
                ### In this case the last detach event history of the volume (40 days) is older than we need (30 days) -> so the Volume will be added to the list.
                ### But if the last detach event age of the Volume is 19 days and we filter by 30 days:
                ### In this case the last detach event history of the volume (19) is less than what we need (30) -> Hence the Volume will be skipped.
                if last_detach_age_days >= self.last_detach_age_days_filter:
                    # Create a new dictionary for each Filtered Volume
                    volumes_dct[id]= {}
                    # Add the Volume "general" info
                    volumes_dct[id]['state'] = v.get('State')
                    volumes_dct[id]['az'] = v.get('AvailabilityZone')
                    volumes_dct[id]['encrypted'] = v.get('Encrypted')
                    volumes_dct[id]['creation_time'] = v.get('CreateTime')
                    volumes_dct[id]['size'] = v.get('Size')
                    volumes_dct[id]['type'] = v.get('VolumeType')
                    if volumes_dct[id]['state'] == self.volume_state_to_filter:
                        # Increase the Volumes number by 1
                        cnt +=1
                        # Increment the Total disks size by the size of this Volume
                        total_size += volumes_dct[id]['size']

                    # If CloudTrail detach events were found, add these info as well.
                    if there_are_detach_events:
                        # detach_event[0] -> The first index has the last detach event.
                        volumes_dct[id]['detach_events'] = True
                        volumes_dct[id]['last_detach_event_time'] = detach_event[0].get('event_time')
                        volumes_dct[id]['last_detach_age_minutes'] = last_detach_age_minutes
                        volumes_dct[id]['last_detach_age_hours'] = last_detach_age_hours
                        volumes_dct[id]['last_detach_age_days'] = last_detach_age_days
                        volumes_dct[id]['last_detach_event_username'] = detach_event[0].get('username')
                        volumes_dct[id]['last_detach_event_access_key'] = detach_event[0].get('access_key')
                        volumes_dct[id]['last_detach_event_instance_id'] = detach_event[0].get('instance_id')
                        volumes_dct[id]['last_detach_event_device'] = detach_event[0].get('device')
                        volumes_dct[id]['last_detach_event_event_type'] = detach_event[0].get('event_type')
                    else:
                        volumes_dct[id]['detach_events'] = False
                else:
                    # If the last_detach_day_filter
                    if self.debug:
                        print(f"DEBUG -- Skiping Volume: '{id}' => Last detach event age is: '{last_detach_age_days}' days which is less than what we need: '{self.last_detach_age_days_filter}' days")

            out = {}
            out['count'] = cnt
            out['total_volumes_size'] = total_size
            out['volumes'] = volumes_dct
            return out
        except (TypeError,
               ValueError,
               AttributeError,
               botocore.exceptions.ClientError) as e:
            raise SystemExit(f"ERROR -- Failed to list volumes\n> {e}")

    def delete_ebs_volume(self, id, dry_run=False):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.delete_volume

        Deletes EBS volume
        Return: does NOT return
        """
        try:
            self.ec2_client.delete_volume(
            VolumeId=id,
            DryRun=dry_run)
            print(f"> Volume {id} deleted successfully")
        except (TypeError,
               ValueError,
               AttributeError) as e:
            raise SystemExit(f"ERROR -- Failed to delete Volume: {id}\n> {e}")

    def print_available_volumes_table(self):
        """
        Prints the found volumes in a table
        Return: does NOT return
        """
        ## get the list of available volumes in a dct
        if self.available_volumes_dct is None:
            self.available_volumes_dct = self.list_available_volumes()

        # The table Header
        table = [['ID', 'AZ', 'State', 'Size', 'Type', 'Encrypted', 'Creation Time', 'Detach Events', 'Last Detach Info']]
        # Print some statistics
        print()
        print(f"> Number of found volumes in the '{self.volume_state_to_filter}' state: {self.available_volumes_dct.get('count')}")
        print(f"> Volumes total size: {self.available_volumes_dct.get('total_volumes_size')}gb")
        print(f"> Deleting EBS Volumes in the '{self.volume_state_to_filter}' state with detach history older than or equal to '{self.last_detach_age_days_filter}' days" )
        print()
        # Loop over the filtered Volumes & collect some info to be printed in the table
        for id, info  in self.available_volumes_dct.get('volumes').items():
            if info['detach_events']:
                last_detach_info = f"""
Detach_time: {info['last_detach_event_time']}
Username: {info['last_detach_event_username']}
AccessKey: {info['last_detach_event_access_key']}
Instance_ID: {info['last_detach_event_instance_id']}
Device: {info['last_detach_event_device']}
Datachment age in days: {info['last_detach_age_days']}
        """
            else:
                last_detach_info = ' '
            row = [id, info['az'], info['state'], str(info['size']) + 'gb', info['type'], info['encrypted'], info['creation_time'], info['detach_events'], last_detach_info]
            table.append(row)

        out = tabulate(table, headers='firstrow', tablefmt='grid', showindex=False)
        # Print the table
        print(out)

    def ask_for_confirmation(self, msg="Confirm before deleting the listed volumes"):
        """
        Keeps asking for confirmation, till gets 'yes' or 'no' Input
        """
        options = ['yes', 'no']
        decision = None
        while decision not in options:
            confirm = input(
            "\nWARNING -- {}: \n".format(msg)
            + "\nyes || no \n\n"
            + "yes: Run & continue\n"
            + "no:  Abort\n"
            + "YOUR Decision: ")
            if confirm == 'yes':
                print("> Ok .. Let\'s continue ...\n")
                break
            elif confirm == 'no':
                print("> See you \n")
                exit(1)

    def cloud_trail_lookup_events(self, volume_id):
        """
        https://boto3.amazonaws.com/v1/documentation/api/1.9.42/reference/services/cloudtrail.html#CloudTrail.Client.lookup_events
        Method to get the CloudTrail detach events for specific EBS Volume
        INPUT:
            1. Volume ID  (String)
        RETURNS:
            1. list of dictionaries (List) (each dct is a detach event)
        """
        try:
            if self.cloudTrail_client is None:
                self.authenticate_cloudTrail()
            detach_events = []
            out = self.cloudTrail_client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'ResourceName',
                        'AttributeValue': volume_id
                    },
                ],
            )
            if len(out.get('Events')) == 0:
                # Then, no events found for the Volume
                # print(f"No events for Volume: {volume_id}")
                return []
            else:
                # If found events for the Volume
                for event in out.get('Events'):
                    info = {}
                    info['event_time'] = event['EventTime']
                    info['username'] = event['Username']
                    info['access_key'] = event['AccessKeyId']

                    CloudTrailEvent = json.loads(event.get('CloudTrailEvent'))
                    info['instance_id'] = CloudTrailEvent.get('requestParameters').get('instanceId')
                    info['force'] = CloudTrailEvent.get('requestParameters').get('force')
                    info['event_name'] = CloudTrailEvent.get('eventName')
                    info['device'] = CloudTrailEvent.get('responseElements').get('device')
                    if info['device'] is None:
                        info['device'] = 'Unknown'
                    info['event_type'] = CloudTrailEvent.get('eventType')
                    if info['event_name'] == 'DetachVolume':
                        detach_events.append(info)
                return detach_events
        except (botocore.exceptions.ClientError,
                TypeError,
               ValueError,
               AttributeError) as e:
            raise SystemExit(f"ERROR -- Failed to get events for Volume: {volume_id}\n> {e}")


    def clean(self):
        """
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.delete_volume

        Deletes volumes in the 'available' state
        INPUT: No inputs
        RETURNS: Nothing
        """
                
        ## Get the list of available volumes in a dct
        if self.available_volumes_dct is None:
            self.available_volumes_dct = self.list_available_volumes()

        # Abort if no Volumes were found
        if self.available_volumes_dct.get('count') < 1:
            print(f"INFO -- Number of disks in the '{self.volume_state_to_filter}' state is {self.available_volumes_dct.get('count')}")
            print("> No need to continue")
            exit(0)

        # Print the Volumes filter output in a table
        self.print_available_volumes_table()

        # Stop here if dry_run is True
        if self.dry_run:
            print("\n> [ DRY RUN ] Stopping Here. [ Skip volumes deletion ]")
            exit(0)

        # Ask for confirmation
        if self.ask_before_delete:
            self.ask_for_confirmation()

        # Delete the volumes
        print(f"INFO -- Deleting Volumes:")
        for volume_id in self.available_volumes_dct.get('volumes').keys():
            self.delete_ebs_volume(volume_id)
            time.sleep(0.3)

        # Update the 'self.available_volumes_dct' attribute
        self.available_volumes_dct = self.list_available_volumes()
        print(f"\n* A double Check; Current Volumes in the '{self.volume_state_to_filter}' state is: {self.available_volumes_dct.get('count')}")
        if self.available_volumes_dct.get('count') == 0:
            print("> Volumes cleaned successfully")
        else:
            print("> Something is wrong !")


clean_volumes = clean_AWS_unused_volumes()
clean_volumes.clean()
