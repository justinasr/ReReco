# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

## Introduction

ReReco machine is a web-based tool for creating, submitting and bookkeeping reprocessing workflows - ReReco requests.
Only PdmV conveners have rights to perform actions in the ReReco machine.

## ReReco objects

There are four types of objects in ReReco machine: Subcampaigns, Requests, Sequences and Tickets. Sequence is always a part of a request and cannot exist independently.

### Subcampaigns

##### Definition
Campaigns in computing can be very big and have many fundamentally different requests in them. While designing ReReco machine, it was decided to introduce a smaller unit - Subcampaign. If ReReco machine used campaigns, a campaign would have to be changed for each batch of requests, for example: campaign UltraLegacy2017 is used for Cosmics and ZeroBiasScouting. Both cases have very different sequences, so it would be impractical to change sequence in campaign after generating Cosmics requests and before generating ZeroBiasScouting requests. Each Subcampaign represent a different variation of same computing campaign. In this example, there would be two UltraLegacy2017 Subcampaigns - one for Cosmics and one for ZeroBiasScouting and ReReco machine can preserve different sequences that were used in one campaign. That is why it is called a Subcampaign - it is like one of many variations of a campaign.
Subcampaign name is made of two parts that are joined with a dash ("-"). First part is campaign name in computing. Second part is arbitrary string that gives more insight on sequence(s) that this Subcampaign contains, i.e.: "NameOfCampaignInComputing-ArbitraryStringForIdentification". Full Subcampaign name is not submitted to computing. When requests are submitted for production, only the campaign name part is used and subcampaign-specific part is removed, so introduction of this new object does not affect computing.

##### Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release for the subcampaign
* `energy` - energy in TeV
* `history` - action history of this object
* `memory` - memory in megabytes
* `notes` - free form user notes
* `prepid` - unique identifier in the ReReco machine, same as `_id`
* `runs_json_path` - relative path to JSON file that contains all runs, this value will be internally prepended with https://cms-service-dqmdc.web.cern.ch/CAF/certification/
* `scram_arch` - scram architecture of CMSSW release, will be automatically fetched from https://cmssdt.cern.ch/SDT/cgi-bin/ReleasesXML?anytype=1
* `sequences` - list of Sequence objects (or dictionaries) that hold attributes for cmsDriver commands

### Requests

##### Definition
Requests are the main units of ReReco machine. Each Request represent one step in production pipeline. In ReReco case it is usually a RECO or NanoAOD step. Request can have multiple sequences - cmsDrivers inside. Request can have a dataset or another Request as input. In latter case, last output dataset of input request will be used as input dataset. Request statuses are new, approved, submitting, submitted and done. When Request becomes done, Requests that use it as input will automatically be submitted.
Each Request corresponds to one submitted workflow in ReqMgr2. If Request or it's workflow was resubmitted, Request will have multiple workflows.

##### Structure in database:
* `_id` - unique document identifier in database (required by DB)
* `cmssw_release` - CMSSW release
* `completed_events` - completed (produced) events
* `energy` - energy in TeV
* `history` - action history of this object
* `input` - dictionary with two values:
    * `dataset` - dataset name that will be used as input
    * `request` - prepid of request that will be used as input when it is done. Last output dataset name of that request will be automatically copied to `dataset` field once it is known
* `lumisections` - dictionary of runs and lumisections to process. Keys are runs and values are list of lumisection ranges
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

##### Definition
Tickets are a way to create multiple Requests with identical settings, but different input datasets. If multiple steps are specified in a Ticket, then each input dataset will create as many Requests as there are steps and these Requests will be linked together, so output of first is the input of second, output of second is input of third, etc. Each input dataset will be used to create one Request where input will be that input dataset. For example, if there are two steps - RECO and Nano campaigns and three input datasets /a/b/RAW, /c/d/RAW and /e/f/RAW, then six Requests in total will be created. First Request will have /a/b/RAW as input dataset. Second Request will use first Request as input. Third request will have /c/d/RAW as input. Fourth Request will use third Request as input. Same for fifth and sixth Requests.
List of input datasets can be filled manually or fetched from DBS using a query. Query supports wildcards. ReReco machine has a list of Primary Datasets that will be omitted from fetched input datasets. Also, only VALID and PRODUCTION datasets are fetched.

##### Structure in database:
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

##### Definition
Sequence is one cmsDriver command. It has some predefined arguments that can be modified by a user. It also has IDs of uploaded configuration files. If Sequence steps include DQM, an additional cmsDriver for harvesting will be automatically added after cmsDriver of this Sequence.

##### Structure in database:
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
