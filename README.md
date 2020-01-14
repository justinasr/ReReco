# ReReco Machine
Web based tool for Data ReReco bookkeeping and submission

# Database index

### Campaigns

### campaigns

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
