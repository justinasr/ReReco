# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

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
  res.add(doc.type, {field:'type', store:'yes', type:'string'});
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