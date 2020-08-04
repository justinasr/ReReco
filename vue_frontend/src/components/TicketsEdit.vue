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
                  <td><input type="text"
                             v-model="step.subcampaign"
                             :disabled="!editingInfo.steps[index].subcampaign"></td>
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
      <v-btn small class="mr-1 mt-2" color="primary" @click="save()" :disabled="!listLength(editableObject.steps) || !listLength(editableObject.input_datasets)">Save</v-btn>
      <v-btn v-if="editingInfo.input_datasets" small class="mr-1 mt-2" color="primary" @click="showGetDatasetsDialog()">Get dataset list from DBS</v-btn>
    </v-card>
    <v-dialog v-model="getDatasetsDialog.visible"
              max-width="50%">
      <v-card class="page-card mb-0" style="max-width: none !important;">
        <v-card-title class="headline">Get dataset list</v-card-title>
        <v-card-text>
          Automatically get a list of input datasets from DBS. Query must satisfy this format:<pre>/*/*/RAW</pre>
          <input type="text" v-model="getDatasetsDialog.input" placeholder="Dataset name, for example /ZeroBias/Run2018*/RAW">
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="!listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(true)">Get</v-btn>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(true)" title="Fetch list and replace existing list with newly fetched one">Get and replace</v-btn>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="listLength(editableObject.input_datasets)" :disabled="!getDatasetsDialog.input.length" @click="getDatasets(false)" title="Fetch list and append it to an existing list">Get and append</v-btn>
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
          {{errorDialog.description}}
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

export default {
  name: 'TicketsEdit',
  components: {
    LoadingOverlay
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
      component.loading = false;
    }).catch(error => {
      component.loading = false;
      this.showError('Error fetching editing information', error.response.data.message);
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
        this.showError('Error saving ticket', error.response.data.message);
      });
    },
    getDatasets: function(replace) {
      this.loading = true;
      let component = this;
      // Timeout 120000ms is 2 minutes
      let httpRequest = axios.get('api/tickets/get_datasets?q=' + this.getDatasetsDialog.input, {timeout: 120000});
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
        this.showError('Error getting datasets for ticket', error.response.data.message)
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
  }
}
</script>