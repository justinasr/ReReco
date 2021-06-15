<template>
  <div>
    <h1 class="page-title"><span class="font-weight-light">Editing</span> {{prepids.length}} <span class="font-weight-light">requests</span></h1>
    <v-card raised class="page-card">
      <h2>List of requests</h2>
      <ul>
        <li v-for="prepid in prepids" :key="prepid"><a :href="'requests?prepid=' + prepid" title="Open request in new tab" target="_blank">{{prepid}}</a></li>
      </ul>
      <h2>Values to be updated in {{prepids.length}} requests</h2>
      <table v-if="editableRequest">
        <tr>
          <td>Energy</td>
          <td><input type="number" v-model="editableRequest.energy">TeV</td>
        </tr>
        <tr>
          <td>CMSSW Version</td>
          <td><input type="text" v-model="editableRequest.cmssw_release"></td>
        </tr>
        <tr>
          <td>Lumisections</td>
          <td>
            <JSONField v-model="editableRequest.lumisections"/>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editableRequest.memory">MB</td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableRequest.notes"></textarea></td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editableRequest.priority"></td>
        </tr>
        <tr>
          <td>Runs ({{runListLength(editableRequest.runs)}})</td>
          <td><textarea v-model="editableRequest.runs"></textarea></td>
        </tr>
        <tr>
          <td>Sequences ({{listLength(editableRequest.sequences)}})</td>
          <td>
            <div v-for="(sequence, index) in editableRequest.sequences" :key="index">
              <h3>Sequence {{index + 1}}</h3>
              <table v-if="!sequence.deleted">
                <tr>
                  <td>conditions</td><td><input type="text" v-model="sequence.conditions"></td>
                </tr>
                <tr>
                  <td>customise</td><td><input type="text" v-model="sequence.customise"></td>
                </tr>
                <tr>
                  <td>datatier</td><td><input type="text" v-model="sequence.datatier"></td>
                </tr>
                <tr>
                  <td>era</td><td><input type="text" v-model="sequence.era"></td>
                </tr>
                <tr>
                  <td>eventcontent</td><td><input type="text" v-model="sequence.eventcontent"></td>
                </tr>
                <tr>
                  <td>extra</td><td><input type="text" v-model="sequence.extra"></td>
                </tr>
                <tr>
                  <td>nThreads</td><td><input type="number" v-model="sequence.nThreads"></td>
                </tr>
                <tr>
                  <td>scenario</td>
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
                  <td>step</td><td><input type="text" v-model="sequence.step"></td>
                </tr>
              </table>
              <span v-if="sequence.deleted">
                Deleted
              </span>
              <v-btn small
                     class="mr-1 mb-1"
                     color="error"
                     v-if="!sequence.deleted"
                     @click="deleteSequence(index)">Delete sequence {{index + 1}}</v-btn>
              <hr>
            </div>
          </td>
        </tr>
        <tr>
          <td>Size per event</td>
          <td><input type="number" v-model="editableRequest.size_per_event">kB</td>
        </tr>
        <tr>
          <td>Time per event</td>
          <td><input type="number" v-model="editableRequest.time_per_event">s</td>
        </tr>
      </table>
      <h2>List of edits that will be done</h2>
      <ul>
        <div v-for="(value, key) in editableRequest" :key="key">
          <template v-if="key != 'sequences' && value != orgEditableRequest[key]">
            <li>
              <b>{{key}}</b> will be set to <b>{{value}}</b> 
              <v-btn small class="ml-1 mb-1" style="height: 22px" color="error" @click="deleteAttribute(editableRequest, key)">Remove</v-btn>
            </li>
          </template>
        </div>
        <div v-for="(sequence, index) in editableRequest.sequences" :key="index">
          <template v-if="!sequence.deleted">
            <div v-for="(value, key) in sequence" :key="key">
              <template v-if="key != 'deleted' && value != orgEditableRequest.sequences[index][key]">
                <li>
                  <b>{{key}}</b> in <b>Sequence {{index + 1}}</b> will be set to <b>{{value}}</b>
                  <v-btn small class="ml-1 mb-1" style="height: 22px" color="error" @click="deleteAttribute(sequence, key)">Remove</v-btn>
                </li>
              </template>
            </div>
          </template>
          <li v-if="sequence.deleted">
            Sequence {{index + 1}} will be <b>deleted in all {{prepids.length}}</b> requests
            <v-btn small class="ml-1 mb-1" style="height: 22px" color="error" @click="undeleteSequence(index)">Bring back sequence {{index + 1}}</v-btn>
          </li>
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
      requests: [],
      editableRequest: {},
      orgEditableRequest: {},
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
      let requests = response.data.response.object;
      if (component.prepids.length == 1) {
        requests = [requests];
      }
      for (let request of requests) {
        request.runs = request.runs.join('\n');
        request.lumisections = component.stringifyLumis(request.lumisections);
        for (let sequence of request.sequences) {
          sequence.datatier = sequence.datatier.join(',');
          sequence.eventcontent = sequence.eventcontent.join(',');
          sequence.step = sequence.step.join(',');
        }
      }
      component.requests = requests;
      let placeholders = component.makePlaceholders(requests);
      component.$set(component, 'editableRequest', placeholders);
      component.$set(component, 'orgEditableRequest', component.makeCopy(placeholders))
      component.loading = false;
    }).catch(error => {
      component.loading = false;
      component.showError('Error getting request information', component.getError(error));
    });
  },
  methods: {
    makePlaceholders: function(requests) {
      let placeholders = {};
      for (let key of ['energy', 'cmssw_release', 'lumisections', 'memory', 'notes',
                       'priority', 'runs', 'time_per_event', 'size_per_event']) {
        let sameValue = true;
        for (let i = 0; i < requests.length - 1; i++) {
          if (JSON.stringify(requests[i][key]) != JSON.stringify(requests[i + 1][key])) {
            sameValue = false;
            break
          }
        }
        placeholders[key] = sameValue ? this.makeCopy(requests[0][key]) : '';
      }
      let minSequences = Math.min(...requests.map(x => x.sequences.length));
      placeholders.sequences = [];
      for (let i = 0; i < minSequences; i++) {
        placeholders.sequences.push({'deleted': false});
      }
      for (let key of ['conditions', 'customise', 'datatier', 'era', 'eventcontent',
                       'extra', 'nThreads', 'scenario', 'step']) {
        for (let sequenceIndex = 0; sequenceIndex < minSequences; sequenceIndex++) {
          let sameValue = true;
          for (let i = 0; i < requests.length - 1; i++) {
            if (JSON.stringify(requests[i].sequences[sequenceIndex][key]) != JSON.stringify(requests[i + 1].sequences[sequenceIndex][key])) {
              sameValue = false;
              break
            }
          }
          placeholders.sequences[sequenceIndex][key] = sameValue ? this.makeCopy(requests[0].sequences[sequenceIndex][key]) : '';
        }
      } 
      return placeholders;
    },
    save: function() {
      let requests = this.makeCopy(this.requests);
      let component = this;
      // First - update request attributes
      for (let key in this.editableRequest) {
        if (key == 'sequences') {
          continue;
        }
        const value = this.editableRequest[key];
        if (value != this.orgEditableRequest[key]) {
          for (let request of requests) {
            request[key] = value;
          }
        }
      }
      // Then - update request sequences attributes
      for (let sequenceIndex in this.editableRequest.sequences) {
        const sequence = this.editableRequest.sequences[sequenceIndex];
        for (let request of requests) {
          const requestSequences = request.sequences;
          if (sequenceIndex >= requestSequences.length) {
            continue;
          }
          let requestSequence = requestSequences[sequenceIndex];
          if (sequence.deleted) {
            // Removal from list will happen later
            requestSequences[sequenceIndex] = undefined;
            continue
          }
          // Sequence attributes
          for (let key in sequence) {
            if (key == 'deleted') {
              continue
            }
            requestSequence[key] = sequence[key];
          }
        }
      }
      for (let request of requests) {
        request.sequences = request.sequences.filter(s => s !== undefined);
        request.notes = request.notes.trim();
        request.runs = this.cleanSplit(request.runs);
        request.lumisections = request.lumisections ? JSON.parse(request.lumisections) : {};
        for (let sequence of request.sequences) {
          sequence.datatier = this.cleanSplit(sequence.datatier);
          sequence.eventcontent = this.cleanSplit(sequence.eventcontent);
          sequence.step = this.cleanSplit(sequence.step);
        }
      }
      this.loading = true;
      let httpRequest = axios.post('api/requests/update', requests)
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
    },
    setValue: function(obj, key, value) {
      this.$set(obj, key, value);
    },
    deleteAttribute: function(obj, name) {
      obj[name] = undefined;
      delete obj[name];
    },
    deleteSequence: function(sequenceIndex) {
      this.editableRequest.sequences[sequenceIndex].deleted = true;
    },
    undeleteSequence: function(sequenceIndex) {
      this.editableRequest.sequences[sequenceIndex].deleted = false;
    },
    runListLength: function(list) {
      return this.cleanSplit(list).length;
    },
  }
}
</script>

<style scoped>
h2 {
  text-align: center;
}
</style>