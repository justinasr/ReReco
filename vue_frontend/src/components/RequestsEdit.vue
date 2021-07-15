<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new request</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing request</span> {{prepid}}</h1>
    <v-card raised class="page-card">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input type="text" v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
        </tr>
        <tr>
          <td>Energy</td>
          <td><input type="number" v-model="editableObject.energy" :disabled="!editingInfo.energy">TeV</td>
        </tr>
        <tr>
          <td>CMSSW Version</td>
          <td><input type="text" v-model="editableObject.cmssw_release" :disabled="!editingInfo.cmssw_release"></td>
        </tr>
        <tr>
          <td>Input</td>
          <td>
            <table v-if="editableObject.input">
              <tr>
                <td>
                  <input type="radio" id="inputTypeDataset" value="dataset" v-model="inputType" v-if="editingInfo.input">
                  Dataset:
                </td>
                <td>
                  <input type="text" v-model="editableObject.input.dataset" :disabled="inputType != 'dataset' || !editingInfo.input">
                </td>
              </tr>
              <tr>
                <td>
                  <input type="radio" id="inputTypeRequest" value="request" v-model="inputType" v-if="editingInfo.input">
                  Request:
                </td>
                <td>
                  <autocompleter
                    v-model="editableObject.input.request"
                    :getSuggestions="getRequestSuggestions"
                    :disabled="inputType != 'request' || !editingInfo.input">
                  </autocompleter>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td>Lumisections</td>
          <td>
            <JSONField v-model="editableObject.lumisections" :disabled="!editingInfo.lumisections"/>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editableObject.memory" :disabled="!editingInfo.memory">MB</td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editableObject.priority" :disabled="!editingInfo.priority"></td>
        </tr>
        <tr>
          <td>Processing String</td>
          <td><input type="text" v-model="editableObject.processing_string" :disabled="!editingInfo.processing_string"></td>
        </tr>
        <tr>
          <td>Runs ({{runListLength(editableObject.runs)}})</td>
          <td><textarea v-model="editableObject.runs" :disabled="!editingInfo.runs"></textarea></td>
        </tr>
        <tr>
          <td>Sequences ({{listLength(editableObject.sequences)}})</td>
          <td>
            <div v-for="(sequence, index) in editableObject.sequences" :key="index">
              <h3>Sequence {{index + 1}}</h3>
              <table>
                <tr>
                  <td>conditions</td><td><input type="text" v-model="sequence.conditions" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>customise</td><td><input type="text" v-model="sequence.customise" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>datatier</td><td><input type="text" v-model="sequence.datatier" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>era</td><td><input type="text" v-model="sequence.era" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>eventcontent</td><td><input type="text" v-model="sequence.eventcontent" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>extra</td><td><input type="text" v-model="sequence.extra" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>nThreads</td><td><input type="number" v-model="sequence.nThreads" :disabled="!editingInfo.sequences"></td>
                </tr>
                <tr>
                  <td>scenario</td>
                  <td>
                    <select v-model="sequence.scenario" :disabled="!editingInfo.sequences">
                      <option>pp</option>
                      <option>cosmics</option>
                      <option>nocoll</option>
                      <option>HeavyIons</option>
                    </select>
                  </td>
                </tr>
                <tr>
                  <td>step</td><td><input type="text" v-model="sequence.step" :disabled="!editingInfo.sequences"></td>
                </tr>
              </table>
              <v-btn small
                     class="mr-1 mb-1"
                     color="error"
                     v-if="editingInfo.sequences"
                     @click="deleteSequence(index)">Delete sequence {{index + 1}}</v-btn>
              <hr>
            </div>
            <v-btn small
                   class="mr-1 mb-1 mt-1"
                   color="primary"
                   v-if="editingInfo.sequences && editableObject.sequences.length < 5"
                   @click="addSequence()">Add sequence {{listLength(editableObject.sequences) + 1}}</v-btn>
          </td>
        </tr>
        <tr>
          <td>Size per event</td>
          <td>
            <div v-for="(sizePerEvent, sizePerEventIndex) in editableObject.size_per_event" :key="sizePerEventIndex" >
              <input type="number"
                     style="margin-top: 2px"
                     v-model="editableObject.size_per_event[sizePerEventIndex]"
                     :disabled="!editingInfo.size_per_event">kB
            </div>
          </td>
        </tr>
        <tr>
          <td>Subcampaign</td>
          <td>
            <autocompleter
              v-model="editableObject.subcampaign"
              :getSuggestions="getSubcampaignSuggestions"
              :disabled="!editingInfo.subcampaign">
            </autocompleter>
          </td>
        </tr>
        <tr>
          <td>Time per event</td>
          <td>
            <div v-for="(timePerEvent, timePerEventIndex) in editableObject.time_per_event" :key="timePerEventIndex" >
              <input type="number"
                     style="margin-top: 2px"
                     v-model="editableObject.time_per_event[timePerEventIndex]"
                     :disabled="!editingInfo.time_per_event">kB
            </div>
          </td>
        </tr>
      </table>
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
      <v-btn v-if="editingInfo.runs && editableObject.subcampaign.length && editableObject.input.dataset" small class="mr-1 mt-1" color="primary" @click="getRuns()">Get runs</v-btn>
      <v-btn v-if="editingInfo.lumisections && editableObject.runs.length && editableObject.subcampaign.length" small class="mr-1 mt-1" color="primary" @click="getLumisections()">Get lumisections</v-btn>
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
import Autocompleter from './Autocompleter.vue'
import JSONField from './JSONField.vue'

export default {
  mixins: [
    utilsMixin
  ],
  components: {
    LoadingOverlay,
    Autocompleter,
    JSONField
  },
  data () {
    return {
      prepid: undefined,
      editableObject: {},
      editingInfo: {},
      loading: true,
      creatingNew: true,
      inputType: 'dataset',
      errorDialog: {
        visible: false,
        title: '',
        description: '',
      }
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    if (query.prepid && query.prepid.length) {
      this.prepid = query.prepid;
    } else {
      this.prepid = '';
    }
    this.creatingNew = this.prepid.length == 0;
    this.loading = true;
    let component = this;
    axios.get('api/requests/get_editable/' + this.prepid).then(response => {
      let objectInfo = response.data.response.object;
      let editingInfo = response.data.response.editing_info;
      if (query.clone && query.clone.length) {
        axios.get('api/requests/get_editable/' + query.clone).then(templateResponse => {
          let templateInfo = templateResponse.data.response.object;
          templateInfo.prepid = objectInfo.prepid;
          templateInfo.history = objectInfo.history;
          templateInfo.status = objectInfo.status;
          templateInfo.workflows = objectInfo.workflows;
          templateInfo.completed_events = objectInfo.completed_events;
          templateInfo.total_events = objectInfo.total_events;
          templateInfo.output_datasets = objectInfo.output_datasets;
          templateInfo.runs = templateInfo.runs.join('\n');
          templateInfo.lumisections = component.stringifyLumis(templateInfo.lumisections);
          component.editableObject = templateInfo;
          component.editingInfo = editingInfo;
          if (component.editableObject.input.request != '') {
            component.inputType = 'request';
          } else {
            component.inputType = 'dataset';
          }
          component.loading = false;
        }).catch(error => {
          component.loading = false;
          component.showError('Error fetching editing information', component.getError(error));
        });
      } else {
        component.editableObject = response.data.response.object;
        component.editingInfo = response.data.response.editing_info;
        objectInfo.runs = objectInfo.runs.join('\n');
        objectInfo.lumisections = component.stringifyLumis(objectInfo.lumisections);
        if (component.editableObject.input.request != '') {
          component.inputType = 'request';
        } else {
          component.inputType = 'dataset';
        }
        component.loading = false;
      }
    }).catch(error => {
      component.loading = false;
      component.showError('Error fetching editing information', component.getError(error));
    });
  },
  methods: {
    save: function() {
      this.loading = true;
      let editableObject = this.makeCopy(this.editableObject);
      let component = this;
      if (this.creatingNew) {
        if (this.inputType == 'dataset') {
          editableObject.input.request = '';
        } else {
          editableObject.input.dataset = '';
        }
      }
      editableObject['notes'] = editableObject['notes'].trim();
      editableObject['runs'] = this.cleanSplit(editableObject['runs']);
      editableObject['lumisections'] = editableObject['lumisections'] ? JSON.parse(editableObject['lumisections']) : {};
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/requests/create', editableObject)
      } else {
        httpRequest = axios.post('api/requests/update', editableObject)
      }
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'requests?prepid=' + response.data.response.prepid;
      }).catch(error => {
        this.showError('Error saving request', component.getError(error));
        component.loading = false;
      });
    },
    addSequence: function() {
      this.loading = true;
      let component = this;
      axios.get('api/subcampaigns/get_default_sequence/' + this.editableObject.subcampaign).then(response => {
        component.editableObject.sequences.push(response.data.response);
        component.editableObject.size_per_event.push(1.0);
        component.editableObject.time_per_event.push(1.0);
        component.loading = false;
      }).catch(error => {
        component.loading = false;
        this.showError('Error getting sequence information', component.getError(error));
      });
    },
    deleteSequence: function(index) {
      this.editableObject.sequences.splice(index, 1);
      this.editableObject.size_per_event.splice(index, 1);
      this.editableObject.time_per_event.splice(index, 1);
    },
    getRuns: function() {
      let component = this;
      this.loading = true;
      axios.post('api/requests/get_runs', {'subcampaign': component.editableObject.subcampaign, 'input_dataset': component.editableObject.input.dataset}).then(response => {
        component.editableObject.runs = response.data.response.filter(Boolean).map(function(s) { return s.toString() }).join('\n');
        this.loading = false;
      }).catch(error => {
        component.loading = false;
        this.showError('Error getting runs for request', component.getError(error))
      });
    },
    getLumisections: function() {
      let component = this;
      this.loading = true;
      let runs = this.cleanSplit(this.editableObject.runs);
      axios.post('api/requests/get_lumisections', {'subcampaign': component.editableObject.subcampaign, 'runs': runs}).then(response => {
        component.editableObject.lumisections = response.data.response ? component.stringifyLumis(response.data.response) : {};
        this.loading = false;
      }).catch(error => {
        component.loading = false;
        this.showError('Error getting lumisections for request', component.getError(error))
      });
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
    getSubcampaignSuggestions: function(_, value, callback) {
      if (!value || value.length == 0) {
        callback([]);
      }
      axios.get('api/suggestions?db_name=subcampaigns&query=' + value).then(response => {
        callback(response.data.response);
      }).catch(() => {
        callback([]);
      });
    },
    getRequestSuggestions: function(_, value, callback) {
      if (!value || value.length == 0) {
        callback([]);
      }
      axios.get('api/suggestions?db_name=requests&query=' + value).then(response => {
        callback(response.data.response);
      }).catch(() => {
        callback([]);
      });
    },
    cancel: function() {
      if (this.creatingNew) {
        window.location = 'requests';
      } else {
        window.location = 'requests?prepid=' + this.prepid;
      }
    },
    runListLength: function(list) {
      return this.cleanSplit(list).length;
    },
  }
}
</script>

<style scoped>

textarea.lumisections {
  font-family: monospace;
  font-size: 0.85em;
}

</style>