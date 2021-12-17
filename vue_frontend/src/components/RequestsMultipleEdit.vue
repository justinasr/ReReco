<template>
  <div>
    <h1 class="page-title"><span class="font-weight-light">Editing</span> {{prepids.length}} <span class="font-weight-light">requests</span></h1>
    <v-card raised class="page-card">
      <h2>List of requests</h2>
      <ul>
        <li v-for="prepid in prepids" :key="prepid"><a :href="'requests?prepid=' + prepid" title="Open request in new tab" target="_blank">{{prepid}}</a></li>
      </ul>
      <h2>Values to be updated in {{prepids.length}} requests</h2>
      <table v-if="editingObject">
        <tr>
          <td>Enable harvesting</td>
          <td><input type="checkbox" v-model="editingObject.enable_harvesting"/></td>
        </tr>
        <tr>
          <td>Energy</td>
          <td><input type="number" v-model="editingObject.energy">TeV</td>
        </tr>
        <tr>
          <td>CMSSW Version</td>
          <td><input type="text" v-model="editingObject.cmssw_release"></td>
        </tr>
        <tr>
          <td>Lumisections</td>
          <td>
            <JSONField v-model="editingObject.lumisections"/>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editingObject.memory">MB</td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editingObject.notes"></textarea></td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editingObject.priority"></td>
        </tr>
        <tr>
          <td>Runs ({{cleanSplit(editingObject.runs).length}})</td>
          <td><textarea v-model="editingObject.runs"></textarea></td>
        </tr>
        <tr v-if="editingObject.sequences">
          <td>Sequences ({{listLength(editingObject.sequences)}})</td>
          <td>
            <div v-for="(sequence, index) in editingObject.sequences" :key="index">
              <h3>Sequence {{index + 1}}</h3>
              <table v-if="!sequence.deleted">
                <tr>
                  <td>--conditions</td><td><input type="text" v-model="sequence.conditions"></td>
                </tr>
                <tr>
                  <td>--customise</td><td><input type="text" v-model="sequence.customise"></td>
                </tr>
                <tr>
                  <td>--datatier</td><td><input type="text" v-model="sequence.datatier"></td>
                </tr>
                <tr>
                  <td>--era</td><td><input type="text" v-model="sequence.era"></td>
                </tr>
                <tr>
                  <td>--eventcontent</td><td><input type="text" v-model="sequence.eventcontent"></td>
                </tr>
                <tr>
                  <td>--extra</td><td><input type="text" v-model="sequence.extra"></td>
                </tr>
                <tr>
                  <td>--nThreads</td><td><input type="number" v-model="sequence.nThreads"></td>
                </tr>
                <tr>
                  <td>--scenario</td>
                  <td>
                    <select v-model="sequence.scenario">
                      <option>pp</option>
                      <option>cosmics</option>
                      <option>nocoll</option>
                      <option>HeavyIons</option>
                    </select>
                  </td>
                </tr>
                <tr>
                  <td>--step</td><td><input type="text" v-model="sequence.step"></td>
                </tr>
                <tr>
                  <td>GPU</td>
                  <td>
                    <select v-model="sequence.gpu.requires">
                      <option>forbidden</option>
                      <option>optional</option>
                      <option>required</option>
                    </select>
                  </td>
                </tr>
                <tr v-if="sequence.gpu.requires != 'forbidden'">
                  <td>GPU Parameters</td>
                  <td>
                    <table>
                      <tr>
                        <td>GPU Memory</td>
                        <td><input type="number" v-model="sequence.gpu.gpu_memory" min="0" max="32000" step="1000">MB</td>
                      </tr>
                      <tr>
                        <td>CUDA Capabilities</td>
                        <td><input type="text" v-model="sequence.gpu.cuda_capabilities" placeholder="E.g. 6.0,6.1,6.2"></td>
                      </tr>
                      <tr>
                        <td>CUDA Runtime</td>
                        <td><input type="text" v-model="sequence.gpu.cuda_runtime"></td>
                      </tr>
                      <tr>
                        <td>GPU Name</td>
                        <td><input type="text" v-model="sequence.gpu.gpu_name"></td>
                      </tr>
                      <tr>
                        <td>CUDA Driver Version</td>
                        <td><input type="text" v-model="sequence.gpu.cuda_driver_version"></td>
                      </tr>
                      <tr>
                        <td>CUDA Runtime Version</td>
                        <td><input type="text" v-model="sequence.gpu.cuda_runtime_version"></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <span v-if="sequence.deleted">
                Deleted
              </span>
              <v-btn small
                     class="mr-1 mb-1"
                     color="error"
                     v-if="!sequence.deleted"
                     @click="sequence.deleted = true">Delete sequence {{index + 1}}</v-btn>
              <hr>
            </div>
          </td>
        </tr>
        <tr>
          <td>Size per event</td>
          <td>
            <div v-for="(sizePerEvent, sizePerEventIndex) in editingObject.size_per_event" :key="sizePerEventIndex" >
              <input type="number"
                     style="margin-top: 2px"
                     v-model="editingObject.size_per_event[sizePerEventIndex]">kB
            </div>
          </td>
        </tr>
        <tr>
          <td>Time per event</td>
          <td>
            <div v-for="(timePerEvent, timePerEventIndex) in editingObject.time_per_event" :key="timePerEventIndex" >
              <input type="number"
                     style="margin-top: 2px"
                     v-model="editingObject.time_per_event[timePerEventIndex]">s
            </div>
          </td>
        </tr>
      </table>
      <h2>List of edits that will be done</h2>
      <ul>
        <div v-for="(value, key) in differences" :key="key">
          <template v-if="!['sequences', 'size_per_event', 'time_per_event'].includes(key)">
            <li>
              <b>{{key}}</b> will be set to <b>{{value}}</b> 
              <v-btn small
                     class="ml-1 mb-1"
                     color="error"
                     @click="editingObject[key] = originalEditingObject[key]">Remove edit</v-btn>
            </li>
          </template>
          <template v-if="key == 'sequences'">
            <div v-for="(sequence, index) in value" :key="index">
              <template v-if="!sequence.deleted">
                <div v-for="(sequenceValue, sequenceKey) in sequence" :key="sequenceKey">
                  <template v-if="['gpu'].includes(sequenceKey)">
                    <li v-for="(driverValue, driverKey) in sequenceValue" :key="driverKey">
                      <b>{{driverKey}}</b> in <b>Sequence {{index + 1}}</b> will be set to <b>{{driverValue}}</b>
                      <v-btn small
                             class="ml-1 mb-1"
                             color="error"
                             @click="editingObject.sequences[index][sequenceKey][driverKey] = originalEditingObject.sequences[index][sequenceKey][driverKey]">Remove edit</v-btn>
                    </li>
                  </template>
                  <template v-if="!['deleted', 'gpu'].includes(sequenceKey)">
                    <li>
                      <b>{{sequenceKey}}</b> in <b>Sequence {{index + 1}}</b> will be set to <b>{{sequenceValue}}</b>
                      <v-btn small
                             class="ml-1 mb-1"
                             color="error"
                             @click="editingObject.sequences[index][sequenceKey] = originalEditingObject.sequences[index][sequenceKey]">Remove edit</v-btn>
                    </li>
                  </template>
                </div>
              </template>
              <li v-if="sequence.deleted">
                Sequence {{index + 1}} will be <b>deleted in all {{prepids.length}}</b> requests
                <v-btn small class="ml-1 mb-1" color="error" @click="editingObject.sequences[index].deleted = false">Remove edit</v-btn>
              </li>
            </div>
          </template>
          <template v-if="['size_per_event', 'time_per_event'].includes(key)">
            <div v-for="(listItem, index) in value" :key="index">
              <template v-if="listItem != null">
                <li>
                  <b>{{key}}</b> value at <b>position {{index + 1}}</b> will be set to <b>{{listItem}}</b>
                  <v-btn small
                         class="ml-1 mb-1"
                         color="error"
                         @click="$set(editingObject[key], index, originalEditingObject[key][index])">Remove edit</v-btn>
                </li>
              </template>
            </div>
          </template>
        </div>
      </ul>
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
      <v-btn small class="mr-1 mt-1" color="error" @click="cancel()">Cancel</v-btn>
    </v-card>
    <LoadingOverlay :visible="loading"/>
    <v-dialog v-model="errorDialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">
          {{errorDialog.title}}
        </v-card-title>
        <v-card-text>
          <span v-html="errorDialog.description"></span>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" @click="clearErrorDialog()">
            Dismiss
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'
import LoadingOverlay from './LoadingOverlay.vue'
import JSONField from './JSONField.vue'

export default {
  components: {
    LoadingOverlay,
    JSONField
  },
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      prepids: [],
      objects: [],
      editingObject: {},
      originalEditingObject: {},
      differences: {},
      loading: true,
      errorDialog: {
        visible: false,
        title: '',
        description: '',
      }
    }
  },
  created () {
    this.loading = true;
    let query = Object.assign({}, this.$route.query);
    this.prepids = this.cleanSplit(query['prepid']);
    let component = this;
    axios.get('api/requests/get_editable/' + this.prepids.join(',')).then(response => {
      let objects = response.data.response.object;
      if (component.prepids.length == 1) {
        objects = [objects];
      }
      for (let obj of objects) {
        this.prepareObjectForEditing(obj);
      }
      component.objects = objects;
      let editingObject = component.makeEditingObject(objects);
      component.$set(component, 'editingObject', component.makeCopy(editingObject));
      component.$set(component, 'originalEditingObject', component.makeCopy(editingObject))
      component.loading = false;
    }).catch(error => {
      component.loading = false;
      component.showError('Error getting request information', component.getError(error));
    });
  },
  watch: {
    editingObject: {
      deep: true,
      handler() {
        let differences = {};
        let ref = this.originalEditingObject;
        let tar = this.editingObject;
        for (let key of Object.keys(ref)) {
          if (['sequences', 'time_per_event', 'size_per_event'].includes(key)) {
            continue
          }
          if (ref[key] != tar[key]) {
            differences[key] = tar[key]
          }
        }
        // Sequence diffs
        let sequencesDiffs = [];
        for (let i = 0; i < ref.sequences.length; i++) {
          let refSeq = ref.sequences[i];
          let tarSeq = tar.sequences[i];
          let seqDiff = {'deleted': tarSeq.deleted, 'gpu': {}};
          sequencesDiffs.push(seqDiff);
          for (let key of Object.keys(refSeq)) {
            if (['gpu'].includes(key)) {
              for (let driverKey of Object.keys(refSeq[key])) {
                if (refSeq[key][driverKey] != tarSeq[key][driverKey]) {
                  seqDiff[key][driverKey] = tarSeq[key][driverKey];
                }
              }
            } else if (refSeq[key] != tarSeq[key]) {
              if (key == 'nThreads') {
                seqDiff[key] = parseInt(tarSeq[key]);
              } else {
                seqDiff[key] = tarSeq[key];
              }
            }
          }
        }
        if (sequencesDiffs.some(s => s.deleted || Object.keys(s).length > 1)) {
          differences['sequences'] = sequencesDiffs;
        }
        // Size per event and time per event diffs
        let sizePerEventDiffs = Array(ref.sequences.length);
        let timePerEventDiffs = Array(ref.sequences.length);
        for (let i = 0; i < ref.sequences.length; i++) {
          sizePerEventDiffs[i] = ref.size_per_event[i] != tar.size_per_event[i] ? parseFloat(tar.size_per_event[i]) : null;
          timePerEventDiffs[i] = ref.time_per_event[i] != tar.time_per_event[i] ? parseFloat(tar.time_per_event[i]) : null;
        }
        if (sizePerEventDiffs.some(s => s !== null)) {
          differences['size_per_event'] = sizePerEventDiffs;
        }
        if (timePerEventDiffs.some(s => s !== null)) {
          differences['time_per_event'] = timePerEventDiffs;
        }
        this.$set(this, 'differences', differences);
      }
    }
  },
  methods: {
    prepareObjectForEditing: function(obj) {
      obj.runs = obj.runs.join('\n');
      obj.lumisections = this.stringifyLumis(obj.lumisections);
      for (let sequence of obj.sequences) {
        sequence.datatier = sequence.datatier.join(',');
        sequence.eventcontent = sequence.eventcontent.join(',');
        sequence.step = sequence.step.join(',');
        sequence.gpu.cuda_capabilities = sequence.gpu.cuda_capabilities.join(',');
      }
    },
    prepareObjectForSaving: function(obj) {
      obj.notes = obj.notes.trim();
      obj.runs = this.cleanSplit(obj.runs);
      obj.lumisections = obj.lumisections ? JSON.parse(obj.lumisections) : {};
      for (let sequence of obj.sequences) {
        sequence.datatier = this.cleanSplit(sequence.datatier);
        sequence.eventcontent = this.cleanSplit(sequence.eventcontent);
        sequence.step = this.cleanSplit(sequence.step);
        sequence.gpu.cuda_capabilities = this.cleanSplit(sequence.gpu.cuda_capabilities);
      }
    },
    jsonDiff: function(obj1, obj2) {
      return JSON.stringify(obj1) != JSON.stringify(obj2);
    },
    getCommonValue: function(objects, callback) {
      for (let i = 0; i < objects.length - 1; i++) {
        if (this.jsonDiff(callback(objects[i]), callback(objects[i + 1]))) {
          return null;
        }
      }
      return callback(objects[0]);
    },
    makeEditingObject: function(requests) {
      let editingObject = {};
      // Primitive attributes
      for (let key of ['enable_harvesting', 'energy', 'cmssw_release', 'lumisections', 'memory', 'notes', 'priority', 'runs']) {
        editingObject[key] = this.getCommonValue(requests, (r) => r[key]);
      }
      // Sequences
      editingObject.sequences = Array(Math.min(...requests.map(x => x.sequences.length)));
      for (let i = 0; i < editingObject.sequences.length; i++) {
        editingObject.sequences[i] = {'deleted': false, 'gpu': {}};
      }
      // Sequence attributes
      for (let key of Object.keys(requests[0].sequences[0])) {
        if (['gpu'].includes(key)) {
          for (let i = 0; i < editingObject.sequences.length; i++) {
            for (let driverKey of Object.keys(requests[0].sequences[i][key])) {
              editingObject.sequences[i][key][driverKey] = this.getCommonValue(requests, (r) => r.sequences[i][key][driverKey]);
            }
          }
        } else {
          for (let i = 0; i < editingObject.sequences.length; i++) {
            editingObject.sequences[i][key] = this.getCommonValue(requests, (r) => r.sequences[i][key]);
          }
        }
      }
      // Time per event and size per event
      editingObject.size_per_event = Array(editingObject.sequences.length);
      editingObject.time_per_event = Array(editingObject.sequences.length);
      for (let i = 0; i < editingObject.sequences.length; i++) {
        editingObject.size_per_event[i] = this.getCommonValue(requests, (r) => r.size_per_event[i]);
        editingObject.time_per_event[i] = this.getCommonValue(requests, (r) => r.time_per_event[i]);
      }
      return editingObject;
    },
    save: function() {
      let objects = this.makeCopy(this.objects);
      let component = this;
      for (let obj of objects) {
        for (let key of Object.keys(this.differences)) {
          let difference = this.differences[key];
          if (key == 'sequences') {
            for (let seqIndex = 0; seqIndex < difference.length; seqIndex++) {
              let diffSeq = difference[seqIndex];
              if (diffSeq.deleted) {
                obj.sequences[seqIndex] = undefined;
              } else {
                let objSeq = obj.sequences[seqIndex];
                for (let seqKey of Object.keys(diffSeq)) {
                  if (['gpu'].includes(seqKey)) {
                    for (let driverKey of Object.keys(diffSeq[seqKey])) {
                      objSeq[seqKey][driverKey] = diffSeq[seqKey][driverKey];
                    }
                  } else if (seqKey != 'deleted') {
                    objSeq[seqKey] = diffSeq[seqKey];
                  }
                }
              }
            }
            obj.sequences = obj.sequences.filter(s => s !== undefined);
          } else if (['size_per_event', 'time_per_event'].includes(key)) {
            for (let i = 0; i < difference.length; i++) {
              if (difference[i] != null) {
                obj[key][i] = difference[i];
              }
            }
          } else {
            obj[key] = difference;
          }
        }
        this.prepareObjectForSaving(obj);
      }
      this.loading = true;
      let httpRequest = axios.post('api/requests/update', objects)
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'requests?prepid=' + response.data.response.map(x => x.prepid).join(',');
      }).catch(error => {
        component.loading = false;
        component.showError('Error saving request', component.getError(error))
      });
    },
    cancel: function() {
      window.location = 'requests?prepid=' + this.prepids.join(',');
    },
    clearErrorDialog: function() {
      this.errorDialog.visible = false;
      this.errorDialog.title = '';
      this.errorDialog.description = '';
    },
    showError: function(title, description) {
      this.clearErrorDialog();
      this.errorDialog.title = title;
      this.errorDialog.description = description;
      this.errorDialog.visible = true;
    }
  }
}
</script>

<style scoped>
h2 {
  text-align: center;
}
</style>
