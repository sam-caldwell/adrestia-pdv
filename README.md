Adrestia Post-Deployment Verification Service
=============================================
(c) 2019 Sam Caldwell.  All Rights Reserved. 

The workhorse post-deployment verification service (PDV) is a centralized source of truth for 
post-deployment verification results which can be used to report on the current health of the
build-deploy pipeline as well as to gate deployment once significant errors have been signaled
to the service.

Operations may submit PDV their state to the system via HTTP/POST and query the service for 
the health of the entire pipeline.  This makes the assumption that one failure should fail 
the entire system.  Until that test passes, or state is cleared, the system will block 
further work.  While a call to clear state will reset the block and could be used as a 
work-around, this is not the intended operation.  Clearing state is intended to start the 
process over again.


Usage
-----
####Clearing state
```
curl -X delete http://pdv:8999/clear
```
####Submitting a state
```
curl -X get http://pdv:8999/submit/<name>/<pass|fail>
```
####Querying the State
```
curl -X get http://pdv:8999/report
```

Starting the Container
----------------------
```angular2html
docker-compose up --detach
```

Versioning
----------
The solution is versioned as follows (updated by the build script for you).

```YYYY.MM.DD``` (where the date/time is set by ```bin/build.sh``` in UTC)

Why do this?  Well, how else should I know when the build was run?  I'm lazy.

Building
--------
To build the service, run ```./bin/build.sh```
Please do not update VERSION.txt or use docker-compose build directly.  See Versioning.

ToDo
----
* Emit logs to splunk (structured logs)
* Emit metrics to statsd for forwarding to monitoring svc.
