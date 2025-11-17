import sys
import boto3
import time
import os
from datetime import datetime
from datetime import timedelta


class AwsRds:

    def __init__(self,profile="default",region="us-east-1"):       
        self.profile = profile
        self.region = region
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.rds = self.session.client('rds')

    def GetInstance(self,Engine:str = "aurora-postgresql",Active: bool = False,RetOut: bool = False):
        '''
        Get all RDS Instance by engine.

        Parameters:
            Engine - RDS instance type (default: aurora-postgresql).
            Active - Check for only available instances True/False.  
            RetOut - Standard Output True/False.  
        Returns
            Instance Names
        '''
        
        valarr = []

        #Describe DB Instances
        data = self.rds.describe_db_instances()

        cnt=len(data['DBInstances'])

        for x in range(cnt):
            if Active:
                if (data['DBInstances'][x]['Engine'] == Engine) and (data['DBInstances'][x]['DBInstanceStatus'] == "available"):
                    valarr.append(data['DBInstances'][x]['DBInstanceIdentifier'])
            else:
                if (data['DBInstances'][x]['Engine'] == Engine):
                    valarr.append(data['DBInstances'][x]['DBInstanceIdentifier'])

        retval = valarr

        if RetOut:
            sys.stdout.write(" ".join(retval))

        return retval

    def GetModifiedLogs(self,Instance,Mins: int = 5,ShowBlankFile: bool = False):
        '''
        Will get the RDS log file names that have been modified within a period.

        Parameters:
            Instance - RDS instance name.
            Mins - number of mins prior to check (default: 5 mins).
                Default = 5 (5 mins)
            ShowBlankFile - Show a file if it is empty.
                Options are 0 (No) and 1 (Yes).  
                Default = 0 (No)
        Returns
            RDS Log File Name
        '''  	

        valarr = []

        # CONVERT TIME TO EPOCH/POSIX MILLISECONDS
        st = datetime.now() - timedelta(minutes=Mins)
        epoch = time.mktime(st.timetuple())*1e3 + st.microsecond/1e3

        data = self.rds.describe_db_log_files(
            DBInstanceIdentifier=Instance,
            FileLastWritten=int(epoch)
            )

        cnt=len(data['DescribeDBLogFiles'])	

        for x in range(cnt):
            if (ShowBlankFile == False): 
                if (data['DescribeDBLogFiles'][x]['Size'] > 0):
                    valarr.append(data['DescribeDBLogFiles'][x]['LogFileName'])
            else:
                valarr.append(data['DescribeDBLogFiles'][x]['LogFileName'])

        return valarr

    def DownloadLogs(self,Instance: str,LogFile: str,DLoc: str):
        '''
        Will download a rds log file locally.

        Parameters:
            Instance - RDS instance name.
            LogFile - RDS log file.
            DLoc - The local file location.

        Returns
            Nothing
        '''  		

        # DOWNLOAD LOG
        data = self.rds.download_db_log_file_portion(
            DBInstanceIdentifier=Instance,
            LogFileName=LogFile
            )

        # OPEN LOGFILE AND OVERWRITE
        with open(DLoc, "w+") as f:
            f.write(data.get("LogFileData", ""))

    def UploadToS3(self,FileLoc: str,BucketName: str,DestFileLoc: str):
        '''
        Will upload a local file to an S3 bucket.

        Parameters:
            FileLoc: - File location of the file you want to upload.
            BucketName - The s3 bucket name.  
                please note this is only the top level bucket.
            DestFileLoc: - The s3 location and file name.
                Examples
                    File Only Copy
                    Windows
                        uploadtos3("c:\\temp\\log.txt","testbucket","log.txt")

                    Linux
                        uploadtos3("/temp/log.txt","testbucket","log.txt")
        Returns
        Nothing
        '''  		

        #LOAD S3 RESOURCE
        s3 = boto3.resource('s3')

        #UPLOAD FILE
        s3.meta.client.upload_file(FileLoc,BucketName,DestFileLoc)

    def TailLogs(self,Instance: str,LogFile: str):
        '''
        Tail a specific RDS log.

        Parameters:
            Instance: - The RDS instance name.
            LogFile: - The RDS log file name.  

        Returns
        RDS Log File Data
        '''  

        data = self.rds.download_db_log_file_portion(
            DBInstanceIdentifier=Instance,
            LogFileName=LogFile
            )	

        return data

    def DownloadSlowQueries(self,Instance: str,LogFile: str,DLoc: str):
        '''
        Download slow queries.

        Parameters:
            Instance: - The RDS instance name.
            LogFile: - The RDS log file name.  
            DLoc: - The destination location and file name.

        Returns
        RDS slow queries 
        '''  

        data = self.rds.download_db_log_file_portion(
            DBInstanceIdentifier=Instance,
            LogFileName=LogFile
            )

        val = ''
        cnt = 1
        slowquery = []

        ####################################################################################################
        ## GET THE LOG DATA INTO A TMP FILE
        ## THE TEMP FILE WILL ALWAYS BE OVERWRITTEN
        ####################################################################################################

        parse=str(data['LogFileData'])
        tmpfilename = "/var/scripts/db/aurora/slowqueries/files/tmplog"
        tmpfile = open(tmpfilename,"w+")
        tmpfile.write(parse)
        tmpfile.close()

        ####################################################################################################
        ## GET THE SLOW QUERIES
        ## LOOP TO GET THE VALUES NEEDED FROM THE TMP FILE
        ####################################################################################################

        with open(tmpfilename) as fp:
            line = fp.readline()
            cnt = 1
            
            while line:
                dur = str.find(line,'duration:')
                par = str.find(line,"parameters:")
                x = 0

                if(dur > 0 or par > 0):
                    val = (line.strip())
                    while x == 0:
                        line = fp.readline()
                        #NO NEW LINES
                        if (line[20:24] == "UTC:"):
                            x=1
                        #YES NEW LINES
                        elif (line[20:24] != "UTC:"):
                            val = val + line
                            x = 0
                        #BLANK LINE EXIT LOOP
                        if(line == ''):
                            x = 1
                else:
                    line = fp.readline()
                
                if (val != ''):
                    slowquery.append(val)

                cnt += 1
                dur = ''
                par = ''
                val = ''

        #REMOVE TMPFILE
        if os.path.exists(tmpfilename):
            os.remove(tmpfilename)

        ####################################################################################################
        ## LOAD THE SLOW QUERY DATA INTO THE SLOW QUERY LOG
        ####################################################################################################

        sqcnt = len(slowquery)

        #IF THE FILE EXIST REMOVE IT TO REPLACE IT
        fexist=os.path.isfile(DLoc)
        if (fexist == True):
            os.remove(DLoc)

        #OPEN LOGFILE AND APPEND
        with open(DLoc, "a") as logfile:
            for x in range(sqcnt):
                line = str.strip(slowquery[x])
                print(line)
                logfile.write(line + "\n")

    def Exists(self,Name: str,IsCluster: bool = True):
        '''
        Check RDS to see if it exists.

        Parameters:
            Name - RDS instance or cluster name.
            IsCluster - Is this name a cluster 
                Options
                    True
                    False
                Default
                    True

        Returns
            True/False
        '''
        #GET ALL CLUSTERS
        cludata = self.rds.describe_db_clusters()
        cnt=len(cludata['DBClusters'])
        cluster_filldata = []

        for x in range(cnt):
            cluster_filldata.append(cludata['DBClusters'][x]['DBClusterIdentifier'])

        #GET ALL INSTANCES
        srvdata = self.rds.describe_db_instances()
        cnt=len(srvdata['DBInstances'])
        instance_filldata = []

        for x in range(cnt):
            instance_filldata.append(srvdata['DBInstances'][x]['DBInstanceIdentifier'])

        if IsCluster:
            if (Name in cluster_filldata):
                retval=True
            else:
                retval=False
        else:
            if (Name in instance_filldata):
                retval=True
            else:
                retval=False

        return retval

    def Status(self,Name: str,IsCluster: bool = True,RtnText: bool = False):
        '''
        Check to see if RDS is running.

        Parameters:
            Name - RDS instance or cluster name.
            Iscluster - Is this name a cluster 
                Options
                    True
                    False
            RtnText - Return text only.  
                Default = False

        Returns
            True/False
        '''
        ###############################################################################################################
        ##  RDS GET EVENTS
        ##
        ##  LOOKING FOR SERVER REBOOTS IN THE LAST 5 MINS (INPUT PARAMETER: IMIN)
        ###############################################################################################################

        if IsCluster:
            if self.Exist(name=Name):
                srvdata=self.rds.describe_db_clusters(
                    DBClusterIdentifier=Name
                )

                cnt=len(srvdata['DBClusters'])

                for x in range(cnt):
                    if (srvdata['DBClusters'][x]['Status'] == 'available') or (srvdata['DBClusters'][x]['Status'] == 'backing-up'):
                        if RtnText:
                            retval = srvdata['DBClusters'][x]['Status']
                        else:
                            retval=True
                    else:
                        if RtnText:
                            retval = srvdata['DBClusters'][x]['Status']
                        else:
                            retval=False
            else:
                retval=False
        else:
            if self.Exist(name=Name,iscluster=False):
                srvdata=self.rds.describe_db_instances(
                    DBInstanceIdentifier=Name
                )

                cnt=len(srvdata['DBInstances'])

                for x in range(cnt):
                    if (srvdata['DBInstances'][x]['DBInstanceStatus'] == 'available') or (srvdata['DBInstances'][x]['DBInstanceStatus'] == 'backing-up'):
                        if RtnText:
                            retval = srvdata['DBInstances'][x]['DBInstanceStatus']
                        else:
                            retval=True
                    else:
                        if RtnText:
                            retval = srvdata['DBInstances'][x]['DBInstanceStatus']
                        else:
                            retval=False
            else:
                retval=False

        return retval

    def CheckDBEnvVar(self,Type: str = "postgres"):
        '''
        Check for the DB environment variable. If it's missing, you'll be prompted to enter its values.\n
        **CURRENTLY ONLY POSTGRES**

        Parameters:
            Type - Type of DB server 
        '''	

        iswin = (os.name)
        local_path = (os.environ['PATH'])

        if iswin == "nt":
            if Type.lower() in ["postgres", "postgresql"]:
                if str(local_path).find("PostgreSQL") == -1:
                    os.system("cls")

                    print("The Local PostgreSQL Variable Path Does Not Exist!!!" + '\n')
                    print("In order for this script to work you must have PostgreSQL installed locally and have the environment path set" + '\n')
                    print("You can provide a temporary path for this run." + '\n')
                    print("Example Path: C:\\Program Files\\PostgreSQL\\10\\bin" + '\n')
                    pg_path = input("Please enter your PostgreSQL path: ")
                        
                    if os.path.exists(pg_path) == False:
                        print("Directory Does Not Exist!!!")
                        sys.exit()
                    else:
                        print("Adding Path to Environment Variables")
                        try:
                            os.environ["PATH"] = os.environ["PATH"] + pg_path
                        except OSError as e:
                            print("Error: {0}".format(e))
                            sys.exit()
                    print("Temporary path added...Attempting DB Creation")
                    time.sleep(2)
                        
                    os.system("cls")

    def GetInstanceCluster(self,Instance: str):
        '''
        Get the RDS instance cluster name.

        Parameters:
            Instance - RDS instance.

        Returns
            RDS Cluster Name
        '''	
        ####################################################################################################
        ##  GET ALL CLUSTERS
        ####################################################################################################

        #CLUSTER
        cludata = self.rds.describe_db_clusters()
        cnt=len(cludata['DBClusters'])
        cluster_filldata = []

        for x in range(cnt):
            cluster_filldata.append(cludata['DBClusters'][x]['DBClusterIdentifier'])

        ####################################################################################################
        ##  CHECK FOR CURRENT CLUSTER
        ####################################################################################################

        cnt=len(cludata['DBClusters'])
        for x in range(cnt):
            clu_mem=len(cludata['DBClusters'][x]['DBClusterMembers'])
            for y in range(clu_mem):
                if str(cludata['DBClusters'][x]['DBClusterMembers'][y]['DBInstanceIdentifier']) == Instance:
                    return(cludata['DBClusters'][x])

    def AddEnvTag(self,Instance: str,Key: str,Value: str):
        '''
        Add a Tag to RDS Instance.

        Parameters:
            Instance - RDS instance
            Key - Tag Key
            Value - Tag Value

        Returns
            True/False
        '''	

        #GET CLUSTER
        CluData = self.GetInstanceCluster(Instance)

        #GET INSTANCE
        InsData = self.rds.describe_db_instances(DBInstanceIdentifier=Instance)

        try:
            if CluData != None:
                clu_arn = CluData['DBClusterArn']
                self.rds.add_tags_to_resource(ResourceName=clu_arn,Tags=[{'Key': Key, 'Value': Value}])

            if InsData != None:
                ins_arn = InsData['DBInstances'][0]['DBInstanceArn']
                self.rds.add_tags_to_resource(ResourceName=ins_arn,Tags=[{'Key': Key, 'Value': Value}])

            print(f"Tag Key={Key}, Value={Value} added to {Instance}")
            return True

        except BaseException as e:
            print(f"ERROR: \n{e}")
            return False

    def DelEnvTag(self,Instance: str,Key: str):
        '''
        Delete a Tag from a RDS Instance.

        Parameters:
            InstanceName - RDS instance
            Key - Tag Key

        Returns
            Nothing
        '''	

        #GET CLUSTER
        CluData = self.GetInstanceCluster(Instance)

        #GET INSTANCE
        InsData = self.rds.describe_db_instances(DBInstanceIdentifier=Instance)

        try:
            if CluData != None:
                clu_arn = CluData['DBClusterArn']
                self.rds.remove_tags_from_resource(ResourceName=clu_arn,TagKeys=[Key])

            if InsData != None:
                ins_arn = InsData['DBInstances'][0]['DBInstanceArn']
                self.rds.remove_tags_from_resource(ResourceName=ins_arn,TagKeys=[Key])

            print(f"Tag Key = {Key} was removed from {Instance}")
            return True

        except BaseException as e:
            print("ERROR: \n{0}".format(e))
            return False

    def GetInstanceByTag(self,Key: str,Value: str):
        '''
        Get RDS Instance by a Tag Value.

        Parameters:
            Key - Tag Key
            Value - Tag Value

        Returns
            InstanceName: [], DBName: []
        '''		

        #GET INSTANCE
        InsData = self.rds.describe_db_instances()

        #NUMBER OF INSTANCES
        cnt=len(InsData['DBInstances'])

        #RETURN VALUE
        RetData = []

        for x in range(cnt):
            InsArn = InsData['DBInstances'][x]['DBInstanceArn']
            InsName = InsData['DBInstances'][x]['DBInstanceIdentifier']
            TagData = self.rds.list_tags_for_resource(ResourceName=InsArn)
            TagList = TagData['TagList']
            
            for tag in TagList:
                if Value == "":
                    if tag['Key'] == Key:
                        RetData.append({"InstanceName": InsName, "DBName": tag['Value']})
                else:
                    if tag['Key'] == Key and tag['Value'] == Value:
                        RetData.append({"InstanceName": InsName, "DBName": tag['Value']})

        return RetData

    def GetSnapshotByInstance(self,Instance: str,RetOut: bool = False):
        '''
        Get a RDS Snapshot for an RDS Instance.

        Parameters:
            InstanceName - RDS instance
            Profile - AWS profile name
                Default = Blank
                    Blank will be default AWS Profile
            RetOut - Return Standard Output
                Default = 0

        Returns
            Snapshot: [], Snapshot Date: []
        '''		
        ####################################################################################################
        ##  GET ALL CLUSTERS & INSTANCES
        ####################################################################################################

        CluData = self.GetInstanceCluster(Instance)
        CluName = CluData['DBClusterIdentifier']

        ####################################################################################################
        ##  GET AUTOFILL SNAPSHOTS
        ####################################################################################################

        srvdata = self.rds.describe_db_cluster_snapshots(DBClusterIdentifier = CluName)
        cnt=len(srvdata['DBClusterSnapshots'])
        ss_data = []
        ss_retout = []

        for x in range(cnt):
            ss_name = srvdata['DBClusterSnapshots'][x]['DBClusterSnapshotIdentifier']
            ss_date = srvdata['DBClusterSnapshots'][x]['SnapshotCreateTime']
            ss_data.append({"Snapshot": ss_name, "Snapshot Date": str(ss_date)})
            ss_retout.append(ss_name)
        
        if RetOut:
            sys.stdout.write(" ".join(ss_retout))

        return ss_data

    def InstanceAction(self,Instance: str,Action: str):
        '''
        Perform an action on an RDS Instance.

        Parameters:
            Instance - RDS Instance Name
            Action - Action to perform
                Options
                    Start = Start an Instance
                    Stop = Stop an Instance
            Profile - AWS profile name
                Default = Blank
                    Blank will be default AWS Profile

        Returns
            Message of the action performed.
        '''			

        ####################################################################################################
        ##  CHECK IF INSTANCE EXISTS
        ####################################################################################################

        ins_run = self.Exist(Instance,0)

        if ins_run ==0:
            print('\n' + "ERROR: INSTANCE DOES NOT EXIST!!!" + '\n')
            sys.exit(1)

        ####################################################################################################
        ##  CHECK TO SEE IF INSTANCE & CLUSTER IS RUNNING
        ####################################################################################################

        #GET CURRENT CLUSTER
        clu_data = self.GetInstanceCluster(Instance)

        if clu_data != "None":
            clu_name = clu_data['DBClusterIdentifier'] 
            isclu = True
        else:
            isclu = False

        clu_run = self.Status(clu_name,True)
        ins_run = self.Status(Instance,False)

        ####################################################################################################
        ##  PROD PROTECTION
        ####################################################################################################

        prod_ins = []

        if Instance in prod_ins:
            print('\n' + "ERROR: PRODUCTION INSTANCE DBs CAN NOT BE STOP OR STARTED VIA THIS SCRIPT!!!" + '\n')
            sys.exit(1)
        elif clu_name in prod_ins:
            print('\n' + "ERROR: PRODUCTION INSTANCE DBs CAN NOT BE STOP OR STARTED VIA THIS SCRIPT!!!" + '\n')
            sys.exit(1)

        ####################################################################################################
        ##	PERFORM ACTION 
        ####################################################################################################

        if str(Action).lower() == "stop":
            if isclu and clu_run:
                print(f"Stopping Cluster {clu_name}")
                self.rds.stop_db_cluster(DBClusterIdentifier=clu_name)

                run = ""
                while run != "stopped":
                    time.sleep(10)
                    run = self.rds.Status(clu_name,1,1)

            elif (isclu == 0) and (ins_run == 1):
                print(f"Stopping Instance {Instance}")
                self.rds.stop_db_instance(DBInstanceIdentifier=Instance)

                run = ""
                while run != "stopped":
                    time.sleep(10)
                    run = self.rds.Status(Instance,0,1)

            print(f"Instance {Instance} is stopped")

        elif str(Action).lower() == "start":
            if isclu and clu_run == False:
                print("Starting Cluster " + clu_name)
                self.rds.start_db_cluster(DBClusterIdentifier=clu_name)

                run = ""
                while run != "available":
                    time.sleep(10)
                    run = self.Status(clu_name,1,1)	

            elif isclu == False and ins_run == False:
                print(f"Starting Instance {Instance}")
                self.rds.start_db_instance(DBInstanceIdentifier=Instance)	

                run = ""
                while run != "available":
                    time.sleep(10)
                    run = self.Status(Instance,0,1)
            
            print(f"Instance {Instance} is available")	

    def GetTopSnapshot(self, InstanceName: str = "ALL",SortOrder: str = "ASC"):
        '''
        Get top RDS snapshot for an instance or all instances.
        The function will get the lastest or earliest snapshot for an instance.

        Parameters:
            InstanceName - RDS instance name 
                Default = ALL
            SortOrder - The sort order.  
                Options are ASC (ascending order) and DESC (descending order).  
                Default = ASC (ascending order)
            Profile - The AWS profile to be used.  
                Default = default
        Returns
            Snapshot Name
        '''   
        ####################################################################################################
        ##  GET THE INSTANCE DATA
        ####################################################################################################

        if str(InstanceName).lower() == "all":
            westss = self.rds.describe_db_cluster_snapshots()
        else:
            CluData = self.GetInstanceCluster(InstanceName)
            CluName = CluData['DBClusterIdentifier']

            westss = self.rds.describe_db_cluster_snapshots(DBClusterIdentifier=CluName)
        
        ####################################################################################################
        ##  GET THE INSTANCE DATA
        ####################################################################################################

        cnt=len(westss['DBClusterSnapshots'])
        max_dt = ""
        max_ss = ""

        for x in range(cnt):
            ss_name = westss['DBClusterSnapshots'][x]['DBClusterSnapshotIdentifier']
            ss_date = westss['DBClusterSnapshots'][x]['SnapshotCreateTime']
            
            if max_dt == "":
                max_dt = ss_date

            if str(SortOrder).lower() == "desc":
                #DESC ORDER
                if ss_date >= max_dt:
                    max_ss = ss_name
                    max_dt = ss_date
            else:
                #ASC ORDER
                if ss_date <= max_dt:
                    max_ss = ss_name
                    max_dt = ss_date			

        return max_ss

    def SnapshotExists(self, SnapshotName: str):
        '''
        Check to see if a RDS snapshot exists.

        Parameters:
            SnapshotName - RDS Snapshot name 
        Returns
            True = exists
            False = not exists
        '''  

        ####################################################################################################
        ##  GET SNAPSHOT DATA
        ####################################################################################################

        snap = self.rds.describe_db_cluster_snapshots()

        ####################################################################################################
        ##  CHECK FOR SNAPSHOT
        ####################################################################################################

        cnt=len(snap['DBClusterSnapshots'])

        ss_exist = False

        for x in range(cnt):
            ss_name = snap['DBClusterSnapshots'][x]['DBClusterSnapshotIdentifier']
            
            #DESC ORDER
            if SnapshotName == ss_name:
                ss_exist = True
                break

        return ss_exist
