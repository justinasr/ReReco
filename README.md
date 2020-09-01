# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

## ReReco objects

There are four types of objects in ReReco machine: subcampaigns, requests, sequences and tickets. Sequences are parts of request and cannot exist independently.

### Subcampaigns

##### Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release for the subcampaign
* `energy` - energy in TeV
* `history` - action history of this object
* `memory` - memory in megabytes
* `notes` - free form user notes
* `prepid` - unique identifier in the ReReco machine, same as `_id`
* `runs_json_path` - relative path to JSON file that contains all runs, this value will be internally prepended with https://cms-service-dqm.web.cern.ch/cms-service-dqm/CAF/certification/
* `scram_arch` - scram architecture of CMSSW release, will be automatically fetched from https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1
* `sequences` - list of Sequence objects (or dictionaries) that hold attributes for cmsDriver commands

### Requests

Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release
* `completed_events` - completed (produced) events
* `energy` - energy in TeV
* `history` - action history of this object
* `input` - dictionary with two values:
    * `dataset` - dataset name that will be used as input
    * `request` - prepid of request that will be used as input when it is done. Last output dataset name of that request will be automatically copied to `dataset` field once it is known
* `memory` - memory in megabytes
* `notes` - free form user notes
* `output_datasets` - list of dataset names that are produced and saved by this request. This information is received after request is submitted to computing
* `prepid` - unique identifier in the ReReco machine, same as `_id`
* `priority` - priority of the job in computing
* `processing_string` - processing string
* `runs` - list of runs to be processed
* `sequences` - list of Sequence objects (or dictionaries) that hold attributes for cmsDriver commands
* `size_per_event` - required disk space for one event in kilobytes
* `status` - status of this request. Can be new, approved, submitting, submitted or done
* `subcampaign` - prepid of subcampaign (see Subcampaigns) that was used as a template for this request
* `time_per_event` - required time for one event in seconds
* `total_events` - total events to be processed (number from ReqMgr2)
* `workflows` - list of dictionaries that represent workflows in computing. Each dictionary has these values:
  * `name` - workflow name
  * `output_datasets` - list of dictionaries that represent output datasets of workflow. Each dictionary has these values:
    * `events` - number of events in dataset
    * `name` - dataset name
    * `type` - dataset access type - NONE, PRODUCTION, VALID, etc.
  * `status_history` - list of dictionaries that represent workflow status change. Each dictionary has these values:
    * `status` - new status
    * `time` - timestamp
  * `type` - workflow type, only ReReco at the moment

### Tickets

Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `created_requests` - list of prepids of requests that were created from this ticket
* `history` - action history of this object
* `input_datasets` - list of datasets that will be used as inputs. Each input dataset will result in a new request
* `notes` - free form user notes
* `status` - status is either new or done, when ticket is done, it can no longer be edited
* `steps` - list of dictionaries where each step will result in one request in the ReReco pipeline. Request created from second step will have first request as input, third will have second as input, etc. Each step has these attributes:
    * `priority` - priority that will be set to created requests from this step
    * `processing_string` - processing string that will be set to created requests from this step
    * `size_per_event` - size per event that will be set to created requests from this step
    * `subcampaign` - name of subcampaign that is used as template for requests from this step
    * `time_per_event` - time per event that will be set to created requests from this step
* `prepid` - unique identifier in the ReReco machine, same as `_id`

### Sequences

Structure in database:
* `conditions` - what conditions to use, this has to be specified
* `config_id` - id of configuration in ReqMgr2's config cache
* `customise` - inline customization
* `datatier` - list of datatiers to use
* `era` - specify which era to use
* `eventcontent` - list of what event content to write out
* `extra` - freeform text appended to the end of cmsDriver command
* `harvesting_config_id` - id of harvesting configuration (if needed) in ReqMgr2's config cache
* `nThreads` - how many threads should CMSSW use
* `scenario` - scenario overriding standard settings: 'pp', 'cosmics', 'nocoll', 'HeavyIons'
* `step` - list of desired steps
