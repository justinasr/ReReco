# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

# ReReco objects

### Campaigns

Structure in database:
* `_id` - unique document identifier in database (required by CouchDB)
* `_rev` - document revision (required by CouchDB)
* `cmssw_release` - CMSSW release
* `energy` - energy in TeV. Unused, but nice to have
* `history` - action history of this object
* `memory` - memory in magabytes
* `notes` - user notes
* `prepid` - unique identifier in the system
* `sequences` - list of dictionaries that hold attributes for cmsDriver commands (see Sequences)
* `step` - DR, MiniAOD or NanoAOD. Indicates which step of chained request is this

### Requests

Structure in database:
* `_id` - unique document identifier in database (required by CouchDB)
* `_rev` - document revision (required by CouchDB)
* `cmssw_release` - CMSSW release
* `energy` - energy in TeV. Unused, but nice to have
* `history` - action history of this object
* `input_dataset` - dataset name that is used as an input
* `member_of_campaign` - name of campaign (see Campaigns) that was used as a template for this request
* `memory` - memory in magabytes
* `notes` - user notes
* `output_datasets` - list of dataset names that are produced and saved by this request. This information is received after request is submitted to computing
* `prepid` - unique identifier in the system
* `priority` - priority of the job in computing
* `processing_string` - TO BE FILLED
* `runs` - TO BE FILLED
* `sequences` - list of dictionaries that hold attributes for cmsDriver commands (see Sequences)
* `size_per_event` - required disk space for one event in kilobytes
* `status` - status of this request. Can be new, approved, submitted or done
* `step` - DR, MiniAOD or NanoAOD. Indicates which step of chained request is this
* `time_per_event` - required time for one event in seconds
* `workflows` - TO BE FILLED

### Campaign tickets

Structure in database:
* `_id` - unique document identifier in database (required by CouchDB)
* `_rev` - document revision (required by CouchDB)
* `campaign` - name of campaign that is used as template for requests
* `created_requests` - list of prepids of requests that were created from this ticket
* `history` - action history of this object
* `input_datasets` - list of datasets that will be used as inputs. Each input dataset will result in a new request
* `notes` - user notes
* `prepid` - unique identifier in the system
* `processing_string` - TO BE FILLED
* `status` - status is either new or done

### Sequences

Structure in database:

* `conditions` - what conditions to use, this has to be specified
* `datatier` - list of datatiers to use
* `customise` - inline customization
* `era` - specify which era to use
* `eventcontent` - list of what event content to write out
* `extra` - TO BE FILLED
* `nThreads` - how many threads should CMSSW use
* `step` - list of desired steps

# Database index

## CouchDB Views

### Campaigns

##### campaigns

all:
```
function(doc) {
  if (doc._id.indexOf('_') === 0) {
    return null;
  }
  if (doc.prepid) {
    emit(doc.prepid, doc._id);
  }
}
```

### Requests

##### requests

all:
```
function(doc) {
  if (doc._id.indexOf('_') === 0) {
    return null;
  }
  if (doc.prepid) {
    emit(doc.prepid, doc._id);
  }
}
```

##### serial_number

map:
```
function(doc) {
  if (doc.member_of_campaign) {
    var parts = doc._id.split('-');
    var number = parseInt(parts[parts.length - 1], 10);
    emit(doc.member_of_campaign, number);
  };
}
```
reduce:
```
function(keys, values, rereduce) {
  return Math.max.apply({}, values);
}
```

## couchdb-lucence Views

### Campaigns

```
function(doc) {
  if (doc._id.indexOf('_') === 0) {
    return null;
  }
  var res = new Document();
  res.add(doc._id, {field:'_id', store:'yes', type:'string'});
  res.add(doc.prepid, {field:'prepid', store:'yes', type:'string'});
  res.add(doc.step, {field:'step', store:'yes', type:'string'});
  res.add(doc.cmssw_release, {field:'cmssw_release', store:'yes', type:'string'});
  res.add(doc.memory, {field:'memory', store:'yes', type:'int'});
  res.add(doc.energy, {field:'energy', store:'yes', type:'float'});
  log.info(doc.prepid);
  return res;
}
```

### Campaign tickets

```
function(doc) {
  log.info('Starting ' + doc._id);
  if (doc._id.indexOf('_') === 0) {
    return null;
  }
  var res = new Document();
  res.add(doc._id, {field:'_id', store:'yes', type:'string'});
  res.add(doc.prepid, {field:'prepid', store:'yes', type:'string'});
  res.add(doc.status, {field:'status', store:'yes', type:'string'});
  res.add(doc.campaign, {field:'campaign', store:'yes', type:'string'});
  res.add(doc.processing_string, {field:'processing_string', store:'yes', type:'string'});
  for (var i = 0; i < doc.input_datasets.length; i++) {
    res.add(doc.input_datasets[i], {field:'input_datasets', store:'yes'});
  }
  for (var i = 0; i < doc.created_requests.length; i++) {
    res.add(doc.created_requests[i], {field:'created_requests', store:'yes'});
  }
  log.info('Done ' + doc.prepid);
  return res;
}
```

### Requests

```
function(doc) {
  log.info('Starting ' + doc._id);
  if (doc._id.indexOf('_') === 0) {
    return null;
  }
  var res = new Document();
  res.add(doc._id, {field:'_id', store:'yes', type:'string'});
  res.add(doc.prepid, {field:'prepid', store:'yes', type:'string'});
  res.add(doc.step, {field:'step', store:'yes', type:'string'});
  res.add(doc.input_dataset, {field:'input_dataset', store:'yes', type:'string'});
  res.add(doc.member_of_campaign, {field:'member_of_campaign', store:'yes', type:'string'});
  res.add(doc.status, {field:'status', store:'yes', type:'string'});
  res.add(doc.cmssw_release, {field:'cmssw_release', store:'yes', type:'string'});
  res.add(doc.memory, {field:'memory', store:'yes', type:'int'});
  res.add(doc.priority, {field:'priority', store:'yes', type:'int'});
  res.add(doc.energy, {field:'energy', store:'yes', type:'float'});
  res.add(doc.processing_string, {field:'processing_string', store:'yes', type:'string'});
  for (var i = 0; i < doc.output_datasets.length; i++) {
    res.add(doc.output_datasets[i], {field:'output_datasets', store:'yes'});
  }
  log.info('Done ' + doc.prepid);
  return res;
}
```