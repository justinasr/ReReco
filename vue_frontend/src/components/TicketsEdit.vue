<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new ticket</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing ticket</span> {{prepid}}</h1>
    <v-card raised class="page-card">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input type="text" v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
        </tr>
        <tr>
          <td>Steps ({{listLength(editableObject.steps)}})</td>
          <td>
            <div v-for="(step, index) in editableObject.steps" :key="index">
              <h3>Step {{index + 1}}</h3>
              <table>
                <tr>
                  <td>Subcampaign</td>
                  <td>
                    <autocompleter
                      v-model="step.subcampaign"
                      :getSuggestions="getSubcampaignSuggestions"
                      :disabled="!editingInfo.steps[index].subcampaign">
                    </autocompleter>
                  </td>
                </tr>
                <tr>
                  <td>Processing String</td>
                  <td><input type="text"
                             v-model="step.processing_string"
                             :disabled="!editingInfo.steps[index].processing_string"></td>
                </tr>
                <tr>
                  <td>Size per event</td>
                  <td><input type="number"
                             v-model="step.size_per_event"
                             :disabled="!editingInfo.steps[index].size_per_event">kB</td>
                </tr>
                <tr>
                  <td>Time per event</td>
                  <td><input type="number"
                             v-model="step.time_per_event"
                             :disabled="!editingInfo.steps[index].time_per_event">s</td>
                </tr>
                <tr>
                  <td>Priority</td>
                  <td><input type="number"
                             v-model="step.priority"
                             :disabled="!editingInfo.steps[index].priority"></td>
                </tr>
              </table>
              <v-btn small
                     class="mr-1 mb-1"
                     color="error"
                     v-if="(creatingNew || index != 0) && editingInfo.__steps"
                     @click="deleteStep(index)">Delete step {{index + 1}}</v-btn>
              <hr>
            </div>
            <v-btn small
                   class="mr-1 mb-1 mt-1"
                   color="primary"
                   v-if="editingInfo.__steps && editableObject.steps.length < 5"
                   @click="addStep()">Add step {{listLength(editableObject.steps) + 1}}</v-btn>
          </td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Input Datasets ({{listLength(editableObject.input_datasets)}})</td>
          <td><textarea v-model="editableObject.input_datasets" :disabled="!editingInfo.input_datasets"></textarea></td>
        </tr>
      </table>
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()" :disabled="!listLength(editableObject.steps) || !listLength(editableObject.input_datasets)">Save</v-btn>
      <v-btn v-if="editingInfo.input_datasets" small class="mr-1 mt-1" color="primary" @click="showGetDatasetsDialog()">Get dataset list from DBS</v-btn>
      <v-btn small class="mr-1 mt-1" color="error" @click="cancel()">Cancel</v-btn>
    </v-card>
    <v-dialog v-model="getDatasetsDialog.visible"
              max-width="50%">
      <v-card class="page-card mb-0" style="max-width: none !important;">
        <v-card-title class="headline">Fetch dataset list</v-card-title>
        <v-card-text>
          Fetch a list of input datasets from DBS. Query must satisfy this format:<pre>/*/*/DATATIER</pre>
          <input type="text" v-model="getDatasetsDialog.input" class="mb-2" placeholder="Dataset name query, for example /ZeroBias/Run2018*/RAW">
          Comma-separated list of values to use when filtering-out dataset names:
          <input type="text" v-model="getDatasetsDialog.exclude" placeholder="Comma separated patterns to exclude, e.g. validation,pilot">
        </v-card-text>
        <small style="opacity: 0.4">Note: some primary datasets are blacklisted and will not appear in fetched list</small>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="!listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(true)">Fetch</v-btn>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(true)" title="Fetch list and replace existing list with newly fetched one">Fetch and replace</v-btn>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(false)" title="Fetch list and append it to an existing list">Fetch and append</v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="closeGetDatasetsDialog()">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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

export default {
  name: 'TicketsEdit',
  components: {
    LoadingOverlay,
    Autocompleter
  },
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      prepid: undefined,
      editableObject: {},
      editingInfo: {},
      loading: true,
      creatingNew: true,
      errorDialog: {
        visible: false,
        title: '',
        description: '',
      },
      getDatasetsDialog: {
        visible: false,
        input: '',
        exclude: 'validation,pilot',
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
    axios.get('api/tickets/get_editable/' + this.prepid).then(response => {
      component.editableObject = response.data.response.object;
      component.editableObject.input_datasets = component.editableObject.input_datasets.filter(Boolean).join('\n');
      component.editingInfo = response.data.response.editing_info;
      if (component.creatingNew) {
        component.addStep();
      }
      component.loading = false;
    }).catch(error => {
      component.loading = false;
      this.showError('Error fetching editing information', component.getError(error));
    });
  },
  methods: {
    save: function() {
      this.loading = true;
      let editableObject = this.makeCopy(this.editableObject);
      editableObject.notes = editableObject.notes.trim();
      editableObject.input_datasets = editableObject.input_datasets.split('\n').map(function(s) { return s.trim() }).filter(Boolean);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/tickets/create', editableObject);
      } else {
        httpRequest = axios.post('api/tickets/update', editableObject);
      }
      let component = this;
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'tickets?prepid=' + response.data.response.prepid;
      }).catch(error => {
        component.loading = false;
        this.showError('Error saving ticket', component.getError(error));
      });
    },
    getDatasets: function(replace) {
      this.loading = true;
      let component = this;
      let url = 'api/tickets/get_datasets?q=' + this.getDatasetsDialog.input;
      let exclude = this.cleanSplit(this.getDatasetsDialog.exclude, ',');
      if (exclude.length) {
        url += '&exclude=' + exclude.join(',');
      }
      // Timeout 120000ms is 2 minutes
      let httpRequest = axios.get(url, {timeout: 120000});
      this.closeGetDatasetsDialog();
      httpRequest.then(response => {
        if (replace) {
          component.editableObject.input_datasets = response.data.response.filter(Boolean).join('\n');
        } else {
          let existingDatasets = component.editableObject.input_datasets.split('\n').map(function(s) { return s.trim() }).filter(Boolean);
          for (let dataset of response.data.response.filter(Boolean)) {
            if (existingDatasets.indexOf(dataset) < 0) {
              existingDatasets.push(dataset);
            }
          }
          component.editableObject.input_datasets = existingDatasets.join('\n');
        }
        component.loading = false;
      }).catch(error => {
        component.loading = false;
        this.showError('Error getting datasets for ticket', component.getError(error))
      });
    },
    showGetDatasetsDialog: function() {
      this.getDatasetsDialog.visible = true;
      this.getDatasetsDialog.input = '';
    },
    closeGetDatasetsDialog: function() {
      this.getDatasetsDialog.visible = false;
      this.getDatasetsDialog.input = '';
    },
    addStep: function() {
      this.editableObject.steps.push({'subcampaign': '',
                                      'processing_string': '',
                                      'priority': 110000,
                                      'size_per_event': 1.0,
                                      'time_per_event': 1.0});
      this.editingInfo.steps.push({'subcampaign': true,
                                   'processing_string': true,
                                   'priority': true,
                                   'size_per_event': true,
                                   'time_per_event': true});
      if (this.editableObject.steps.length > 1) {
        // Copy processing string of last step
        const steps = this.editableObject.steps;
        steps[steps.length - 1]['processing_string'] = steps[steps.length - 2]['processing_string'];
        steps[steps.length - 1]['priority'] = steps[steps.length - 2]['priority'];
      }
    },
    deleteStep: function(index) {
      this.editableObject.steps.splice(index, 1);
      this.editingInfo.steps.splice(index, 1);
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
    getSubcampaignSuggestions: function(value, callback) {
      if (!value || value.length == 0) {
        callback([]);
      }
      axios.get('api/suggestions?db_name=subcampaigns&query=' + value).then(response => {
        callback(response.data.response);
      }).catch(() => {
        callback([]);
      });
    },
    cancel: function() {
      if (this.creatingNew) {
        window.location = 'subcampaigns';
      } else {
        window.location = 'subcampaigns?prepid=' + this.prepid;
      }
    },
  }
}
</script>