<template>
  <div>
    <h1 v-if="creatingNew">Creating new Ticket</h1>
    <h1 v-else>Editing {{editableObject.prepid}}</h1>
    <v-card raised class="editPageCard">
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
                  <td>Subcampaign</td><td><input type="text" v-model="step.subcampaign" :disabled="!editingInfo.steps"></td>
                </tr>
                <tr>
                  <td>Processing String</td><td><input type="text" v-model="step.processing_string" :disabled="!editingInfo.steps"></td>
                </tr>
                <tr>
                  <td>Size per event</td><td><input type="number" v-model="step.size_per_event" :disabled="!editingInfo.steps">kB</td>
                </tr>
                <tr>
                  <td>Time per event</td><td><input type="number" v-model="step.time_per_event" :disabled="!editingInfo.steps">s</td>
                </tr>
              </table>
              <v-btn small class="mr-1 mb-1" color="error" @click="deleteStep(index)">Delete step {{index + 1}}</v-btn>
              <hr>
            </div>
            <v-btn small class="mr-1 mb-1 mt-1" color="primary" @click="addStep()">Add step {{listLength(editableObject.steps) + 1}}</v-btn>
          </td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editableObject.priority" :disabled="!editingInfo.priority"></td>
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
      <v-btn small class="mr-1 mb-1" color="primary" @click="save()">Save</v-btn>
      <v-btn v-if="editingInfo.input_datasets" small class="mr-1 mb-1" color="primary" @click="showGetDatasetsDialog()">Get dataset list from DBS</v-btn>
    </v-card>
    <v-dialog v-model="getDatasetsDialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">Get dataset list</v-card-title>
        <v-card-text>
          Automatically get a list of input datasets from DBS. Query must satisfy this format:<pre>/*/*/RAW</pre>Enter dataset name query below, for example:<pre>/ZeroBias/Run2018*/RAW</pre>
          <input type="text" v-model="getDatasetsDialog.input">
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" :disabled="!getDatasetsDialog.input.length" @click="getDatasets()">Get</v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="closeGetDatasetsDialog()">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-overlay :absolute="false"
               :opacity="0.95"
               :z-index="3"
               :value="loading"
               style="text-align: center">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <br>Please wait...
    </v-overlay>
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
import { listLengthMixin } from '../mixins/ListLengthMixin.js'

export default {
  components: {

  },
  mixins: [
    listLengthMixin
  ],
  data () {
    return {
      prepid: undefined,
      editableObject: {},
      editingInfo: {},
      loading: true,
      creatingNew: true,
      getDatasetsDialog: {
        visible: false,
        input: '',
      },
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
    this.prepid = query['prepid'];
    this.creatingNew = this.prepid === undefined;
    let component = this;
    axios.get('api/tickets/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      component.editableObject = response.data.response.object;
      component.editableObject.input_datasets = component.editableObject.input_datasets.filter(Boolean).join('\n')
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    });
  },
  methods: {
    save: function() {
      let editableObject = JSON.parse(JSON.stringify(this.editableObject))
      let component = this;
      editableObject['notes'] = editableObject['notes'].trim();
      editableObject['input_datasets'] = editableObject['input_datasets'].split('\n').map(function(s) { return s.trim() }).filter(Boolean);
      let httpRequest;
      this.loading = true;
      if (this.creatingNew) {
        httpRequest = axios.put('api/tickets/create', editableObject)
      } else {
        httpRequest = axios.post('api/tickets/update', editableObject)
      }
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'tickets?prepid=' + response.data.response.prepid;
      }).catch(error => {
        component.loading = false;
        this.showError('Error saving ticket', error.response.data.message)
      });
    },
    getDatasets: function() {
      this.loading = true;
      let component = this;
      // Timeout 120000ms is 2 minutes
      let httpRequest = axios.get('api/tickets/get_datasets?q=' + this.getDatasetsDialog.input, {timeout: 120000});
      this.closeGetDatasetsDialog();
      httpRequest.then(response => {
        component.editableObject['input_datasets'] = response.data.response.filter(Boolean).join('\n');
        component.loading = false;
      }).catch(error => {
        this.showError('Error getting datasets for ticket', error.response.data.message)
        component.loading = false;
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
    addStep: function() {
      this.editableObject['steps'].push({'subcampaign': '',
                                         'processing_string': '',
                                         'size_per_event': 1.0,
                                         'time_per_event': 1.0});
    },
    deleteStep: function(index) {
      this.editableObject['steps'].splice(index, 1);
    }
  }
}
</script>

<style scoped>

h1 {
  margin: 8px;
}

td {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-right: 4px;
}

.editPageCard {
  margin: auto;
  padding: 16px;
  max-width: 750px;
}

</style>