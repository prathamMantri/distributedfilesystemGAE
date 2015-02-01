# DFS on Google App Engine

###project summary
>In this project we have implemented distributed file system on GAE.
>Google app engine is a PAAS model. We don't have to worry about scaling on
>GAE. But some decison like where to store what file? how to maintain the 
>metadata has to be taken. We used blob store , memcache , datastore for this.
>if the file size is small it will be cached to increase the system throughput 
>and to reduce latency. Metadata is maintained in memcache and also written to
>datastore for recovery in case of any failures. We also implemented some 
>basic file system functionalities such as create,delete,lookup,clear/disable cache
>etc. We also ran scripts to test system perfomance by measuring throughput and latency

###files
- code/distdb.py contains main logic
- code/*.html    htmls for client operation such as create,delete.
- code/app.yaml  configuration file
