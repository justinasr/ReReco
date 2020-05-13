# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

# ReReco objects

### Subcampaigns

Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release
* `energy` - energy in TeV. Unused, but nice to have
* `history` - action history of this object
* `memory` - memory in megabytes
* `notes` - user notes
* `prepid` - unique identifier in the system
* `runs_json_path` - path to json that contains all runs
* `scram_arch` - scram architecture of CMSSW release
* `sequences` - list of dictionaries that hold attributes for cmsDriver commands (see Sequences)
* `step` - DR, MiniAOD or NanoAOD. Indicates which step of chained request is this

### Requests

Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release
* `completed_events` - completed (produced) events
* `energy` - energy in TeV. Unused, but nice to have
* `history` - action history of this object
* `input_dataset` - dataset name that is used as an input
* `memory` - memory in megabytes
* `notes` - user notes
* `output_datasets` - list of dataset names that are produced and saved by this request. This information is received after request is submitted to computing
* `prepid` - unique identifier in the system
* `priority` - priority of the job in computing
* `processing_string` - processing string
* `runs` - list of runs to be processed
* `sequences` - list of dictionaries that hold attributes for cmsDriver commands (see Sequences)
* `size_per_event` - required disk space for one event in kilobytes
* `status` - status of this request. Can be new, approved, submitted or done
* `step` - DR, MiniAOD or NanoAOD. Indicates which step of chained request is this
* `subcampaign` - name of subcampaign (see Subcampaigns) that was used as a template for this request
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

### Subcampaign tickets

Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `created_requests` - list of prepids of requests that were created from this ticket
* `history` - action history of this object
* `input_datasets` - list of datasets that will be used as inputs. Each input dataset will result in a new request
* `notes` - user notes
* `priority`
* `prepid` - unique identifier in the system
* `processing_string` - processing string that will be added to created requests
* `size_per_event` - size per event that will be set to created requests
* `status` - status is either new or done
* `subcampaign` - name of subcampaign that is used as template for requests
* `time_per_event` - time per event that will be set to created requests

### Sequences

Structure in database:
* `conditions` - what conditions to use, this has to be specified
* `config_id` - id of configuration in ReqMgr2's config cache
* `customise` - inline customization
* `datatier` - list of datatiers to use
* `era` - specify which era to use
* `eventcontent` - list of what event content to write out
* `extra` - freeform text appended to the end of cmsDriver.py command
* `harvesting_config_id` - id of harvesting configuration (if needed) in ReqMgr2's config cache
* `nThreads` - how many threads should CMSSW use
* `scenario` - scenario overriding standard settings: 'pp', 'cosmics', 'nocoll', 'HeavyIons'
* `step` - list of desired steps
